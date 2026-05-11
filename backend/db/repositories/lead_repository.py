from typing import Optional

from sqlalchemy.orm import Session

from ..models.lead import Lead


class LeadRepository:
    def __init__(self, db: Session):
        self.db = db

    def create_lead(
        self,
        name: Optional[str] = None,
        email: Optional[str] = None,
        company: Optional[str] = None,
        phone: Optional[str] = None,
        qualification: Optional[dict] = None,
        products_shown: Optional[dict] = None,
        status: str = "new",
    ) -> Lead:
        """Create a new lead record."""
        lead = Lead(
            name=name,
            email=email,
            company=company,
            phone=phone,
            qualification=qualification,
            products_shown=products_shown,
            status=status,
        )
        self.db.add(lead)
        self.db.commit()
        self.db.refresh(lead)
        return lead
