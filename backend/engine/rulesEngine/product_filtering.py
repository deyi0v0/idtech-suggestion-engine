from sqlalchemy.orm import Session
from typing import Dict, Any, List
from ...db.repositories.product_query import ProductRepository

def product_filtering(db: Session, constraints: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Search product based on constraints like category, use case, or environment.
    Example constraints: {"category": "Outdoor", "use_case": "EV station"}
    """
    repo = ProductRepository(db)

