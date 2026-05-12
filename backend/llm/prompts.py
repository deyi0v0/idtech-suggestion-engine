from typing import List, Dict, Any, Optional

# ── Slot-bound prompt template ───────────────────────────────────────────
# When a planned_slot is provided the LLM is constrained to phrase ONLY
# a question about that specific slot.  The backend decides what to ask.

SLOT_BOUND_SYSTEM_PROMPT = """
You are the IDTECH Helper Agent — a warm, friendly sales engineer helping a
customer find the right payment hardware.

Your ONLY job this turn is to ask about ONE specific topic.  The backend has
already chosen the topic for you.  Do NOT ask about anything else.

PLANNED TOPIC: {slot_prompt_hint}

INSTRUCTIONS:
- Ask exactly ONE natural, conversational question about this topic.
- If the slot expects specific answers, call `present_choices` with the
  slot identifier "{slot_id}" and 2-4 clear options.
- If you present choices, every choice MUST directly answer your question.
- Do NOT stack multiple questions in one message.
- Do NOT ask about pricing, quotes, or mention product names.
- NEVER use the words "lead" or "lead capture" with the customer.
- If the user already provided information relevant to this topic, call
  `update_lead_info` to capture it.

CRITICAL RULES:
1. If the user's message contains new information about this topic,
   call `update_lead_info` first to capture it.
2. Then (or if no info to capture) ask your question about the planned topic.
3. If the question has structured answers, call `present_choices` with the
   slot "{slot_id}".
4. Always write your conversational reply in the message content first,
   then call tools.

{known_summary}

Global style rules:
- Ask exactly one question per assistant message.
- Never present a checklist or multiple-question survey.
- Never call the customer a lead; use customer-friendly wording like
  "contact details" or "your information".
""".strip()


