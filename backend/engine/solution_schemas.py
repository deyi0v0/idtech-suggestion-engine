from pydantic import BaseModel
from typing import Optional, List

# it is known as the solution engine, it defines how the solution being structured in the pdf
# this is a protocol, improve it with reasonable design
# a tool of pdf generator

class HardwareRecommendation(BaseModel):
    model_name: str
    info: str
    install_url: Optional[str] = None
    operate_temperature: Optional[str] = None
    ip_rating: Optional[str] = None

class SoftwareRecommendation(BaseModel):
    name: str
    info: str
    url: Optional[str] = None

class RecommendationBundle(BaseModel):
    hardware: HardwareRecommendation
    software: SoftwareRecommendation
    llm_reasoning: str
