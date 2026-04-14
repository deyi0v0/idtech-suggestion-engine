from sqlalchemy.orm import Session
from typing import Dict, Any, List
from db.repositories.product_query import ProductRepository
from engine.rulesEngine.filters_schemas import HardwareFilters

def product_filtering(db: Session, constraints: HardwareFilters) -> List[Dict[str, Any]]:
    """
    Search product based on constraints like category, use case, or environment.
    Example constraints: {"category": "Outdoor", "use_case": "EV station"}
    """
    repo = ProductRepository(db)

    hardware_options = repo.find_hardware(constraints)

    return hardware_options
