from dataclasses import dataclass
from typing import Optional, List

@dataclass
class HardwareFilters:
    def __init__(self):
        pass

    model_name: Optional[str] = None
    use_case: Optional[str] = None
    category: Optional[str] = None
    interface: Optional[List[str]] = None
    input_power: Optional[str] = None
    is_outdoor: Optional[bool] = None
    is_standalone: Optional[bool] = None
    extra_specs: Optional[str] = None
    search_query: Optional[str] = None
    operate_temperature: Optional[str] = None


    #dust_protection: Optional[int] = None
    #durability: Optional[str] = None
