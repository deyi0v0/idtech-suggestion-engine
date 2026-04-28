from sqlalchemy import Table, Column, ForeignKey, Integer
from ..base import Base

# Association Table for Hardware <-> Categories
hardware_category_map = Table(
    "hardware_category_map",
    Base.metadata,
    Column("hardware_id", Integer, ForeignKey("hardware.id"), primary_key=True),
    Column("category_id", Integer, ForeignKey("categories.id"), primary_key=True),
)

# Association Table for Hardware <-> Use Cases
hardware_use_case_map = Table(
    "hardware_use_case_map",
    Base.metadata,
    Column("hardware_id", Integer, ForeignKey("hardware.id"), primary_key=True),
    Column("use_case_id", Integer, ForeignKey("use_cases.id"), primary_key=True),
)

# Association Table for Hardware <-> Software
hardware_software_map = Table(
    "hardware_software_map",
    Base.metadata,
    Column("hardware_id", Integer, ForeignKey("hardware.id"), primary_key=True),
    Column("software_id", Integer, ForeignKey("software.id"), primary_key=True),
)
