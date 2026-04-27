from pydantic import BaseModel
from typing import Optional, List, Dict, Any

class InstallationDoc(BaseModel):
    title: str
    url: str

class SoftwareRecommendation(BaseModel):
    name: str
    datasheet_url: Optional[str] = None

class RecommendationBundle(BaseModel):
    hardware_name: str
    software: List[SoftwareRecommendation] = []
    highlights: List[str] = []
    explanation: str
    technical_specs: Dict[str, Any] = {}
    installation_docs: List[InstallationDoc] = []
