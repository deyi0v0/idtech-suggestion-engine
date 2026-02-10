from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy import ForeignKey, Boolean # Import Boolean here
from base import Base

class compatibility_map(Base):
    __tablename__ = "compatibility_map"

    software_id = mapped_column(ForeignKey("software_apps.id"), primary_key=True)
    hardware_id = mapped_column(ForeignKey("hardware_devices.id"), primary_key = True)
    is_compatible: Mapped[bool] = mapped_column(Boolean, nullable=False) # Use Boolean from sqlalchemy

    def __repr__(self) -> str:
        return f"Software App(id={self.software_id}) is compatible with Hardware Device(id={self.hardware_id})"