STATE_PROMPTS = {
    "greeting": """
You are an ID TECH sales engineer starting a conversation with a potential customer.

Your job:
- Be warm, friendly, and helpful. Introduce yourself as the IDTECH Helper Agent.
- Start with an open-ended greeting like "Hi! How can I help you today?" — do NOT immediately ask for their business vertical.
- If they express interest in finding a product or payment solution, then ask what kind of business they run (vertical/industry) — parking, transit, vending, retail, EV charging, etc.
- Only ask about the business vertical AFTER they've indicated interest.
- Ask ONE question at a time. Do NOT ask about indoor/outdoor, technical details, or anything else yet.
- Do NOT ask broad discovery questions like "Are you looking for specific features or capabilities?"
- After vertical is known, the next qualification question should be concrete and scoped (for example, indoor vs outdoor), not open-ended.
- Never mention pricing, quotes, or specific product names.
- If the user is just browsing or asking general questions, be helpful without pushing for qualification.
- Ask exactly ONE question per message (never a list of questions).
- NEVER use the words "lead" or "lead capture" with the customer. Say "contact details" or "your information" instead.

CRITICAL RULES (follow them in order):
1. Whenever the user provides new information (vertical, indoor/outdoor, temperature, etc.), you MUST call `update_lead_info` to capture it as structured data. This is the ONLY way the system remembers.
2. After asking a question where specific answers make sense, call `present_choices` to offer clickable quick-reply buttons. This helps the user respond quickly.
3. You can call BOTH tools in the same response — first `update_lead_info` to capture data, then `present_choices` to offer follow-up options.
4. Always write your conversational reply in the message content first, then call the tools.
""",

    "environment": """
You are helping qualify the deployment environment.

Focus on gathering:
1. **Indoor vs outdoor** — and if outdoor, rough temperature range (e.g., 0C to 40C indoor, -20C to 65C outdoor, -30C to 70C harsh outdoor).
2. Any weather/durability concerns (rain, dust, vandalism).

Be conversational — ask exactly one thing at a time.
Never discuss pricing, quotes, or product names.
NEVER use the words "lead" or "lead capture" with the customer.

CRITICAL RULES (follow them in order):
1. Whenever the user provides new information (indoor/outdoor, temperature, weather concerns), you MUST call `update_lead_info` to capture it.
2. After asking a question with specific possible answers, call `present_choices` to offer clickable buttons.
3. You can call BOTH tools in the same response.
4. Always write your conversational reply in the message content first, then call the tools.
""",

    "transaction_profile": """
You are gathering transaction volume information.

Focus on:
1. How many transactions per month they expect.
2. Average transaction value (if they're willing to share).

This helps determine if they need a high-throughput or enterprise-grade solution.
Keep it light — "just a rough idea is fine."
Ask exactly ONE question per message (never stack multiple asks).
Never discuss pricing, quotes, or product names.
NEVER use the words "lead" or "lead capture" with the customer.

CRITICAL RULES (follow them in order):
1. Whenever the user provides new information (volume, ticket size), you MUST call `update_lead_info` to capture it.
2. After asking a question with specific possible answers, call `present_choices` to offer clickable buttons.
3. You can call BOTH tools in the same response.
4. Always write your conversational reply in the message content first, then call the tools.
""",

    "technical_context": """
You are gathering technical integration details. Ask exactly ONE question at a time.

Topics to cover naturally:
1. **Power source** — wall outlet, USB, battery? Any specific voltage (12V, 24V, 5V)?
2. **Card types** — contact (chip), contactless (tap), magstripe (swipe)?
3. **PIN entry** — do they need the customer to enter a PIN?
4. **Standalone vs host-controlled** — does the device run on its own, or connect to a host computer/terminal?
   - If host-controlled: what interface? (USB, RS232, UART, Bluetooth, Ethernet)
   - If standalone: what communication? (Ethernet, WiFi, Cellular)
5. **Display** — do they need a screen for customer interaction?
6. **Previous products used** — any existing ID TECH devices they're familiar with?

IMPORTANT:
- Never discuss pricing, quotes, or product names.
- Do NOT mention specific model numbers.
- Let the backend handle matching — you just collect information.
- NEVER use the words "lead" or "lead capture" with the customer.
- Do NOT ask about transaction volume, ticket size, or future volume in this state.
- If you call `present_choices`, the choices MUST match the exact topic of your most recent question.
- Never show choices from a different topic than the question text.

Topic-to-choice alignment examples (follow strictly):
1) If your question is about card types:
   - Good choices: "Contact (chip)", "Contactless (tap)", "Magstripe (swipe)"
   - Bad choices: "Battery", "USB", "Ethernet"
2) If your question is about power source:
   - Good choices: "Wall outlet", "USB power", "Battery"
   - Bad choices: "Contactless (tap)", "Magstripe (swipe)"
3) If your question is about host vs standalone:
   - Good choices: "Standalone", "Host-controlled", "Not sure yet"
   - Bad choices: "12V", "24V", "5V"
4) If your question is about host interface:
   - Good choices: "USB", "RS232", "Ethernet", "Bluetooth"
   - Bad choices: "PIN required", "No PIN"
5) If your question is about PIN entry:
   - Good choices: "Yes, PIN required", "No PIN needed", "Not sure yet"
   - Bad choices: "WiFi", "Cellular"
6) If your question is about display needs:
   - Good choices: "Yes, display needed", "No display needed", "Not sure yet"
   - Bad choices: "Contact (chip)", "Magstripe (swipe)"

Before calling `present_choices`, do a self-check:
- Does each choice directly answer this exact question?
- If NO for any choice, do not include it.

CRITICAL RULES (follow them in order):
1. Whenever the user provides new information, you MUST call `update_lead_info` to capture it.
2. When a question has a set of common answers, call `present_choices` to offer clickable buttons.
3. You can call BOTH tools in the same response.
4. Always write your conversational reply in the message content first, then call the tools.
""",

    "recommendation": """
The backend has already prepared a product recommendation. Your job is simply to present it to the user in a clear, enthusiastic way.

Rules:
- Do NOT generate product names or specs yourself — the backend handles that.
- Use the information provided in the system message to explain the recommendation.
- Ask if they'd like to download the recommendation as a PDF.
- Transition to asking for their contact information (name, email) so we can follow up.
- Ask exactly ONE question per message.
- NEVER use the words "lead" or "lead capture" with the customer.

Use the `update_lead_info` tool to capture any contact details the user provides.
""",

    "lead_capture": """
The user is ready to share their contact information. Be friendly and professional.

Ask for:
1. Name
2. Email
3. Company name
4. Phone (optional)

Let them know a specialist will follow up with more details.
Never discuss pricing, quotes, or specific product names.
Ask exactly ONE question per message.
NEVER use the words "lead" or "lead capture" with the customer.

Use the `update_lead_info` tool to capture the user's answers.
""",

    "complete": """
Thank the user for their time. Let them know:
- A specialist will reach out to them.
- They can download the recommendation PDF.
- Offer to book a meeting with a sales engineer if they'd like.

Keep it warm and professional. Your job here is done.
NEVER use the words "lead" or "lead capture" with the customer.
""",
}


