from __future__ import annotations

import re
import uuid
import os
from typing import Any, Dict, List, Optional, Set, Tuple

from ..db.session import SessionLocal
from ..engine.rulesEngine.product_filtering import product_filtering
from ..engine.solution_schemas import (
    HardwareRecommendation,
    InstallationDoc,
    RecommendationBundle,
    SoftwareRecommendation,
)
from ..engine.lead_service import LeadService
from ..engine.state_machine import (
    CollectedInfo,
    ConversationState,
    determine_next_state,
    state_order,
)
from ..engine.slot_planner import (
    SlotDef,
    SlotPlanner,
    SLOT_BY_ID,
    _is_slot_answered,
    validate_choices_for_slot,
)
from ..engine.input_parsers import try_parse_for_slot, parse_volume_ticket, NOT_SURE
from ..llm.client import process_turn
from ..llm.contracts import ChatResponse, DebugTrace


class ChatService:
    """
    Orchestrator that coordinates:
    - Slot planner (determines exactly which question to ask next)
    - Deterministic input parsers (extract info before LLM)
    - LLM (phrases the question — does NOT choose the topic)
    - Product engine (matches products when ready)

    The backend is the source of truth for slot order, validation, and memory.
    """

    PRICING_KEYWORDS = [
        "price", "pricing", "cost", "costs", "quote", "quotes",
        "how much", "rate", "rates", "cheap", "expensive", "budget",
    ]
    DEBUG_MATCH_ENV = "CHAT_DEBUG_MATCH"

    @staticmethod
    def _debug_match_enabled() -> bool:
        return os.getenv(ChatService.DEBUG_MATCH_ENV, "").strip().lower() in {"1", "true", "yes", "on"}

    @staticmethod
    def _build_debug_match_payload(
        constraints: Dict[str, Any],
        rows: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        return {
            "constraints": constraints,
            "rows_returned": len(rows),
            "top_candidates": [r.get("hardware_name") for r in rows[:5]],
        }

    @staticmethod
    def _detect_pricing(message: str) -> bool:
        lower = message.lower()
        return any(kw in lower for kw in ChatService.PRICING_KEYWORDS)

    @staticmethod
    def _build_pricing_response() -> ChatResponse:
        return ChatResponse(
            type="clarification",
            text="Pricing depends on volume and configuration — I can connect you with a specialist who can provide a customized quote. Would you like me to collect your contact info for a follow-up?",
            quick_replies=["Yes, please connect me", "No thanks, just browsing"],
            ui_actions=["offer_booking"],
        )

    @staticmethod
    def _build_recommendation_bundle(
        rows: List[Dict[str, Any]],
        constraints: Dict[str, Any],
    ) -> RecommendationBundle:
        """Deterministically build a recommendation bundle from product data."""
        items = []
        for row in rows[:3]:
            specs = row.get("technical_specs", {})
            items.append(HardwareRecommendation(
                name=row.get("hardware_name", specs.get("model_name", "Unknown")),
                role="Primary Card Reader",
                technical_specs=specs,
            ))

        top = rows[0]
        specs = top.get("technical_specs", {})

        evidence_parts = []
        for field, label in [
            ("input_power", "power"),
            ("interface", "interface"),
            ("operate_temperature", "temp range"),
            ("ip_rating", "IP rating"),
        ]:
            val = specs.get(field)
            if val:
                evidence_parts.append(f"{label}: {val}")

        extras = str(specs.get("extra_specs", "")).lower()
        if "display" in extras:
            evidence_parts.append("built-in display")
        if "pin" in extras or "keypad" in extras:
            evidence_parts.append("PIN entry support")
        if "weather" in extras or "ip" in extras:
            evidence_parts.append("weatherproof design")

        if not evidence_parts:
            evidence_parts.append("compatibility match")

        explanation = (
            f"Based on your requirements, I recommend the {items[0].name}. "
            f"It matches on: {', '.join(evidence_parts)}. "
            f"This device is suitable for your deployment needs."
        )

        highlights = []
        for label, field in [
            ("Power", "input_power"),
            ("Interface", "interface"),
            ("Temperature Range", "operate_temperature"),
            ("Weather Rating", "ip_rating"),
        ]:
            val = specs.get(field)
            if val:
                highlights.append(f"{label}: {val}")

        docs = ChatService._fetch_installation_docs(items[0].name) if items else []

        return RecommendationBundle(
            hardware_name=items[0].name,
            hardware_items=items,
            software=[],
            highlights=highlights,
            explanation=explanation,
            installation_docs=docs,
        )

    @staticmethod
    def _fetch_installation_docs(model_name: str) -> List[InstallationDoc]:
        try:
            from ..engine.doc_fetcher import fetch_installation_docs
            result = fetch_installation_docs(model_name)
            if result:
                return [InstallationDoc(**doc) for doc in result]
        except Exception:
            pass
        return []

    @staticmethod
    def _run_product_matching(collected: CollectedInfo) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        constraints = collected.to_flat_constraints()
        db = SessionLocal()
        try:
            rows = product_filtering(db, constraints)
            return rows, constraints
        finally:
            db.close()

    # ── New: deterministic parsing + slot planner ────────────────────────

    @staticmethod
    def _run_deterministic_parsers(
        message: str,
        planned_slot_id: Optional[str],
    ) -> Dict[str, Any]:
        """
        Try deterministic parsers before LLM extraction.
        Returns parsed info that can be merged directly into CollectedInfo.
        """
        result: Dict[str, Any] = {}

        # Always try volume/ticket parser (can fill transaction_profile fields)
        vt = parse_volume_ticket(message)
        if vt:
            if "monthly_volume" in vt and vt["monthly_volume"] is not None:
                result.setdefault("transaction_profile", {})["monthly_volume"] = vt["monthly_volume"]
            if "average_ticket" in vt and vt["average_ticket"] is not None:
                result.setdefault("transaction_profile", {})["average_ticket"] = vt["average_ticket"]

        # If there's a planned slot, try its specific parser
        if planned_slot_id:
            slot = SLOT_BY_ID.get(planned_slot_id)
            if slot:
                parsed = try_parse_for_slot(message, planned_slot_id, slot.allowed_choices)
                if parsed is not None:
                    ChatService._apply_parsed_to_result(result, slot, parsed)

        # Cross-slot heuristics: extract high-value qualification signals even when
        # they are not the currently planned slot.
        inferred = ChatService._infer_qualification_fields(message)
        if inferred:
            ChatService._deep_merge(result, inferred)

        return result

    @staticmethod
    def _deep_merge(base: Dict[str, Any], incoming: Dict[str, Any]) -> Dict[str, Any]:
        for key, value in incoming.items():
            if isinstance(value, dict) and isinstance(base.get(key), dict):
                ChatService._deep_merge(base[key], value)
            else:
                base[key] = value
        return base

    @staticmethod
    def _infer_qualification_fields(message: str) -> Dict[str, Any]:
        lower = message.lower()
        out: Dict[str, Any] = {}

        # Vertical/use case inference
        vertical_map = [
            ("ev charging", "EV Charging"),
            ("parking", "Parking / Transit"),
            ("transit", "Parking / Transit"),
            ("vending", "Vending Machine"),
            ("retail", "Retail / POS"),
            ("pos", "Retail / POS"),
        ]
        for token, canonical in vertical_map:
            if token in lower:
                out.setdefault("environment", {})["vertical"] = canonical
                break

        # Environment inference
        if "outdoor" in lower or "outside" in lower:
            if "harsh" in lower or "extreme" in lower:
                out.setdefault("environment", {})["indoor_outdoor"] = "outdoor harsh"
            else:
                out.setdefault("environment", {})["indoor_outdoor"] = "outdoor"
        elif "indoor" in lower or "inside" in lower:
            out.setdefault("environment", {})["indoor_outdoor"] = "indoor"

        # Temperature inference
        temp = ChatService._extract_temp_from_text(message)
        if temp:
            out.setdefault("environment", {})["temperature_range"] = temp

        # Card type inference
        card_types: List[str] = []
        if ("contactless" in lower) or ("tap" in lower):
            card_types.append("contactless")
        if ("chip" in lower) or ("emv" in lower) or ("contact " in lower):
            card_types.append("contact")
        if "magstripe" in lower or "swipe" in lower:
            card_types.append("magstripe")
        if card_types:
            out.setdefault("technical_context", {})["card_types"] = sorted(set(card_types))

        return out

    @staticmethod
    def _extract_temp_from_text(text: str) -> Optional[str]:
        pattern = re.compile(
            r"(-?\d+\s*°?\s*[CF])\s*(?:to|-|–)\s*(-?\d+\s*°?\s*[CF])",
            re.IGNORECASE,
        )
        m = pattern.search(text)
        if not m:
            return None
        lo = re.sub(r"\s+", "", m.group(1)).upper().replace("°", "")
        hi = re.sub(r"\s+", "", m.group(2)).upper().replace("°", "")
        return f"{lo} to {hi}"

    @staticmethod
    def _apply_parsed_to_result(result: Dict[str, Any], slot: SlotDef, parsed: Any) -> None:
        """Apply a parsed value to the result dict using the slot's dotted path."""
        parts = slot.path.split(".")
        # Navigate to the right nested dict
        current = result
        for part in parts[:-1]:
            if part not in current:
                current[part] = {}
            current = current[part]
        # Set the value
        if slot.path == "transaction_profile.monthly_volume" and isinstance(parsed, dict):
            # volume_ticket parser returns a dict
            tp = result.setdefault("transaction_profile", {})
            if "monthly_volume" in parsed:
                tp["monthly_volume"] = parsed["monthly_volume"]
            if "average_ticket" in parsed:
                tp["average_ticket"] = parsed["average_ticket"]
        elif isinstance(parsed, bool):
            current[parts[-1]] = parsed
        elif isinstance(parsed, str) and slot.parser.value == "choice":
            # Map the choice back to the canonical value stored in CollectedInfo
            current[parts[-1]] = ChatService._choice_to_value(slot, parsed)
            # Special: extract temperature_range from indoor_outdoor choice
            if slot.id == "indoor_outdoor":
                temp = ChatService._extract_temp_from_choice(parsed)
                if temp:
                    result.setdefault("environment", {})["temperature_range"] = temp
        elif isinstance(parsed, list) and slot.parser.value == "choice":
            # Multi-select (e.g., card_types)
            current[parts[-1]] = parsed
        else:
            current[parts[-1]] = parsed

    @staticmethod
    def _extract_temp_from_choice(choice: str) -> Optional[str]:
        """Extract temperature range from indoor/outdoor choice string."""
        import re as _re
        m = _re.search(r'(-?\d+\s*°?[CF]\s*(?:to|–|-)\s*-?\d+\s*°?[CF])', choice, re.IGNORECASE)
        if m:
            return m.group(1).replace('°', '').replace('C', '°C').replace('F', '°F')
        return None

    @staticmethod
    def _choice_to_value(slot: SlotDef, matched_choice: str) -> Any:
        """Map a matched choice string to the value stored in CollectedInfo."""
        sid = slot.id
        lowered = matched_choice.lower()

        if sid == "vertical":
            return matched_choice
        if sid == "indoor_outdoor":
            if "harsh" in lowered:
                return "outdoor harsh"
            if "outdoor" in lowered:
                return "outdoor"
            return "indoor"
        if sid == "monthly_volume":
            # Extract the number
            import re as _re
            m = _re.search(r'(\d[\d,]*)', matched_choice)
            if m:
                return int(m.group(1).replace(",", ""))
            return matched_choice
        if sid == "card_types":
            # Parse multiple card types from choice
            result = []
            if "contact" in lowered and "contactless" not in lowered:
                result.append("contact")
            if "contactless" in lowered or "tap" in lowered:
                result.append("contactless")
            if "magstripe" in lowered or "swipe" in lowered:
                result.append("magstripe")
            return result if result else [matched_choice]
        if sid == "needs_pin":
            if "yes" in lowered:
                return True
            if "no" in lowered:
                return False
            return None  # "not sure"
        if sid == "is_standalone":
            if "standalone" in lowered and "no host" in lowered:
                return True
            if "host" in lowered and "controlled" in lowered:
                return False
            return None  # "not sure"
        if sid == "power_source":
            if "wall" in lowered:
                return "wall outlet"
            if "usb" in lowered:
                return "USB"
            if "battery" in lowered:
                return "battery"
            return matched_choice
        if sid == "host_interface":
            if "usb" in lowered:
                return "USB"
            if "rs232" in lowered or "serial" in lowered:
                return "RS232"
            if "ethernet" in lowered:
                return "Ethernet"
            if "bluetooth" in lowered:
                return "Bluetooth"
            return matched_choice
        if sid == "standalone_comms":
            if "ethernet" in lowered:
                return "Ethernet"
            if "wifi" in lowered:
                return "WiFi"
            if "cellular" in lowered or "4g" in lowered or "5g" in lowered:
                return "Cellular"
            return matched_choice
        if sid == "needs_display":
            if "yes" in lowered:
                return True
            if "no" in lowered:
                return False
            return None

        return matched_choice

    @staticmethod
    def _normalize_extracted_info(raw: Dict[str, Any]) -> Dict[str, Any]:
        """
        Harden update_lead_info extraction:
        - Normalize misplaced fields into correct sections
        - Ignore unknown fields safely
        - Deep-merge compatible
        """
        if not raw:
            return {}

        cleaned: Dict[str, Any] = {}

        # Known top-level sections
        known_sections = {"environment", "transaction_profile", "technical_context", "lead"}
        known_sections.add("meta")

        for key, value in raw.items():
            if key in known_sections:
                if isinstance(value, dict):
                    cleaned[key] = ChatService._clean_section(key, value)
                # else skip non-dict values for known sections
            elif key == "__state_override":
                cleaned[key] = value
            # Unknown top-level keys are silently ignored

        return cleaned

    @staticmethod
    def _sync_answered_slots_from_collected(
        collected: CollectedInfo,
        answered_slots: Set[str],
    ) -> None:
        for slot in SLOT_BY_ID.values():
            if _is_slot_answered(slot, collected):
                answered_slots.add(slot.id)

    @staticmethod
    def _clean_section(section: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Clean a section dict, keeping only known fields."""
        known_fields: Dict[str, set] = {
            "environment": {"vertical", "indoor_outdoor", "temperature_range"},
            "transaction_profile": {"monthly_volume", "average_ticket"},
            "technical_context": {
                "power_source", "voltage", "card_types", "needs_pin",
                "is_standalone", "host_interface", "host_os",
                "standalone_comms", "needs_display", "previous_products",
            },
            "lead": {"name", "email", "company", "phone"},
            "meta": {"recommendation_shown"},
        }

        allowed = known_fields.get(section, set())
        result: Dict[str, Any] = {}
        for k, v in data.items():
            if k in allowed:
                result[k] = v
            # else: silently ignore unknown field
        return result

    # ── Main entry point ─────────────────────────────────────────────────

    def process_message(
        self,
        message: str,
        history: List[Dict[str, str]],
        collected_info: Optional[Dict[str, Any]] = None,
        asked_slots: Optional[Set[str]] = None,
        answered_slots: Optional[Set[str]] = None,
        slot_attempts: Optional[Dict[str, int]] = None,
    ) -> ChatResponse:
        """
        Main entry point: process a user message and return a response.

        Args:
            message: The user's current message.
            history: Previous message exchange history.
            collected_info: Structured data accumulated from previous turns.
            asked_slots: Set of slot ids that have been asked.
            answered_slots: Set of slot ids that are answered.
            slot_attempts: Dict of slot_id → attempt count.
        """

        # ── Detect pricing ──
        if self._detect_pricing(message):
            return self._build_pricing_response()

        # ── Build collected ──
        collected = CollectedInfo()
        if collected_info:
            collected.merge(collected_info)

        # ── Initialize planner metadata ──
        _asked: Set[str] = asked_slots if asked_slots is not None else set()
        _answered: Set[str] = answered_slots if answered_slots is not None else set()
        _attempts: Dict[str, int] = slot_attempts if slot_attempts is not None else {}

        # ── 1. Run deterministic parsers on user input ──
        parsed_info = self._run_deterministic_parsers(message, None)
        parser_succeeded = False
        parser_used: Optional[str] = None

        if parsed_info:
            # Check if we got something from volume_ticket parser
            tp = parsed_info.get("transaction_profile", {})
            if tp.get("monthly_volume") is not None or tp.get("average_ticket") is not None:
                parser_succeeded = True
                parser_used = "volume_ticket"
            collected.merge(parsed_info)
            self._sync_answered_slots_from_collected(collected, _answered)

        # ── 2. Select next slot ──
        next_slot = SlotPlanner.select_next_slot(collected, _asked, _answered, _attempts)
        pre_slot_state = determine_next_state(collected)

        # If recommendation has not been shown yet, do not enter lead-capture slots.
        if (
            next_slot is not None
            and next_slot.state == ConversationState.LEAD_CAPTURE
            and pre_slot_state == ConversationState.RECOMMENDING
        ):
            return self._transition_to_recommendation_or_complete(
                collected, _answered, new_info={}
            )

        # ── 3. No more slots? Transition to recommendation or handoff ──
        if next_slot is None:
            return self._transition_to_recommendation_or_complete(
                collected, _answered, new_info={}
            )

        # ── 4. We have a slot — record it as asked ──
        SlotPlanner.record_asked(next_slot.id, _asked, _attempts)

        # ── 5. Try slot-specific deterministic parser ──
        slot_parsed = try_parse_for_slot(message, next_slot.id, next_slot.allowed_choices)
        slot_parser_used: Optional[str] = None
        slot_parser_succeeded = False

        if slot_parsed is not None:
            slot_parser_used = next_slot.parser.value
            slot_parser_succeeded = True

            # Handle NOT_SURE sentinel
            if slot_parsed is NOT_SURE:
                # User answered "not sure" — mark answered without setting a value
                if next_slot.accept_not_sure:
                    SlotPlanner.record_answered(next_slot.id, _answered)
            else:
                slot_result: Dict[str, Any] = {}
                self._apply_parsed_to_result(slot_result, next_slot, slot_parsed)
                if slot_result:
                    collected.merge(slot_result)

                # Mark slot as answered
                if next_slot.parser.value == "boolean" and slot_parsed is False:
                    # Explicit "no" — mark answered (value is False, which is a valid answer)
                    SlotPlanner.record_answered(next_slot.id, _answered)
                elif next_slot.parser.value == "boolean" and slot_parsed is True:
                    SlotPlanner.record_answered(next_slot.id, _answered)
                else:
                    SlotPlanner.record_answered(next_slot.id, _answered)

                # After deterministic parse succeeded, select the NEXT slot
                # instead of making the LLM ask about the one we just answered
                next_next = SlotPlanner.select_next_slot(collected, _asked, _answered, _attempts)
                if next_next:
                    next_slot = next_next
                    SlotPlanner.record_asked(next_slot.id, _asked, _attempts)
                    # Reset parser flags for the new slot
                    slot_parser_used = None
                    slot_parser_succeeded = False
                else:
                    # No more slots — go straight to recommendation / complete
                    return self._transition_to_recommendation_or_complete(
                        collected, _answered, new_info={}
                    )

        # If deterministic parsing already reached recommending conditions,
        # bypass another LLM question and transition immediately.
        if determine_next_state(collected) == ConversationState.RECOMMENDING:
            return self._transition_to_recommendation_or_complete(
                collected, _answered, new_info={}
            )

        # ── 6. Call LLM with slot-bound prompt ──
        llm_result = process_turn(
            message=message,
            history=history,
            state=next_slot.state.value,
            collected_info=collected.model_dump(exclude_none=True),
            planned_slot_id=next_slot.id,
            slot_prompt_hint=next_slot.prompt_hint,
        )

        # ── 7. Merge LLM-extracted info ──
        extracted = llm_result.get("extracted_info", {})
        new_info: Dict[str, Any] = {}

        if extracted:
            cleaned = self._normalize_extracted_info(extracted)
            if cleaned:
                collected.merge(cleaned)
                new_info = cleaned
                self._sync_answered_slots_from_collected(collected, _answered)

                # Check if the planned slot was answered via update_lead_info
                if _is_slot_answered(next_slot, collected):
                    SlotPlanner.record_answered(next_slot.id, _answered)

        # ── 8. Resolve choices: use validated LLM choices or fallback ──
        choice_validation = llm_result.get("choice_validation", "none")
        accepted_slot = llm_result.get("accepted_slot")
        suggested_choices = llm_result.get("suggested_choices", [])

        final_choices: List[str] = []
        if next_slot.parser.value == "free_text":
            final_choices = []
        elif suggested_choices and choice_validation == "valid":
            final_choices = list(suggested_choices)
        elif next_slot.fallback_choices:
            # Use deterministic fallback choices
            choice_validation = "fallback" if choice_validation in ("none", "rejected_mismatch", "rejected_vocab") else choice_validation
            final_choices = list(next_slot.fallback_choices)

        # ── 9. Determine next state ──
        next_state = determine_next_state(collected)

        # Intercept: if we should go to RECOMMENDING
        if (state_order(next_slot.state) < state_order(ConversationState.RECOMMENDING) and
            state_order(next_state) >= state_order(ConversationState.RECOMMENDING)):
            transition = self._transition_to_recommendation_or_complete(
                collected, _answered, new_info=new_info
            )
            if transition.type in {"recommendation", "clarification"}:
                transition.planned_slot = next_slot.id
                transition.accepted_slot = accepted_slot
                transition.choice_validation_result = choice_validation
                return transition
            next_state = next_slot.state

        if next_state != next_slot.state:
            new_info["__state_override"] = next_state.value

        # Build the reply text
        reply = llm_result.get("reply", "") or ""

        # ── 10. Build debug trace ──
        debug = DebugTrace(
            turn_id=str(uuid.uuid4()),
            final_response_type="question",
            planned_slot=next_slot.id,
            accepted_slot=accepted_slot,
            choice_validation_result=choice_validation,
            parser_used=slot_parser_used or parser_used,
            parser_succeeded=slot_parser_succeeded or parser_succeeded,
        )

        return ChatResponse(
            type="question",
            text=reply,
            quick_replies=final_choices if final_choices else None,
            ui_actions=self._get_ui_actions(next_state),
            new_info=new_info,
            next_state=next_state,
            planned_slot=next_slot.id,
            accepted_slot=accepted_slot,
            choice_validation_result=choice_validation,
            debug=debug,
        )

    @staticmethod
    def _transition_to_recommendation_or_complete(
        collected: CollectedInfo,
        answered_slots: Set[str],
        new_info: Dict[str, Any],
    ) -> ChatResponse:
        """Determine whether to show a recommendation or go to lead capture / complete."""
        tech_answered = any(
            sid in answered_slots
            for sid in ["card_types", "needs_pin", "is_standalone"]
        )
        has_basics = (
            "vertical" in answered_slots
            and "indoor_outdoor" in answered_slots
        )

        if has_basics and tech_answered:
            rows, constraints = ChatService._run_product_matching(collected)
            debug_match = (
                ChatService._build_debug_match_payload(constraints, rows)
                if ChatService._debug_match_enabled()
                else None
            )
            if rows:
                bundle = ChatService._build_recommendation_bundle(rows, constraints)
                return ChatResponse(
                    type="recommendation",
                    text=(
                        f"{bundle.explanation} "
                        "This is a preview based on what you've shared so far. "
                        "Would you like me to connect you with an ID TECH specialist "
                        "for final fit validation, specs, and next steps?"
                    ),
                    recommendation=bundle,
                    quick_replies=["Yes, connect me", "Not yet"],
                    ui_actions=["show_products", "offer_booking"],
                    next_state=ConversationState.LEAD_CAPTURE,
                    new_info={
                        **new_info,
                        "meta": {"recommendation_shown": True},
                        "__state_override": "lead_capture",
                    },
                    debug_match=debug_match,
                )
            else:
                return ChatResponse(
                    type="clarification",
                    text="I couldn't find a confident product match from the current requirements. I can connect you with an ID TECH specialist who can recommend the right fit.",
                    quick_replies=["Yes, connect me", "No thanks"],
                    ui_actions=["offer_booking"],
                    debug_match=debug_match,
                )

        # Check if we're in lead capture phase
        if "lead_name" in answered_slots or "lead_email" in answered_slots:
            if collected.lead.name and collected.lead.email:
                LeadService.save_lead_from_collected(collected, status="completed")
                return ChatResponse(
                    type="clarification",
                    text="Thank you for your time! A specialist will follow up with you shortly. Would you like to book a meeting with a sales engineer?",
                    ui_actions=["offer_booking"],
                    next_state=ConversationState.HANDOFF,
                )
            if not collected.lead.name:
                return ChatResponse(
                    type="clarification",
                    text="Before we wrap up, could you share your name?",
                    next_state=ConversationState.LEAD_CAPTURE,
                )
            return ChatResponse(
                type="clarification",
                text="Could you share the best email address for follow-up?",
                next_state=ConversationState.LEAD_CAPTURE,
            )

        # Fallback: start lead capture
        return ChatResponse(
            type="clarification",
            text="I have enough information to work with. To provide the best recommendation, could you share your name and email so a specialist can follow up?",
            quick_replies=["Sure, I'll share my details", "No thanks"],
        )

    @staticmethod
    def _get_ui_actions(state: ConversationState) -> List[str]:
        actions = []
        if state == ConversationState.LEAD_CAPTURE:
            actions.append("show_lead_form")
        elif state == ConversationState.HANDOFF:
            actions.append("offer_booking")
        return actions


_service_instance = ChatService()
def get_chat_service() -> ChatService:
    return _service_instance
