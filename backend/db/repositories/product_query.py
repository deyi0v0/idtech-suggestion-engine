from sqlalchemy.orm import Session
from sqlalchemy import select, or_, not_, func, cast, String
from engine.rulesEngine.filters_schemas import HardwareFilters
from ..models.hardware import Hardware
from ..models.software import Software
from ..models.category import Category
from ..models.associations import hardware_software_map
from ..models.use_case import UseCase
from typing import List, Optional, Any

SOFTWARE_DATASHEETS = {
    "RKI": "https://idtechproducts.com/wp-content/uploads/2024/11/RKI_Datasheet_v03.24.pdf",
    "RDM": "https://idtechproducts.com/wp-content/uploads/2025/03/RDM_DataSheet_v02.27.25.pdf",
    "PAE": "https://idtechproducts.com/wp-content/uploads/2026/03/PAE_Datasheet_v03.11.26.pdf"
}

# example, complete & improve the implementation
class ProductRepository:
    def __init__(self, db: Session):
        self.db = db
  
    def find_hardware(self, constraints: HardwareFilters) -> List[Hardware]:
        """
        Search hardware based on category, use case, or a general search query.
        """
        stmt = select(Hardware)

        if constraints.model_name:
            stmt = stmt.where(Hardware.model_name.ilike(f"%{constraints.model_name}%"))

        if constraints.category:
            stmt = stmt.join(Hardware.categories).where(Category.name.ilike(f"%{constraints.category}%"))

        if constraints.use_case:
            stmt = stmt.join(Hardware.use_cases).where(UseCase.name.ilike(f"%{constraints.use_case}%"))

        if constraints.interface:
            interfaces = constraints.interface
            if isinstance(interfaces, str):
                interfaces = [interfaces]

            stmt = stmt.where(
                or_(*[
                    Hardware.interface.ilike(f"%{i}%")
                    for i in interfaces
                ])
            )

        if constraints.input_power:
            stmt = stmt.where(Hardware.input_power.ilike(f"%{constraints.input_power}%"))

        if constraints.is_outdoor is True:
            stmt = stmt.where(
                or_(
                    Hardware.ip_rating.ilike("%IP65%"),
                    Hardware.ip_rating.ilike("%IP66%"),
                    Hardware.ip_rating.ilike("%IP67%"),
                    Hardware.ip_rating.ilike("%IP68%"),
                    Hardware.ip_rating.ilike("%IP69%")
                )
            ) 

        if constraints.is_standalone is True:
            stmt = stmt.where(
                or_(
                    Hardware.extra_specs.ilike("%processor%"),
                    Hardware.extra_specs.ilike("%CPU%"),
                    Hardware.extra_specs.ilike("%RAM%"),
                    Hardware.extra_specs.ilike("%memory%"),
                    Hardware.extra_specs.ilike("%Flash%"),
                    Hardware.extra_specs.ilike("%ARM Processor%"),
                )
            )

        if constraints.extra_specs:
            filters = constraints.extra_specs
            if isinstance(filters, str):
                filters = [filters]

            stmt = stmt.where(
                or_(*[
                    Hardware.extra_specs.ilike(f"%{f.strip()}%")
                    for f in filters if f
                ])
            )

        # if constraints.operate_temperature: #change
        #     stmt = stmt.where(Hardware.operate_temperature.ilike(f"%{constraints.operate_temperature}%"))

        
        return self.db.execute(stmt).scalars().unique().all()
    
    def get_hardware_by_name(self, model_name: str) -> Optional[Hardware]:
        stmt = select(Hardware).where(Hardware.model_name == model_name)
        return self.db.execute(stmt).scalar_one_or_none()

    def get_software_by_name(self, name: str) -> Optional[Software]:
        stmt = select(Software).where(Software.name == name)
        return self.db.execute(stmt).scalar_one_or_none()
    
    def get_software_for_hardware(self, constraints):
        stmt = (
            select(Software)
            .join(
                hardware_software_map,
                Software.id == hardware_software_map.c.software_id
            )
            .join(
                Hardware,
                Hardware.id == hardware_software_map.c.hardware_id
            )
            .where(Hardware.model_name == constraints.model_name)
        )

        return self.db.execute(stmt).scalars().unique().all()
    
    def fetch_software_datasheets(self, model_name: str) -> List[dict]:
        hardware = self.get_hardware_by_name(model_name)
        if not hardware:
            return []
        
        results = []
        for software in hardware.software:
            url = SOFTWARE_DATASHEETS.get(software.name)
            if url:
                results.append({
                    "name": software.name,
                    "url": url
                })
        
        return results
