"""
Deterministic parsers that run *before* LLM extraction for high-frequency
user-input formats.  When a parser succeeds the slot is marked answered
without relying on the LLM tool call.
"""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional, Tuple


def parse_volume_ticket(text: str) -> Optional[Dict[str, Any]]:
    """
    Try to parse "1000 transactions, $10 each" style messages.

    Returns dict with monthly_volume and average_ticket if both found,
    or just one if only one is found.
    """
    result: Dict[str, Any] = {}

    # Look for a number followed by optional "transactions" or "/month" or "per month"
    volume_patterns = [
        r'(\d[\d,]*)\s*(?:transactions?|txns?|/month|per month|a month|monthly)',
        r'(?:about|around|approx(?:imately)?)\s*(\d[\d,]*)\s*(?:transactions?|txns?)?',
        r'(\d[\d,]*)\s*(?:transactions?|txns?)',
    ]
    for pat in volume_patterns:
        m = re.search(pat, text, re.IGNORECASE)
        if m:
            raw = m.group(1).replace(",", "")
            try:
                result["monthly_volume"] = int(raw)
            except ValueError:
                pass
            break

    # Look for dollar amounts
    ticket_patterns = [
        r'\$(\d+(?:\.\d{1,2})?)\s*(?:each|per|/|a ticket|average|avg)',
        r'(?:average|avg)(?:\s+ticket)?\s*(?:of|is|:)?\s*\$(\d+(?:\.\d{1,2})?)',
        r'\$(\d+(?:\.\d{1,2})?)',
    ]
    for pat in ticket_patterns:
        m = re.search(pat, text, re.IGNORECASE)
        if m:
            try:
                result["average_ticket"] = float(m.group(1))
            except ValueError:
                pass
            break

    return result if result else None


def parse_range(text: str) -> Optional[str]:
    """
    Parse a range like "500-1000", "-20C to 65C", "0C to 40C".
    Returns the cleaned range string.
    """
    # Match common range patterns
    patterns = [
        r'(-?\d+)\s*(?:°?[CF])\s*(?:to|–|-)\s*(-?\d+)\s*(?:°?[CF])',  # -20C to 65C
        r'(-?\d+)\s*(?:to|–|-)\s*(-?\d+)',  # 500-1000
    ]
    for pat in patterns:
        m = re.search(pat, text, re.IGNORECASE)
        if m:
            return f"{m.group(1)} to {m.group(2)}"
    return None


def parse_boolean(text: str) -> Optional[bool]:
    """
    Parse a yes/no/not-sure intent from user text.

    Returns:
        True  → affirmative (yes, yeah, yep, sure, definitely, absolutely)
        False → negative (no, nope, nah, not really, don't need)
        None  → ambiguous / "not sure" / can't determine
    """
    lowered = text.lower().strip(" .!?,;:\"'")

    # Strong affirmatives
    affirmative = {"yes", "yeah", "yep", "y", "sure", "definitely",
                   "absolutely", "of course", "i do", "we do", "correct",
                   "that's right", "right", "indeed", "please", "yes please"}
    # Strong negatives
    negative = {"no", "nope", "nah", "n", "not really", "don't need",
                "do not need", "don't", "no thanks", "not at all",
                "i don't", "we don't", "never", "no way"}

    # Check exact short answers first
    if lowered in affirmative:
        return True
    if lowered in negative:
        return False

    # Check substrings for longer messages
    for aff in sorted(affirmative, key=len, reverse=True):
        if aff in lowered and len(aff) > 3:
            # Avoid false positives like "not sure" matching "sure"
            if aff == "sure" and "not sure" in lowered:
                continue
            return True

    for neg in sorted(negative, key=len, reverse=True):
        if neg in lowered and len(neg) > 1:
            return False

    # "not sure" / "maybe" → treat as ambiguous (not answered)
    ambiguous = {"not sure", "not sure yet", "maybe", "i don't know",
                 "idk", "unsure", "don't know", "possibly"}
    if lowered in ambiguous or any(a in lowered for a in ambiguous):
        return None  # explicitly ambiguous

    return None  # can't determine


