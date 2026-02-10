from session import engine
from base import Base

if __name__ == "__main__":
    Base.metadata.create_all(bind=engine)
    print("Database tables created")