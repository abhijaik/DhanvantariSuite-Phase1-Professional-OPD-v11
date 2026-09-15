import os
from contextlib import contextmanager
from typing import Generator
from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import sessionmaker, Session
from src.adapters.db.orm_models import Base

# Default is PostgreSQL for both SaaS and Desktop multi-tenant usage.
# (Make sure PostgreSQL is running and update credentials as needed)
DATABASE_URL = os.environ.get("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/clinic_erp")

# Enable SQLite foreign key constraints
@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    if "sqlite" in DATABASE_URL:
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

# Create SQLAlchemy engine
engine = create_engine(
    DATABASE_URL, 
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {}
)

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db() -> None:
    """Create tables and apply small, safe schema upgrades for existing local databases."""
    Base.metadata.create_all(bind=engine)
    # create_all does not add new columns to an existing SQLite table. Apply additive
    # migrations here so users upgrading from an earlier Phase 1 build keep their data.
    if "sqlite" in DATABASE_URL:
        from sqlalchemy import inspect, text
        inspector = inspect(engine)
        columns = {c["name"] for c in inspector.get_columns("appointments")}
        with engine.begin() as conn:
            if "referred_by_type" not in columns:
                conn.execute(text("ALTER TABLE appointments ADD COLUMN referred_by_type VARCHAR(30)"))
            if "referred_by_name" not in columns:
                conn.execute(text("ALTER TABLE appointments ADD COLUMN referred_by_name VARCHAR(120)"))

@contextmanager
def get_db_session() -> Generator[Session, None, None]:
    """Provide a transactional scope around a series of operations."""
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
