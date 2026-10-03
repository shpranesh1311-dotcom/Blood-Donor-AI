"""
database.py
===========
SQLAlchemy engine/session setup. Defaults to SQLite (zero setup) but the
connection string is fully driven by app.config so switching to
PostgreSQL later only requires changing environment variables - no code
changes needed anywhere else in the project.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

from app import config

DATABASE_URL = config.get_database_url()

connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(DATABASE_URL, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    """FastAPI dependency that yields a database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Create all tables. Safe to call multiple times (no-op if tables exist)."""
    from app.models import db_models  # noqa: F401  (ensures models are registered)
    Base.metadata.create_all(bind=engine)
