from fastapi import APIRouter, Response
from ..pdf_generator import generate_pdf
from ..engine.solution_schemas import RecommendationBundle

router = APIRouter()

@router.post("/generate")
async def generate_pdf_endpoint(bundle: RecommendationBundle):
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
