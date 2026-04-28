from sqlalchemy.orm import Mapped, mapped_column
from ..base import Base

class Category(Base):
    __tablename__ = "categories"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(unique=True, nullable=False)

    def __repr__(self) -> str:
        return f"Category(id={self.id}, name='{self.name}')"