
# backend/app/db.py
from contextlib import contextmanager
from typing import Generator
import os
from sqlmodel import Session, create_engine, SQLModel

# ---------------------------------------------------------------------------
# Supabase / PostgreSQL connection
# Set SUPABASE_DB_URL in your environment, e.g.:
#   postgresql://postgres.<ref>:<password>@aws-0-<region>.pooler.supabase.com:6543/postgres
#
# Falls back to SQLite for local-only development when the env var is absent.
# ---------------------------------------------------------------------------
DATABASE_URL = os.getenv("SUPABASE_DB_URL") or os.getenv(
    "DATABASE_URL",
    "sqlite:///./accrue_smart.db",
)

_is_sqlite = DATABASE_URL.startswith("sqlite")

engine = create_engine(
    DATABASE_URL,
    echo=bool(os.getenv("DEBUG")),
    # SQLite needs this; Postgres does not
    connect_args={"check_same_thread": False} if _is_sqlite else {},
    # Postgres pool sizing (ignored by SQLite)
    **({} if _is_sqlite else {"pool_size": 5, "max_overflow": 10}),
)

def init_db():
    """Create tables that are defined as SQLModel classes.
    For Supabase the canonical schema lives in ops/supabase_schema.sql;
    this call is a no-op for tables already created there, but still
    ensures any SQLModel-only tables (e.g. ScheduleLock) exist."""
    SQLModel.metadata.create_all(engine)

@contextmanager
def get_session() -> Generator[Session, None, None]:
    """Context manager for database sessions"""
    session = Session(engine)
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


