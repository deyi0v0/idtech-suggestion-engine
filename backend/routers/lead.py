from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from backend.engine.lead_service import LeadService, get_lead_service

router = APIRouter()


class RequestCallRequest(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    company: Optional[str] = None
    phone: Optional[str] = None
    qualification: Optional[Dict[str, Any]] = None


@router.post("/request-call")
async def request_call(
    request: RequestCallRequest,
    lead_service: LeadService = Depends(get_lead_service),
):
    """Accept lead info and trigger a sales follow-up."""
    result = lead_service.save_lead(
        name=request.name,
        email=request.email,
        company=request.company,
        phone=request.phone,
        qualification=request.qualification,
        status="requested_call",
    )
    return {
        "success": True,
        "message": "Thanks! A specialist will reach out to you shortly.",
        "lead_id": result["id"],
    }
