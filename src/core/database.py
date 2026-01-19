from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.core.config import get_settings

settings = get_settings()

# check_same_thread=False is needed for SQLite when used with FastAPI/multiple threads
engine = create_engine(
    f"sqlite:///{settings.DB_PATH}", 
    connect_args={"check_same_thread": False}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
