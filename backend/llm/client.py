import json
import logging
import os
from typing import Any, Dict, List, Optional

from dotenv import load_dotenv
from openai import OpenAI

from .prompts import TOOLS, build_chat_prompt

load_dotenv()
logger = logging.getLogger(__name__)


class LLMClient:
    """
    Thin wrapper around OpenAI. Responsibilities:
    - Call the LLM with per-state prompt + tools
    - Parse tool call arguments (update_lead_info)
    - Return the extracted data + assistant text reply
    - DOES NOT contain product logic, state machine, or recommendation building
    """

    def __init__(self) -> None:
        api_key = os.getenv("OPENAI_API_KEY") or os.getenv("OPENAI_ADMIN_KEY")
        if not api_key:
            api_key = "test-key"
        self.client = OpenAI(api_key=api_key)
        self.model = "gpt-4o-mini"
        self.max_attempts = 2

    def process_turn(
        self,
        message: str,
        history: List[Dict[str, str]],
        state: str = "greeting",
        collected_info: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Send a turn to the LLM and return:
        {
            "reply": str,            # The assistant's text response
            "extracted_info": dict,  # Data extracted via update_lead_info tool call
            "tool_was_called": bool, # Whether the tool was invoked
        }
        """
        messages = build_chat_prompt(message, history, state, collected_info)

        for attempt in range(1, self.max_attempts + 1):
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                tools=TOOLS,
                tool_choice="auto",
            )
            response_message = response.choices[0].message
            messages.append(response_message)

            tool_calls = response_message.tool_calls or []

            if not tool_calls:
                # No tool called — just return the text reply
                return {
                    "reply": response_message.content or "",
                    "extracted_info": {},
                    "tool_was_called": False,
                }

            for tool_call in tool_calls:
                fname = tool_call.function.name
                if fname == "update_lead_info":
                    args = self._try_parse_json(tool_call.function.arguments) or {}
                    return {
                        "reply": response_message.content or "",
                        "extracted_info": args,
                        "tool_was_called": True,
                    }

            # Unknown tool — force retry
            messages.append({
                "role": "system",
                "content": "Only use the `update_lead_info` tool to capture information.",
            })

        # Fallback after max attempts
        return {
            "reply": "Could you tell me a bit more about your setup?",
            "extracted_info": {},
            "tool_was_called": False,
        }

    @staticmethod
    def _try_parse_json(value: Any) -> Optional[Dict[str, Any]]:
        if not isinstance(value, str):
            return None
        stripped = value.strip()
        if stripped.startswith("```json"):
            stripped = stripped[len("```json"):].strip()
        if stripped.endswith("```"):
            stripped = stripped[:-3].strip()
        try:
            obj = json.loads(stripped)
            return obj if isinstance(obj, dict) else None
        except Exception:
            return None


_client_instance = LLMClient()


def process_turn(
    message: str,
    history: List[Dict[str, str]],
    state: str = "greeting",
    collected_info: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    return _client_instance.process_turn(message, history, state, collected_info)
