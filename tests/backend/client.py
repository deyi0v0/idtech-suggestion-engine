"""
Simple stateless completion for use in test_api.py. Add lazy initialization for CI testing.
"""

from __future__ import annotations

import os
from typing import Any

from openai import OpenAI

_client: OpenAI | None = None


def _get_client() -> OpenAI:
    """Lazy-init the OpenAI client.  Raises if no API key is configured."""
    global _client
    if _client is None:
        api_key = os.getenv("OPENAI_API_KEY") or os.getenv("OPENAI_ADMIN_KEY")
        if not api_key:
            raise ValueError(
                "OPENAI_API_KEY (or OPENAI_ADMIN_KEY) environment variable not set"
            )
        _client = OpenAI(api_key=api_key)
    return _client


async def get_completion_from_messages(messages: list[dict[str, Any]]) -> str:
    try:
        client = _get_client()
        completion = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            max_tokens=100,
        )
        resp = completion.choices[0].message.content
        return resp or ""
    except Exception as e:
        print(f"{type(e)}: {e}")
        return f"Could not finish completion: {e}"
