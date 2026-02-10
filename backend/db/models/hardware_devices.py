from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from base import Base

class hardware_devices(Base):
    __tablename__ = "hardware_devices"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(nullable=False)

    def __repr__(self) -> str:
        return f"Hardware Device(id={self.id}, name='{self.name}')"