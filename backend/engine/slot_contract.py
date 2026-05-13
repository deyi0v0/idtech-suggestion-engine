"""
Enforces the ASK_SLOT contract between the LLM and the slot planner.

When a slot is planned, the LLM MUST produce a valid question about that slot.
If it doesn't (e.g., it changes the subject, or produces a closing remark),
this service falls back to a canned question and appropriate choices.

This is the backend's last line of defense against LLM drift.
"""

from typing import List, Tuple

from ..engine.slot_planner import SlotDef


class SlotContractEnforcer:
    """
    Validates the LLM's output against the slot contract and provides
    fallback questions/choices when the LLM fails.
    """

    @staticmethod
    def is_valid_question_reply(text: str) -> bool:
        """Check if the LLM reply is a valid single-question message."""
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
    def fallback_question_for_slot(slot: SlotDef) -> str:
        """Return a deterministic canned question for a given slot."""
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
    def enforce(
        slot: SlotDef,
        reply: str,
        suggested_choices: List[str],
        choice_validation: str,
    ) -> Tuple[str, List[str], str]:
        """
        Enforce the ASK_SLOT contract.

        Returns:
            (final_reply, final_choices, final_validation)
        """
        final_reply = reply
        final_choices: List[str] = []
        final_validation = choice_validation

        if not SlotContractEnforcer.is_valid_question_reply(final_reply):
            final_reply = SlotContractEnforcer.fallback_question_for_slot(slot)
            final_validation = "contract_reply_fallback"

        # Free-text slots don't need choices
        if slot.parser.value == "free_text":
            return final_reply, [], final_validation

        # Use LLM-suggested choices if they're valid
        if suggested_choices and choice_validation == "valid":
            final_choices = list(suggested_choices)[:4]
            return final_reply, final_choices, final_validation

        # Fallback to predefined choices
        final_choices = list(slot.fallback_choices or [])[:4]
        if final_validation in ("none", "rejected_mismatch", "rejected_vocab"):
            final_validation = "contract_choices_fallback"
        return final_reply, final_choices, final_validation
