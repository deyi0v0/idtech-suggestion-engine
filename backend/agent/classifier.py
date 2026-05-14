"""
Intent classifier for the agentic loop.

Uses gpt-4o-mini for lightweight, fast classification of every incoming
user message before the main agent processes it.

Intents:
    product_search  — prospect wants to explore/find hardware
    faq             — asking about pricing, shipping, warranty, etc.
    qualification   — answering questions about their setup/needs
    lead_capture    — ready to share contact info or asking about next steps
    escalate        — explicitly wants to speak to a person
    greeting        — first message or general hello
    chitchat        — off-topic or non-sales conversation
"""

from __future__ import annotations

import logging
import os
from typing import Any, Dict, Tuple

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()
logger = logging.getLogger(__name__)


CLASSIFIER_SYSTEM_PROMPT = """
You are a message classifier for a B2B payment hardware company's sales chatbot.

Classify the user's message into exactly one of these intents:

- greeting: Initial hello, introduction, or "how can you help me" — the prospect just arrived.
- qualification: Prospect is answering questions about their business, environment, or technical needs. Includes phrases like "we're a parking lot", "it's for outdoor use", "about 5000 transactions", "we need PIN entry".
- product_search: Prospect is explicitly looking for a product, asking what you recommend, or describing what they need in hardware terms. "What do you have for...", "I need a reader that..."
- faq: Asking about pricing, cost, shipping, warranty, returns, compatibility, security, support, or general company information.
- lead_capture: Prospect is ready to share contact details, wants a call, says "connect me", or asks what happens next after a recommendation.
- escalate: Prospect explicitly asks to speak to a person, says "talk to sales", "need a human", "call me", or is frustrated.
- chitchat: Completely unrelated to payment hardware or ID TECH. Includes jokes, off-topic questions, or political/social topics.

Reply with ONLY the intent string in lowercase. No explanation, no punctuation, no extra whitespace.
""".strip()


class IntentClassifier:
    """Lightweight intent classifier using gpt-4o-mini."""

    VALID_INTENTS = {
        "greeting", "qualification", "product_search", "faq",
        "lead_capture", "escalate", "chitchat",
    }

    def __init__(self) -> None:
        api_key = os.getenv("OPENAI_API_KEY") or os.getenv("OPENAI_ADMIN_KEY")
        self.client = OpenAI(api_key=api_key or "test-key")
        self.model = "gpt-4o-mini"

    def classify(self, user_message: str) -> Tuple[str, float, Dict[str, Any]]:
        """
        Classify the user's message into one of the known intents.

        Returns:
            (intent, confidence, extracted_entities)

        confidence is 1.0 since gpt-4o-mini doesn't provide logprobs easily.
        extracted_entities is currently empty; the slot extractor handles entity extraction.
        """
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                max_tokens=10,
                temperature=0,
                messages=[
                    {"role": "system", "content": CLASSIFIER_SYSTEM_PROMPT},
                    {"role": "user", "content": user_message},
                ],
            )
            raw = response.choices[0].message.content or ""
            intent = raw.strip().lower()

            if intent not in self.VALID_INTENTS:
                logger.warning("Unknown intent '%s', defaulting to 'qualification'", intent)
                intent = "qualification"

            return intent, 1.0, {}

        except Exception as e:
            logger.exception("Intent classification failed")
            return "qualification", 0.0, {"error": str(e)}


# Singleton
_classifier = IntentClassifier()


def classify_intent(user_message: str) -> Tuple[str, float, Dict[str, Any]]:
    """Convenience wrapper around the singleton classifier."""
    return _classifier.classify(user_message)