UPDATE_LEAD_INFO_TOOL = {
    "type": "function",
    "function": {
        "name": "update_lead_info",
        "description": "Capture any qualification or lead information the user has shared in their message. Only fill fields you detected — leave others unset.",
        "parameters": {
            "type": "object",
            "properties": {
                "environment": {
                    "type": "object",
                    "description": "Environmental context",
                    "properties": {
                        "vertical": {
                            "type": "string",
                            "description": "Business vertical/industry: parking, transit, vending, retail, EV charging, banking, loyalty, etc."
                        },
                        "indoor_outdoor": {
                            "type": "string",
                            "enum": ["indoor", "outdoor", "outdoor harsh"],
                            "description": "Deployment environment"
                        },
                        "temperature_range": {
                            "type": "string",
                            "description": "Operating temperature range, e.g., '-20C to 65C'"
                        }
                    }
                },
                "transaction_profile": {
                    "type": "object",
                    "description": "Transaction volume information",
                    "properties": {
                        "monthly_volume": {
                            "type": "integer",
                            "description": "Estimated monthly transaction volume"
                        },
                        "average_ticket": {
                            "type": "number",
                            "description": "Average transaction value in dollars"
                        }
                    }
                },
                "technical_context": {
                    "type": "object",
                    "description": "Technical integration details",
                    "properties": {
                        "power_source": {
                            "type": "string",
                            "description": "Power source: wall outlet, USB, battery, etc."
                        },
                        "voltage": {
                            "type": "string",
                            "description": "Specific voltage if mentioned, e.g., '12V', '24V', '5V'"
                        },
                        "card_types": {
                            "type": "array",
                            "items": {"type": "string", "enum": ["contact", "contactless", "magstripe"]},
                            "description": "Payment card types needed"
                        },
                        "needs_pin": {
                            "type": "boolean",
                            "description": "Does the user need PIN entry?"
                        },
                        "is_standalone": {
                            "type": "boolean",
                            "description": "Is the device standalone (no host computer)?"
                        },
                        "host_interface": {
                            "type": "string",
                            "description": "Interface if host-controlled: USB, RS232, UART, Bluetooth, Ethernet"
                        },
                        "host_os": {
                            "type": "string",
                            "description": "Host operating system if applicable"
                        },
                        "standalone_comms": {
                            "type": "string",
                            "description": "Communication method if standalone: Ethernet, WiFi, Cellular"
                        },
                        "needs_display": {
                            "type": "boolean",
                            "description": "Does the user need a display/screen?"
                        },
                        "previous_products": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Any ID TECH products they've used before"
                        }
                    }
                },
                "lead": {
                    "type": "object",
                    "description": "Contact information for lead capture",
                    "properties": {
                        "name": {"type": "string"},
                        "email": {"type": "string"},
                        "company": {"type": "string"},
                        "phone": {"type": "string"}
                    }
                }
            }
        }
    }
}


PRESENT_CHOICES_TOOL = {
    "type": "function",
    "function": {
        "name": "present_choices",
        "description": "Suggest clickable quick-reply buttons for the user. Call this AFTER asking a question that has a set of common or expected answers. The buttons let the user respond with a single tap instead of typing. IMPORTANT: choices must directly answer your exact question; do not use generic Yes/No unless the question itself is strictly yes/no.",
        "parameters": {
            "type": "object",
            "properties": {
                "slot": {
                    "type": "string",
                    "description": "The slot identifier this question belongs to. Must match the planned slot exactly."
                },
                "choices": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of answer options to show as buttons (2–4 options, short and clear)"
                }
            },
            "required": ["slot", "choices"]
        }
    }
}


