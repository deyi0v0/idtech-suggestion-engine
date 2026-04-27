from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from ..llm.client import get_chat_response

router = APIRouter()

class ChatRequest(BaseModel):
    message: str
    history: List[Dict[str, str]] = []

@router.post("/chat")
async def chat_endpoint(request: ChatRequest):
    """
    Takes user message and history, returns the LLM's structured JSON (RecommendationBundle or Question).
    """
    try:
        response = get_chat_response(request.message, request.history)
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