def parse_number(text: str) -> Optional[int]:
    """
    Parse a numeric value from text. Handles comma-separated thousands.
    Returns the first number found, or None.
    """
    # Try to find a standalone number (not part of a range)
    m = re.search(r'(?:^|\s)(\d[\d,]*(?:k|K| thousand)?)(?:\s|$)', text)
    if not m:
        m = re.search(r'(\d[\d,]*)', text)
    if m:
        raw = m.group(1).replace(",", "")
        # Handle "5k" style
        if raw.lower().endswith('k'):
            try:
                return int(float(raw[:-1]) * 1000)
            except ValueError:
                pass
        try:
            return int(raw)
        except ValueError:
            pass
    return None


def parse_choice(text: str, allowed_choices: List[str]) -> Optional[str]:
    """
    Match user text against a list of allowed choices.

    Uses fuzzy matching:
    1. Exact case-insensitive match
    2. Choice is a substring of user text
    3. User text is a substring of choice
    """
    lowered = text.lower().strip(" .!?,;:\"'")

    for choice in allowed_choices:
        choice_lower = choice.lower().strip()
        # Exact match
        if lowered == choice_lower:
            return choice
        # Choice contained in user text (e.g. "contactless" in "I need contactless for sure")
        if len(choice_lower) > 3 and choice_lower in lowered:
            return choice

    # User text is a substring of choice (e.g. "contact" matches "Contact (chip)")
    for choice in allowed_choices:
        choice_lower = choice.lower().strip()
        # Remove parentheticals for matching
        choice_clean = re.sub(r'\([^)]*\)', '', choice_lower).strip()
        if lowered in choice_clean or lowered in choice_lower:
            return choice

    return None


def is_not_sure(text: str) -> bool:
    """Check if the user is expressing uncertainty / 'not sure'."""
    lowered = text.lower().strip(" .!?,;:\"'")
    markers = {"not sure", "not sure yet", "maybe", "i don't know", "idk",
               "unsure", "don't know", "possibly", "not certain"}
    if lowered in markers:
        return True
    for marker in markers:
        if len(marker) > 4 and marker in lowered:
            return True
    return False


def try_parse_for_slot(text: str, slot_id: str, allowed_choices: List[str]) -> Optional[Any]:
    """
    Try to parse user input for a specific slot using deterministic parsers.

    Returns:
        The parsed value if successful.
        A special sentinel NOT_SURE if the user indicated uncertainty on a
          slot that accepts "not sure".
        None if parsing fails.
    """
    from .slot_planner import SLOT_BY_ID, SlotParser

    slot = SLOT_BY_ID.get(slot_id)
    if not slot:
        return None

    if slot.parser == SlotParser.BOOLEAN:
        result = parse_boolean(text)
        if result is not None:
            return result
        # If boolean parser returned None but user said "not sure",
        # return sentinel so caller knows it's ambiguous (not a failure)
        if slot.accept_not_sure and is_not_sure(text):
            return NOT_SURE
        return None

    if slot.parser == SlotParser.NUMBER:
        return parse_number(text)

    if slot.parser == SlotParser.VOLUME_TICKET:
        return parse_volume_ticket(text)

    if slot.parser == SlotParser.CHOICE:
        choices = allowed_choices or slot.allowed_choices
        result = parse_choice(text, choices)
        if result is not None:
            return result
        # Check if the user indicated uncertainty
        if slot.accept_not_sure and is_not_sure(text):
            return NOT_SURE
        return None

    # FREE_TEXT — just return the text as-is (no pre-parsing needed)
    return text.strip() if text.strip() else None


# Sentinel for "not sure" responses
class _NotSure:
    """Sentinel indicating the user answered 'not sure'."""
    def __bool__(self) -> bool:
        return False
    def __repr__(self) -> str:
        return "NOT_SURE"

NOT_SURE = _NotSure()
