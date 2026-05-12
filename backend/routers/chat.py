from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from backend.engine.chat_service import ChatService, get_chat_service
from backend.engine.conversation_store import ConversationStore, get_conversation_store
from backend.llm.contracts import ChatResponse

router = APIRouter()

WELCOME_MESSAGE = (
    "Hi, I'm the ID TECH solutions assistant. I can help match you with the right "
    "payment hardware. What industry or use case are you working on?"
)


class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None


class SessionCreateResponse(BaseModel):
    session_id: str
    message: str
    stage: str


def normalize_chat_response(payload: ChatResponse) -> Dict[str, Any]:
    """Ensure the response is clean and serializable."""
    result = payload.model_dump(exclude_none=True)
    if "planned_slot" in result and result["planned_slot"] is None:
        del result["planned_slot"]
    return result


def _deep_merge_dict(base: Dict[str, Any], incoming: Dict[str, Any]) -> Dict[str, Any]:
    for key, value in incoming.items():
        if isinstance(value, dict) and isinstance(base.get(key), dict):
            _deep_merge_dict(base[key], value)
        else:
            base[key] = value
    return base


@router.post("/session", response_model=SessionCreateResponse)
async def create_session(
    store: ConversationStore = Depends(get_conversation_store),
):
    session_id = store.ensure_session(None)
    return SessionCreateResponse(
        session_id=session_id,
        message=WELCOME_MESSAGE,
        stage="greeting",
    )


@router.post("/chat")
async def chat_endpoint(
    request: ChatRequest,
    chat_service: ChatService = Depends(get_chat_service),
    store: ConversationStore = Depends(get_conversation_store),
):
    try:
        session_id = store.ensure_session(request.session_id)
        session = store.get_session(session_id)

        # Backend is the source of truth for memory/state.
        session_history = session.get("history", [])
        session_collected = session.get("collected_info", {})
        asked_slots = session.get("asked_slots", set())
        answered_slots = session.get("answered_slots", set())
        slot_attempts = session.get("slot_attempts", {})

        response = chat_service.process_message(
            message=request.message,
            history=session_history,
            collected_info=session_collected,
            asked_slots=asked_slots,
            answered_slots=answered_slots,
            slot_attempts=slot_attempts,
        )

        payload = normalize_chat_response(response)

        # Persist structured info extracted this turn.
        merged_collected = dict(session_collected)
        new_info = payload.get("new_info", {})
        if isinstance(new_info, dict):
            filtered_new_info = {k: v for k, v in new_info.items() if k != "__state_override"}
            _deep_merge_dict(merged_collected, filtered_new_info)

        # Persist message history.
        updated_history = list(session_history)
        updated_history.append({"role": "user", "content": request.message})
        assistant_text = payload.get("text", "")
        if isinstance(assistant_text, str) and assistant_text.strip():
            updated_history.append({"role": "assistant", "content": assistant_text})

        # Persist slot planner metadata mutated by ChatService.
        updated_asked = set(asked_slots)
        updated_answered = set(answered_slots)
        updated_attempts = dict(slot_attempts)

        accepted_slot = payload.get("accepted_slot")
        if accepted_slot and payload.get("choice_validation_result") == "valid":
            updated_answered.add(accepted_slot)

        store.save_session(
            session_id,
            updated_history,
            merged_collected,
            asked_slots=updated_asked,
            answered_slots=updated_answered,
            slot_attempts=updated_attempts,
            last_planned_slot=payload.get("planned_slot"),
        )

        payload["session_id"] = session_id
        return payload
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
