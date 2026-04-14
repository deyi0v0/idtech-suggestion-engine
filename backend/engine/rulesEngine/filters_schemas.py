from dataclasses import dataclass
from typing import Optional

@dataclass
class HardwareFilters:
    def __init__(self):
        pass

    use_case: Optional[str] = None
    operating_temp: Optional[str] = None
    dust_protection: Optional[str] = None
    water_protection: Optional[str] = None
    durability: Optional[str] = None
    # input_power: Optional[str] = None
    # interface: Optional[str] = None
    #extra_specs: Optional[str] = None