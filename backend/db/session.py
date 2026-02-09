from sqlalchemy import create_engine
from sqlalchemy.orm import Session
import models

DB_URL ="sqlite://" # Temporary for short-term testing

engine = create_engine(DB_URL, echo=True)

session = Session(engine)

try:
    # Do stuff
    pass
finally:
    session.close()