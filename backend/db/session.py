import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from typing import Generator

DB_URL = os.environ.get("DATABASE_URL", "postgresql://admin:ics1802026@localhost:5432/product_db")

engine = create_engine(DB_URL, echo=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db() -> Generator[Session, None, None]:
    """
    Dependency for FastAPI to provide a database session for each request.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
