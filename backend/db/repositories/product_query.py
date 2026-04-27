from sqlalchemy.orm import Session, joinedload
from sqlalchemy import select, String
from ..models.hardware import Hardware
from ..models.software import Software
from ..models.category import Category
from ..models.use_case import UseCase
from typing import List, Optional

class ProductRepository:
    def __init__(self, db: Session):
        self.db = db

    def find_products(self, 
                      category: Optional[str] = None, 
                      use_case: Optional[str] = None, 
                      input_power: Optional[str] = None,
                      interface: Optional[str] = None,
                      temp: Optional[str] = None,
                      extra_filter: Optional[str] = None,
                      query: Optional[str] = None) -> List[Hardware]:
        """
        Comprehensive search for hardware along with its compatible software.
        """
        # We use joinedload to pre-fetch the software and categories in one go
        stmt = select(Hardware).options(
            joinedload(Hardware.software),
            joinedload(Hardware.categories),
            joinedload(Hardware.use_cases)
        )

        filters = []
        
        if category:
            stmt = stmt.join(Hardware.categories).where(Category.name.ilike(f"%{category}%"))
        
        if use_case:
            stmt = stmt.join(Hardware.use_cases).where(UseCase.name.ilike(f"%{use_case}%"))

        if input_power:
            filters.append(Hardware.input_power.ilike(f"%{input_power}%"))
        
        if interface:
            filters.append(Hardware.interface.ilike(f"%{interface}%"))

        if temp:
            filters.append(Hardware.operate_temperature.ilike(f"%{temp}%"))

        if extra_filter:
            # Search inside the JSONB extra_specs field
            filters.append(Hardware.extra_specs.cast(String).ilike(f"%{extra_filter}%"))

        if query:
            filters.append(Hardware.model_name.ilike(f"%{query}%"))

        if filters:
            from sqlalchemy import and_
            stmt = stmt.where(and_(*filters))

        result = self.db.execute(stmt)
        return result.scalars().unique().all()
