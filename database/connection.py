import os
from sqlalchemy import create_engine, event
from sqlalchemy.orm import declarative_base, sessionmaker
from config.settings import DB_PATH

# Format SQLite local file-system connection string
DATABASE_URL = f"sqlite:///{DB_PATH}"

# Initialize the engine
engine = create_engine(
    DATABASE_URL, 
    connect_args={"check_same_thread": False}  # Safe for async/multithreaded FastAPI tasks
)

# Enforce Foreign Key integrity constraints natively inside SQLite on every connection open
@event.listens_for(engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()

# Session local factory pool
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base model class that all models inherit from
Base = declarative_base()

def get_db():
    """Dependency provider for FastAPI route contexts to handle automatic cleanup."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()