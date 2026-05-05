from fastapi import APIRouter, HTTPException
import json
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from backend.llm.client import get_chat_response

router = APIRouter()

class ChatRequest(BaseModel):
    message: str
    history: List[Dict[str, str]] = []
    force_recommendation: bool = False

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
        response = get_chat_response(request.message, request.history, request.force_recommendation)

        # If the LLM returned a wrapper dict with a `content` string that itself
        # contains JSON (possibly fenced with ```json), try to parse it and use
        # the parsed object as the response so downstream logic can detect a
        # RecommendationBundle (hardware_name / hardware_items).
        if isinstance(response, dict):
            content = response.get("content")
            if isinstance(content, str):
                # Strip common code fences
                stripped = content.strip()
                if stripped.startswith("```json") and stripped.endswith("```"):
                    stripped = stripped[len("```json"):].rstrip("`").strip()
                # Try to find JSON object boundaries if the content contains extra text
                try:
                    # If it starts with {, try loading directly
                    if stripped.startswith("{"):
                        parsed = json.loads(stripped)
                        if isinstance(parsed, dict):
                            response = parsed
                    else:
                        # Try to extract first {...} block
                        start = stripped.find("{")
                        end = stripped.rfind("}")
                        if start != -1 and end != -1 and end > start:
                            candidate = stripped[start:end+1]
                            parsed = json.loads(candidate)
                            if isinstance(parsed, dict):
                                response = parsed
                except Exception:
                    # Ignore parse errors and fall back to original response
                    pass

            has_hardware_items = isinstance(response.get("hardware_items"), list) and len(response.get("hardware_items")) > 0
            response["show_recommendation_modal"] = has_hardware_items or bool(_extract_hardware_name(response))
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
