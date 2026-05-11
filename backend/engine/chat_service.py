from __future__ import annotations

import uuid
from typing import Any, Dict, List, Optional, Tuple

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
)
from ..llm.client import process_turn
from ..llm.contracts import ChatResponse


class ChatService:
    """
    Orchestrator that coordinates:
    - State machine (determines what to do next)
    - LLM (extracts info from user messages)
    - Product engine (matches products when ready)

    Stateless — each turn receives collected_info and returns updated info.
    """

    PRICING_KEYWORDS = [
        "price", "pricing", "cost", "costs", "quote", "quotes",
        "how much", "rate", "rates", "cheap", "expensive", "budget",
    ]

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

        # Build evidence-based explanation
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

        # Build highlights from available data
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

        # Attach installation docs from Confluence
        docs = ChatService._fetch_installation_docs(items[0].name) if items else []

        return RecommendationBundle(
            hardware_name=items[0].name,
            hardware_items=items,
            software=[],  # Software can be added later
            highlights=highlights,
            explanation=explanation,
            installation_docs=docs,
        )

    @staticmethod
    def _fetch_installation_docs(model_name: str) -> List[InstallationDoc]:
        """Try to fetch installation docs for the recommended product."""
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
        """Run the deterministic product engine with the collected constraints."""
        constraints = collected.to_flat_constraints()

        db = SessionLocal()
        try:
            rows = product_filtering(db, constraints)
            return rows, constraints
        finally:
            db.close()

    def process_message(
        self,
        message: str,
        history: List[Dict[str, str]],
        collected_info: Optional[Dict[str, Any]] = None,
    ) -> ChatResponse:
        """
        Main entry point: process a user message and return a response.

        Args:
            message: The user's current message.
            history: Previous message exchange history.
            collected_info: Structured data accumulated from previous turns (from frontend).

        Returns:
            ChatResponse with reply, optional recommendation, ui_actions, and new_info.
        """

        # exit out if there's pricing
        if self._detect_pricing(message):
            return self._build_pricing_response()

        # get the next state based on the collected info
        collected = CollectedInfo()
        if collected_info:
            collected.merge(collected_info)
        state = determine_next_state(collected)

        # build the recommendation now
        if state == ConversationState.RECOMMENDATION:
            rows, constraints = self._run_product_matching(collected)
            if rows:
                bundle = self._build_recommendation_bundle(rows, constraints)
                return ChatResponse(
                    type="recommendation",
                    text=bundle.explanation,
                    recommendation=bundle,
                    ui_actions=["show_products"],
                    next_state=ConversationState.LEAD_CAPTURE,
                    new_info={"__state_override": "lead_capture"},
                )
            else:
                return ChatResponse(
                    type="clarification",
                    text="I wasn't able to find a perfect match with the details provided. Could you tell me which requirement is most flexible?",
                    quick_replies=[
                        "Power source",
                        "Communication interface",
                        "Operating temperature",
                        "Outdoor/IP requirements",
                        "PIN/display features",
                    ],
                )

        # exit out if complete and offer a booking with a sales agent from ID TECH
        if state == ConversationState.COMPLETE:
            # Auto-save lead if we have their info
            if collected.lead.name and collected.lead.email:
                LeadService.save_lead_from_collected(collected, status="completed")
            return ChatResponse(
                type="clarification",
                text="Thank you for your time! A specialist will follow up with you shortly. Would you like to book a meeting with a sales engineer?",
                ui_actions=["offer_booking"],
                next_state=ConversationState.COMPLETE,
            )

        # call the LLM with the current state
        llm_result = process_turn(
            message=message,
            history=history,
            state=state.value,
            collected_info=collected.model_dump(exclude_none=True),
        )

        # get the extracted info from the message, and merge it into the currently collected info
        extracted = llm_result.get("extracted_info", {})
        new_info: Dict[str, Any] = {}

        if extracted:
            collected.merge(extracted)
            new_info = extracted

        # re-evaluate the current state based on what we just gathered
        next_state = determine_next_state(collected)
        if next_state != state:
            new_info["__state_override"] = next_state.value

        # if entering RECOMMENDATION state, run produtc matching
        if next_state == ConversationState.RECOMMENDATION and state != ConversationState.RECOMMENDATION:
            rows, constraints = self._run_product_matching(collected)
            if rows:
                bundle = self._build_recommendation_bundle(rows, constraints)
                return ChatResponse(
                    type="recommendation",
                    text=bundle.explanation,
                    recommendation=bundle,
                    ui_actions=["show_products"],
                    next_state=ConversationState.LEAD_CAPTURE,
                    new_info={**new_info, "__state_override": "lead_capture"},
                )
            else:
                # Matching failed, so we should ask user what they can compromise on
                return ChatResponse(
                    type="clarification",
                    text="I wasn't able to find a perfect match with the details collected. Which requirement are you most flexible on?",
                    quick_replies=[
                        "Power source / voltage",
                        "Communication interface",
                        "Operating temperature range",
                        "Outdoor / IP requirements",
                        "PIN or display features",
                    ],
                    new_info=new_info,
                    next_state=ConversationState.RECOMMENDATION,
                )

        # build what frontend actions need to happen
        ui_actions = self._get_ui_actions(next_state)

        return ChatResponse(
            type="question",
            text=llm_result.get("reply", "") or "",
            quick_replies=self._get_quick_replies(next_state),
            ui_actions=ui_actions,
            new_info=new_info,
            next_state=next_state,
        )

    @staticmethod
    def _get_ui_actions(state: ConversationState) -> List[str]:
        """Return UI actions appropriate for the current state."""
        actions = []
        if state == ConversationState.LEAD_CAPTURE:
            actions.append("show_lead_form")
        elif state == ConversationState.COMPLETE:
            actions.append("offer_booking")
        return actions

    @staticmethod
    def _get_quick_replies(state: ConversationState) -> Optional[List[str]]:
        """Return suggested quick replies for the current state."""
        replies_by_state = {
            ConversationState.GREETING: [
                "Parking payment kiosk",
                "EV charging station",
                "Retail/POS terminal",
                "Vending machine",
            ],
            ConversationState.ENVIRONMENT: [
                "Indoor (0C to 40C)",
                "Outdoor (-20C to 65C)",
                "Outdoor harsh (-30C to 70C)",
            ],
            ConversationState.TRANSACTION_PROFILE: [
                "Under 1,000/month",
                "1,000 - 5,000/month",
                "5,000+ /month",
                "Not sure yet",
            ],
        }
        return replies_by_state.get(state)


_service_instance = ChatService()
def get_chat_service() -> ChatService:
    return _service_instance
