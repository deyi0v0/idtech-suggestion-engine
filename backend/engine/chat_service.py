"""
Conversation orchestrator — the "traffic cop" that coordinates between
the slot planner, LLM, and product matching engine.

This module is deliberately slim: it owns the flow but delegates each
specific concern to a dedicated service:

    PricingDetector     — keyword-based pricing detection
    VolumeTicketParser  — regex-based volume/ticket parsing
    ProductMatcher      — database product queries + recommendation building
    SlotContractEnforcer— validates LLM question output, provides fallbacks
    InfoNormalizer      — normalizes LLM extraction into CollectedInfo schema
    SlotPlanner         — selects the next slot to ask about
    StateMachine        — determines the current conversation phase
"""

from __future__ import annotations

import uuid
from typing import Any, Dict, List, Optional, Set

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
    _is_slot_answered,
)
from ..llm.client import process_turn
from ..llm.contracts import ChatResponse, DebugTrace

# ── Dedicated service imports ──
from ..engine.pricing_detector import PricingDetector
from ..engine.volume_parser import VolumeTicketParser
from ..engine.product_matcher import ProductMatcher
from ..engine.slot_contract import SlotContractEnforcer
from ..engine.info_normalizer import InfoNormalizer


class ChatService:
    """
    Orchestrator — coordinates the conversation flow.

    process_message() is the single public entry point. It:
    1. Checks for pricing keywords (short-circuit)
    2. Parses volume/ticket info (the one remaining deterministic parser)
    3. Picks the next slot to ask about
    4. Calls the LLM with a slot-constrained prompt + per-slot extraction tool
    5. Normalizes extracted info back into CollectedInfo
    6. Enforces the ASK_SLOT contract on the LLM reply (fallbacks if needed)
    7. Determines if we should transition to recommendation / lead capture / handoff
    8. Builds and returns the final ChatResponse

    Owns NO logic itself — all concerns are delegated to dedicated services.
    """

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
        # ── 0. Early exit: pricing keywords ──
        if PricingDetector.detect(message):
            return PricingDetector.build_response()

        # ── Initialize state from session ──
        collected = CollectedInfo()
        if collected_info:
            collected.merge(collected_info)

        _asked: Set[str] = asked_slots if asked_slots is not None else set()
        _answered: Set[str] = answered_slots if answered_slots is not None else set()
        _attempts: Dict[str, int] = slot_attempts if slot_attempts is not None else {}

        # ── 1. Volume/ticket deterministic parsing ──
        parsed_volume = VolumeTicketParser.parse(message)
        if parsed_volume:
            collected.merge(parsed_volume)
            InfoNormalizer.sync_answered_slots(collected, _answered)

        # ── 2. Pick the next question slot ──
        next_slot = SlotPlanner.select_next_slot(collected, _asked, _answered, _attempts)
        pre_slot_state = determine_next_state(collected)

        # If the planner wants lead_capture but we haven't shown the recommendation yet,
        # intercept and show it first.
        if (
            next_slot is not None
            and next_slot.state == ConversationState.LEAD_CAPTURE
            and pre_slot_state == ConversationState.RECOMMENDING
        ):
            return self._transition_to_recommendation_or_complete(
                collected, _answered, new_info={}
            )

        # No more slots to ask — transition to recommendation or lead capture
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
            cleaned = InfoNormalizer.normalize(extracted)
            if cleaned:
                collected.merge(cleaned)
                new_info = cleaned
                InfoNormalizer.sync_answered_slots(collected, _answered)

                # Check if the planned slot was answered via extraction
                if _is_slot_answered(next_slot, collected):
                    SlotPlanner.record_answered(next_slot.id, _answered)

        # ── 5. Enforce the ASK_SLOT contract on the LLM reply ──
        choice_validation = llm_result.get("choice_validation", "none")
        accepted_slot = llm_result.get("accepted_slot")
        suggested_choices = llm_result.get("suggested_choices", [])

        raw_reply = llm_result.get("reply", "") or ""
        reply, final_choices, choice_validation = SlotContractEnforcer.enforce(
            next_slot,
            raw_reply,
            suggested_choices,
            choice_validation,
        )

        # ── 6. Determine next state and handle transitions ──
        next_state = determine_next_state(collected)

        # If this slot pushed us past QUALIFYING into RECOMMENDING territory,
        # transition to the recommendation/lead-capture flow.
        if (
            state_order(next_slot.state) < state_order(ConversationState.RECOMMENDING)
            and state_order(next_state) >= state_order(ConversationState.RECOMMENDING)
        ):
            transition = self._transition_to_recommendation_or_complete(
                collected, _answered, new_info=new_info
            )
            if transition.type in {"recommendation", "clarification"}:
                transition.planned_slot = next_slot.id
                transition.accepted_slot = accepted_slot
                transition.choice_validation_result = choice_validation
                return transition
            # Fall through — keep asking
            next_state = next_slot.state

        # If the state machine says we've moved on but the slot planner hasn't,
        # signal the override to the frontend.
        if next_state != next_slot.state:
            new_info["__state_override"] = next_state.value

        # ── 7. Build debug trace ──
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

    def _transition_to_recommendation_or_complete(
        self,
        collected: CollectedInfo,
        answered_slots: Set[str],
        new_info: Dict[str, Any],
    ) -> ChatResponse:
        """
        Determine whether to show a recommendation, go to lead capture,
        or complete the conversation.

        Decision tree:
        - Have basics (vertical + indoor_outdoor) + some technical data? → product match + recommendation
        - No match found? → offer specialist connection
        - Already in lead capture phase? → ask for missing fields or finalize
        - Fallback → start lead capture
        """
        tech_answered = any(
            sid in answered_slots
            for sid in ["card_types", "needs_pin", "is_standalone"]
        )
        has_basics = (
            "vertical" in answered_slots
            and "indoor_outdoor" in answered_slots
        )

        if has_basics and tech_answered:
            rows, constraints, debug_match = ProductMatcher.match(collected)
            if rows:
                bundle = ProductMatcher.build_recommendation_bundle(rows, constraints)
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

        # ── Lead capture phase ──
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

        # ── Fallback: start lead capture ──
        return ChatResponse(
            type="clarification",
            text="I have enough information to work with. To provide the best recommendation, could you share your name and email so a specialist can follow up?",
            quick_replies=["Sure, I'll share my details", "No thanks"],
        )

    @staticmethod
    def _get_ui_actions(state: ConversationState) -> List[str]:
        """Return UI-action hints for the frontend based on conversation state."""
        if state == ConversationState.LEAD_CAPTURE:
            return ["show_lead_form"]
        elif state == ConversationState.HANDOFF:
            return ["offer_booking"]
        return []


# ── Singleton factory ──
_service_instance = ChatService()

def get_chat_service() -> ChatService:
    return _service_instance
