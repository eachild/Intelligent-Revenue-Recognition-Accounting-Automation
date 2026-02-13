# backend/app/db.py
from contextlib import contextmanager
from typing import Generator
import os
from sqlmodel import Session, create_engine, SQLModel
from .services.locks import init_models as init_lock_models

# Database URL from environment or default to SQLite for development
DATABASE_URL = os.getenv(
    "DATABASE_URL", 
    "sqlite:///./accrue_smart.db"
)

# Create engine
engine = create_engine(
    DATABASE_URL,
    echo=True if os.getenv("DEBUG") else False,
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {}
)

def init_db():
    SQLModel.metadata.create_all(engine)
    try:
        init_lock_models()
    except Exception:
        # safe no-op if already initialized
        pass

@contextmanager
def get_session() -> Generator[Session, None, None]:
    """Context manager for database sessions"""
    session = Session(engine)
    try:
        yield session
    finally:
        session.close()