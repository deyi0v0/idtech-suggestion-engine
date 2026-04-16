from pydantic import BaseModel
from typing import Optional, List

class InstallationDoc(BaseModel):
    title: str
    url: str

class HardwareRecommendation(BaseModel):
    model_name: str
    info: str
    operate_temperature: Optional[str] = None
    ip_rating: Optional[str] = None
    ik_rating: Optional[str] = None
    interface: Optional[str] = None
    extra_specs: Optional[dict] = None
    installation_docs: List[InstallationDoc] = []

class SoftwareRecommendation(BaseModel):
    name: str
    info: str
    datasheet_url: Optional[str] = None

class RecommendationBundle(BaseModel):
    hardware: HardwareRecommendation
    software: List[SoftwareRecommendation] = []
    llm_reasoning: str
    use_case: Optional[str] = None
    generated_at = None