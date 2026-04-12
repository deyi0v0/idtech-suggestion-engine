from sqlalchemy.orm import Session
from sqlalchemy import select, or_
from ..models.hardware import Hardware
from ..models.software import Software
from ..models.category import Category
from ..models.use_case import UseCase
from typing import List, Optional

# example, complete & improve the implementation
class ProductRepository:
    def __init__(self, db: Session):
        self.db = db

    def find_hardware(self, category_name: Optional[str] = None, use_case_name: Optional[str] = None, search_query: Optional[str] = None) -> List[Hardware]:
        """
        Search hardware based on category, use case, or a general search query.
        """
        stmt = select(Hardware)

        if category_name:
            stmt = stmt.join(Hardware.categories).where(Category.name.ilike(f"%{category_name}%"))
        
        if use_case_name:
            stmt = stmt.join(Hardware.use_cases).where(UseCase.name.ilike(f"%{use_case_name}%"))

        if search_query:
            stmt = stmt.where(or_(
                Hardware.model_name.ilike(f"%{search_query}%"),
                Hardware.interface.ilike(f"%{search_query}%")
            ))

        return self.db.execute(stmt).scalars().unique().all()

    def get_hardware_by_name(self, model_name: str) -> Optional[Hardware]:
        stmt = select(Hardware).where(Hardware.model_name == model_name)
        return self.db.execute(stmt).scalar_one_or_none()

    def get_software_by_name(self, name: str) -> Optional[Software]:
        stmt = select(Software).where(Software.name == name)
        return self.db.execute(stmt).scalar_one_or_none()
