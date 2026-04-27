from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from ..llm.client import get_chat_response

router = APIRouter()

class ChatRequest(BaseModel):
    message: str
    history: List[Dict[str, str]] = []

def _extract_hardware_name(response: Dict[str, Any]) -> str:
    direct_name = response.get("hardware_name")
    if isinstance(direct_name, str):
        return direct_name.strip()

    # Supports nested recommendation shapes as a fallback.
    hardware = response.get("hardware")
    if isinstance(hardware, dict):
        model_name = hardware.get("model_name")
        if isinstance(model_name, str):
            return model_name.strip()
        nested_name = hardware.get("hardware_name")
        if isinstance(nested_name, str):
            return nested_name.strip()

    return ""

@router.post("/chat")
async def chat_endpoint(request: ChatRequest):
    """
    Takes user message and history, returns the LLM's structured JSON (RecommendationBundle or Question).
    """
    try:
        response = get_chat_response(request.message, request.history)
        if isinstance(response, dict):
            response["show_recommendation_modal"] = bool(_extract_hardware_name(response))
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
