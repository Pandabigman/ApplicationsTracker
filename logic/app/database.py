from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from pathlib import Path

# Create a 'data' directory in the logic folder for the SQLite database
db_dir = Path(__file__).parent.parent / "data"
db_dir.mkdir(exist_ok=True)

# SQLite database URL
DATABASE_URL = f"sqlite:///{db_dir / 'jobtracker.db'}"

# Create engine with SQLite-specific settings
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},  # Needed for SQLite with FastAPI
    echo=False  # Set to True for SQL query logging during development
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
