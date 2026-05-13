from __future__ import annotations

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
)
from ..engine.input_parsers import parse_volume_ticket
from ..llm.client import process_turn
from ..llm.contracts import ChatResponse, DebugTrace


class ChatService:
    """
    Orchestrator that coordinates:
    - Slot planner (determines exactly which question to ask next)
    - LLM (phrases the question, extracts answers via constrained per-slot tools)
    - Product engine (matches products when ready)

    The backend is the source of truth for slot order, validation, and memory.
    All user-input parsing is done by the LLM through constrained tools,
    except volume_ticket which has a dedicated regex parser.
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
    def _is_valid_question_reply(text: str) -> bool:
        if not text or not text.strip():
            return False
        lowered = text.lower()
        closing_markers = [
            "feel free to ask",
            "let me know if you have any more questions",
            "if you have any more questions",
            "anything else i can help",
        ]
        if any(marker in lowered for marker in closing_markers):
            return False
        if text.count("?") != 1:
            return False
        return text.strip().endswith("?")

    @staticmethod
    def _fallback_question_for_slot(slot: SlotDef) -> str:
        by_slot = {
            "vertical": "What industry or use case are you working on?",
            "indoor_outdoor": "Will your deployment be indoors or outdoors?",
            "monthly_volume": "About how many transactions do you expect per month?",
            "card_types": "Which card types do you need to accept: contact/chip, contactless/tap, or magstripe/swipe?",
            "needs_pin": "Do customers need to enter a PIN on the device?",
            "is_standalone": "Will this be a standalone device, or host-controlled?",
            "power_source": "What power source is available: wall outlet, USB power, or battery?",
            "host_interface": "Which host interface do you need: USB, RS232/Serial, Ethernet, or Bluetooth?",
            "standalone_comms": "For standalone deployment, which communication method do you need: Ethernet, WiFi, or Cellular?",
            "needs_display": "Do you need a display on the device?",
            "lead_name": "Could I get your name so we can follow up with the right specialist?",
            "lead_email": "Could you share the best email address for follow-up?",
        }
        return by_slot.get(slot.id, "Could you share a bit more detail?")

    @staticmethod
    def _build_slot_question(slot: SlotDef) -> str:
        return ChatService._fallback_question_for_slot(slot)

    @staticmethod
    def _enforce_ask_slot_contract(
        slot: SlotDef,
        reply: str,
        suggested_choices: List[str],
        choice_validation: str,
    ) -> Tuple[str, List[str], str]:
        final_reply = reply
        final_choices: List[str] = []
        final_validation = choice_validation

        if not ChatService._is_valid_question_reply(final_reply):
            final_reply = ChatService._build_slot_question(slot)
            final_validation = "contract_reply_fallback"

        if slot.parser.value == "free_text":
            return final_reply, [], final_validation

        if suggested_choices and choice_validation == "valid":
            final_choices = list(suggested_choices)[:4]
            return final_reply, final_choices, final_validation

        final_choices = list(slot.fallback_choices or [])[:4]
        if final_validation in ("none", "rejected_mismatch", "rejected_vocab"):
            final_validation = "contract_choices_fallback"
        return final_reply, final_choices, final_validation

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

    @staticmethod
    def _run_volume_ticket_parser(message: str) -> Dict[str, Any]:
        """
        Parse volume/ticket info using the dedicated regex parser.
        This is the only deterministic parser we keep — it handles a
        uniquely structured format (e.g., "1000 transactions, $10 each")
        that the LLM finds surprisingly error-prone.
        """
        result: Dict[str, Any] = {}
        vt = parse_volume_ticket(message)
        if vt:
            if "monthly_volume" in vt and vt["monthly_volume"] is not None:
                result.setdefault("transaction_profile", {})["monthly_volume"] = vt["monthly_volume"]
            if "average_ticket" in vt and vt["average_ticket"] is not None:
                result.setdefault("transaction_profile", {})["average_ticket"] = vt["average_ticket"]
        return result

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
            slot_attempts: Dict of slot_id -> attempt count.
        """
        if self._detect_pricing(message):
            return self._build_pricing_response()

        collected = CollectedInfo()
        if collected_info:
            collected.merge(collected_info)

        _asked: Set[str] = asked_slots if asked_slots is not None else set()
        _answered: Set[str] = answered_slots if answered_slots is not None else set()
        _attempts: Dict[str, int] = slot_attempts if slot_attempts is not None else {}

        # ── 1. Volume/ticket deterministic parsing ──
        parsed_volume = self._run_volume_ticket_parser(message)
        if parsed_volume:
            collected.merge(parsed_volume)
            self._sync_answered_slots_from_collected(collected, _answered)

        # ── 2. Pick the next question slot ──
        next_slot = SlotPlanner.select_next_slot(collected, _asked, _answered, _attempts)
        pre_slot_state = determine_next_state(collected)

        # If recommendation has not been shown yet, do not enter lead-capture slots
        if (
            next_slot is not None
            and next_slot.state == ConversationState.LEAD_CAPTURE
            and pre_slot_state == ConversationState.RECOMMENDING
        ):
            return self._transition_to_recommendation_or_complete(
                collected, _answered, new_info={}
            )

        if next_slot is None:
            return self._transition_to_recommendation_or_complete(
                collected, _answered, new_info={}
            )

        SlotPlanner.record_asked(next_slot.id, _asked, _attempts)

        # ── 3. Call the LLM with a slot-constrained prompt and tool ──
        llm_result = process_turn(
            message=message,
            history=history,
            state=next_slot.state.value,
            collected_info=collected.model_dump(exclude_none=True),
            planned_slot_id=next_slot.id,
            slot_prompt_hint=next_slot.prompt_hint,
        )

        # ── 4. Extract info the LLM captured ──
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

        # ── 5. Resolve choices: use validated LLM choices or fallback ──
        choice_validation = llm_result.get("choice_validation", "none")
        accepted_slot = llm_result.get("accepted_slot")
        suggested_choices = llm_result.get("suggested_choices", [])

        # Contract-enforced ASK_SLOT output
        raw_reply = llm_result.get("reply", "") or ""
        reply, final_choices, choice_validation = self._enforce_ask_slot_contract(
            next_slot,
            raw_reply,
            suggested_choices,
            choice_validation,
        )

        # ── 6. Determine next state and possibly transition ──
        next_state = determine_next_state(collected)

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

        debug = DebugTrace(
            turn_id=str(uuid.uuid4()),
            final_response_type="question",
            planned_slot=next_slot.id,
            accepted_slot=accepted_slot,
            choice_validation_result=choice_validation,
            parser_used="volume_ticket" if parsed_volume else None,
            parser_succeeded=bool(parsed_volume),
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
