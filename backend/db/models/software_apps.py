from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from base import Base

class software_apps(Base):
    __tablename__ = "software_apps"

    id: Mapped[int] = mapped_column(primary_key=True)

    def __repr__(self) -> str:
        return f"Software App(id={self.id})"