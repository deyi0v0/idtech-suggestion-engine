import os
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
import models

DB_URL = os.environ.get("DATABASE_URL", "postgresql://admin:ics1802026@db:5432/product_db") # Using environment variable with PostgreSQL fallback

engine = create_engine(DB_URL, echo=True)

session = Session(engine)

try:
    # Do stuff
    pass
finally:
    session.close()

# Reverting this specific change, as it overcomplicates the capture.
# Instead, we'll modify init_db.py to explicitly print the DDL.