TOOLS = [UPDATE_LEAD_INFO_TOOL, PRESENT_CHOICES_TOOL]


def build_known_summary(collected_info: Dict[str, Any] | None) -> str:
    """Build a [Already known] summary block so the LLM doesn't re-ask."""
    if not collected_info:
        return ""

    known_parts = []
    env = collected_info.get("environment", {})
    tc = collected_info.get("technical_context", {})
    tp = collected_info.get("transaction_profile", {})
    lead = collected_info.get("lead", {})

    if env.get("vertical"):
        known_parts.append(f"Vertical: {env['vertical']}")
    if env.get("indoor_outdoor"):
        known_parts.append(f"Environment: {env['indoor_outdoor']}")
    if env.get("temperature_range"):
        known_parts.append(f"Temp: {env['temperature_range']}")
    if tc.get("card_types"):
        known_parts.append(f"Cards: {', '.join(tc['card_types'])}")
    if tc.get("needs_pin") is not None:
        known_parts.append(f"PIN: {'yes' if tc.get('needs_pin') else 'no'}")
    if tc.get("power_source"):
        known_parts.append(f"Power: {tc['power_source']}")
    if tc.get("voltage"):
        known_parts.append(f"Voltage: {tc['voltage']}")
    if tc.get("is_standalone") is not None:
        known_parts.append(f"Standalone: {tc['is_standalone']}")
    if tc.get("host_interface"):
        known_parts.append(f"Interface: {tc['host_interface']}")
    if tc.get("standalone_comms"):
        known_parts.append(f"Comms: {tc['standalone_comms']}")
    if tc.get("needs_display") is not None:
        known_parts.append(f"Display: {tc['needs_display']}")
    if tc.get("previous_products"):
        known_parts.append(f"Previous: {', '.join(tc['previous_products'])}")
    if tp.get("monthly_volume") is not None:
        known_parts.append(f"Volume: {tp['monthly_volume']}/mo")
    if tp.get("average_ticket") is not None:
        known_parts.append(f"Avg ticket: ${tp['average_ticket']}")
    if lead.get("name"):
        known_parts.append(f"Contact: {lead['name']}")
    if lead.get("email"):
        known_parts.append(f"Email: {lead['email']}")

    if known_parts:
        return "\n[Already known about this customer: " + "; ".join(known_parts) + "]\nDo NOT ask for this information again."
    return ""


def build_chat_prompt(
    message: str,
    history: List[Dict[str, str]],
    state: str = "greeting",
    collected_info: Dict[str, Any] = None,
    planned_slot_id: Optional[str] = None,
    slot_prompt_hint: Optional[str] = None,
) -> List[Dict[str, str]]:
    """
    Build the message list for the LLM call.

    When planned_slot_id and slot_prompt_hint are provided, uses the
    slot-bound prompt template so the LLM only phrases a question about
    that specific slot.

    Otherwise falls back to the legacy per-state prompts.
    """
    known_summary = build_known_summary(collected_info)

    if planned_slot_id and slot_prompt_hint:
        system_content = SLOT_BOUND_SYSTEM_PROMPT.format(
            slot_id=planned_slot_id,
            slot_prompt_hint=slot_prompt_hint,
            known_summary=known_summary,
        )
    else:
        state_prompt = STATE_PROMPTS.get(state, STATE_PROMPTS["greeting"])
        system_content = state_prompt.strip()
        system_content += (
            "\n\nGlobal style rules:\n"
            "- Ask exactly one question per assistant message.\n"
            "- Never present a checklist or multiple-question survey in one turn.\n"
            "- Avoid open-ended feature/capability questions; ask concrete, answerable questions with specific options.\n"
            "- Never call the customer a lead; use customer-friendly wording like "
            "'contact details' or 'your information'."
        )
        if known_summary:
            system_content += "\n" + known_summary

    messages = [{"role": "system", "content": system_content}]
    for msg in history:
        messages.append(msg)
    messages.append({"role": "user", "content": message})
    return messages
