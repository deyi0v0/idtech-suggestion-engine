from __future__ import annotations

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
    - Parse tool call arguments (update_lead_info, present_choices)
    - Return the extracted data + assistant text reply + suggested choices
    - DOES NOT contain product logic, state machine, or recommendation building
    """

    def __init__(self) -> None:
        api_key = os.getenv("OPENAI_API_KEY") or os.getenv("OPENAI_ADMIN_KEY")
        if not api_key:
            api_key = "test-key"
        self.client = OpenAI(api_key=api_key)
        self.model = "gpt-4o-mini"
        self.max_attempts = 3

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
            "reply": str,                # The assistant's text response
            "extracted_info": dict,      # Data extracted via update_lead_info tool call
            "suggested_choices": list,   # Choices from present_choices tool call
            "tool_was_called": bool,     # Whether any tool was invoked
        }
        """
        messages: List[Dict[str, Any]] = build_chat_prompt(message, history, state, collected_info)

        extracted_info: Dict[str, Any] = {}
        suggested_choices: List[str] = []
        tool_was_called = False
        must_generate_text = False  # becomes True once tools have been processed

        for attempt in range(1, self.max_attempts + 1):
            # After tools have been processed once, force the LLM to produce
            # conversational text — no further tool calls allowed this turn.
            effective_tool_choice = "none" if must_generate_text else "auto"

            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    tools=TOOLS,
                    tool_choice=effective_tool_choice,
                )
            except Exception as exc:
                logger.error("OpenAI API call failed (attempt %d/%d): %s", attempt, self.max_attempts, exc)
                if attempt < self.max_attempts:
                    continue
                return {
                    "reply": "Sorry, I'm having trouble connecting right now. Could you try again?",
                    "extracted_info": extracted_info,
                    "suggested_choices": suggested_choices,
                    "tool_was_called": tool_was_called,
                }

            response_message = response.choices[0].message
            reply_text = response_message.content or ""

            # Append the assistant message (with tool_calls if any) to the conversation
            msg_dict: Dict[str, Any] = {
                "role": response_message.role,
                "content": reply_text,
            }
            if response_message.tool_calls:
                msg_dict["tool_calls"] = [tc.model_dump() for tc in response_message.tool_calls]
            messages.append(msg_dict)

            tool_calls = response_message.tool_calls or []

            # ── No tool calls → pure text response, we're done ──
            if not tool_calls:
                return {
                    "reply": reply_text,
                    "extracted_info": extracted_info,
                    "suggested_choices": suggested_choices,
                    "tool_was_called": tool_was_called,
                }

            # ── Process tool calls ──
            any_unknown = False
            for tool_call in tool_calls:
                fname = tool_call.function.name
                try:
                    args = json.loads(tool_call.function.arguments) if isinstance(tool_call.function.arguments, str) else {}
                except json.JSONDecodeError:
                    args = {}

                if fname == "update_lead_info":
                    extracted_info.update(args)
                    tool_was_called = True
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": "Information captured successfully.",
                    })
                elif fname == "present_choices":
                    choices = args.get("choices", [])
                    if isinstance(choices, list):
                        suggested_choices.extend(choices)
                    tool_was_called = True
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": "Choices noted.",
                    })
                else:
                    any_unknown = True
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": "Unknown tool. Only use the available tools.",
                    })

            # Tools processed — on the next iteration, force the LLM to generate
            # conversational text rather than calling more tools.
            must_generate_text = True

            if any_unknown:
                # Add an extra system hint and let the loop retry
                messages.append({
                    "role": "system",
                    "content": "Only use the `update_lead_info` and `present_choices` tools.",
                })
                # The next iteration will still use effective_tool_choice="auto"
                # since must_generate_text was just set, but the unknown tool
                # flow needs tools available for the correction.
                must_generate_text = False

        # Fallback after max attempts
        return {
            "reply": "Could you tell me a bit more about your setup?",
            "extracted_info": extracted_info,
            "suggested_choices": suggested_choices,
            "tool_was_called": tool_was_called,
        }


_client_instance = LLMClient()


def process_turn(
    message: str,
    history: List[Dict[str, str]],
    state: str = "greeting",
    collected_info: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    return _client_instance.process_turn(message, history, state, collected_info)
