from sqlalchemy.orm import Session
from typing import Dict, Any, List
import json
import re
from db.repositories.product_query import ProductRepository
from engine.rulesEngine.filters_schemas import HardwareFilters

def product_filtering(db: Session, constraints: dict) -> List[Dict[str, Any]]:
    """
    Search product based on constraints like category, use case, or environment.
    Example constraints: {"category": "Outdoor", "use_case": "EV station"}
    """
    if isinstance(constraints, list):
        constraints = constraints[0] if constraints else {}
    
    hardware_filter = HardwareFilters()
    hardware_filter.category = constraints.get("category") 
    hardware_filter.use_case = constraints.get("use_case") 
    hardware_filter.input_power = constraints.get("input_power")
    hardware_filter.interface = constraints.get("interface")
    hardware_filter.is_outdoor = constraints.get("is_outdoor")
    hardware_filter.operate_temperature = constraints.get("operate_temperature")
    hardware_filter.extra_specs = constraints.get("extra_specs_filter")
    hardware_filter.search_query = constraints.get("search_query")
    
    repo = ProductRepository(db)

    hardware_options = repo.find_hardware(hardware_filter)
    return [build_response(hw, repo) for hw in hardware_options]

def build_response(hw, repo):
    # software
    software = repo.get_software_for_hardware(hw.model_name)

    # highlights
    categories = [cat.name for cat in hw.categories]
    use_cases = [uc.name for uc in hw.use_cases]

    highlights = (
        categories + use_cases +
        [
            hw.input_power,
            hw.interface,
            hw.operate_temperature,
        ]
    )

    # metadata
    metadata = {
        "model_name": hw.model_name,
        "interface": hw.interface,
        "operate_temperature": hw.operate_temperature,
        "input_power": hw.input_power,
        "ip_rating": hw.ip_rating,
        "ik_rating": hw.ik_rating,
        "extra_specs": hw.extra_specs or {},
    }

    return {
        "hardware_name": hw.model_name,
        "software_name": software,
        "highlights": highlights,
        "explanation_metadata": metadata,
    }

def query_software_for_hardware(db: Session, constraints: HardwareFilters) -> List[Dict[str, Any]]:
    repo = ProductRepository(db)
    hardware_options = repo.get_software_for_hardware(constraints)
    return hardware_options

def parse_interfaces(interface_str: str):
    cleaned = interface_str.replace("&", ",")

    parts = cleaned.split(",")

    results = []
    for part in parts:
        part = re.sub(r"\(.*?\)", "", part)

        part = part.strip()

        if part:
            results.append(part)

    return results
