from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from backend.engine.chat_service import ChatService, get_chat_service
from backend.llm.contracts import ChatResponse

router = APIRouter()


class ChatRequest(BaseModel):
    message: str
    history: List[Dict[str, str]] = []
    collected_info: Dict[str, Any] = {}
    session_id: Optional[str] = None


def normalize_chat_response(payload: ChatResponse) -> Dict[str, Any]:
    """Ensure the response is clean and serializable."""
    return payload.model_dump(exclude_none=True)


@router.post("/chat")
async def chat_endpoint(
    request: ChatRequest,
    chat_service: ChatService = Depends(get_chat_service),
):
    try:
        response = chat_service.process_message(
            message=request.message,
            history=request.history,
            collected_info=request.collected_info,
        )
        return normalize_chat_response(response)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
