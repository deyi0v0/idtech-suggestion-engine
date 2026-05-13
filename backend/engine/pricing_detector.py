"""
Simple service to detect pricing-related keywords in user messages.
"""

from ..llm.contracts import ChatResponse


class PricingDetector:
    """
    Detects when a user is asking about pricing/quoting and returns a
    predefined clarifying response.

    This is a lightweight keyword-matching service kept separate from the
    main orchestration to isolate a single, stable concern.
    """

    PRICING_KEYWORDS = [
        "price", "pricing", "cost", "costs", "quote", "quotes",
        "how much", "rate", "rates", "cheap", "expensive", "budget",
    ]

    @staticmethod
    def detect(message: str) -> bool:
        """Return True if the message contains pricing-related keywords."""
        lower = message.lower()
        return any(kw in lower for kw in PricingDetector.PRICING_KEYWORDS)

    @staticmethod
    def build_response() -> ChatResponse:
        """Return a canned ChatResponse for pricing inquiries."""
        return ChatResponse(
            type="clarification",
            text="Pricing depends on volume and configuration — I can connect you with a specialist who can provide a customized quote. Would you like me to collect your contact info for a follow-up?",
            quick_replies=["Yes, please connect me", "No thanks, just browsing"],
            ui_actions=["offer_booking"],
        )
