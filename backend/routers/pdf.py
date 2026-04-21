from fastapi import APIRouter, Response
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from ..pdf_generator import generate_pdf

router = APIRouter()

class PDFRequest(BaseModel):
    hardware_name: str
    software_name: Optional[str] = None
    highlights: List[str] = []
    explanation: str

@router.post("/generate")
async def generate_pdf_endpoint(bundle: PDFRequest):
    """
    Receives the RecommendationBundle and returns a downloadable PDF.
    """
    # Convert Pydantic model to dict for the generator
    pdf_bytes = generate_pdf(bundle.model_dump())
    
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"attachment; filename=IDTECH_Recommendation_{bundle.hardware_name}.pdf"
        }
    )
