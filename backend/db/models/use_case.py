from sqlalchemy.orm import Mapped, mapped_column
from ..base import Base

class UseCase(Base):
    __tablename__ = "use_cases"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(unique=True, nullable=False)

    def __repr__(self) -> str:
        return f"UseCase(id={self.id}, name='{self.name}')"
