"""
Database Engine Configuration
Engine, session factory, Base class, and PortableUUID type.
Supports SQLite (development) and PostgreSQL (production).
"""

import os
import uuid
import logging
from contextlib import contextmanager

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

from sqlalchemy import create_engine, Column, String, Text, Integer, Float, Boolean, DateTime, ForeignKey, JSON, TypeDecorator, CHAR
from sqlalchemy.orm import DeclarativeBase, sessionmaker, relationship
from sqlalchemy import text, inspect

logger = logging.getLogger("vdo_content.database")


# ============ Portable UUID Type ============

class PortableUUID(TypeDecorator):
    """UUID type that works on both PostgreSQL and SQLite.
    Stores as CHAR(36) — compatible with all backends.
    """
    impl = CHAR(36)
    cache_ok = True

    def process_bind_param(self, value, dialect):
        if value is not None:
            s = str(value).strip()
            if not s:  # Empty string → NULL
                return None
            # Validate UUID format before storing
            try:
                uuid.UUID(s)
            except (ValueError, AttributeError):
                logger.warning(f"PortableUUID: invalid UUID '{s[:50]}', storing as NULL")
                return None
            return s
        return value

    def process_result_value(self, value, dialect):
        if value is not None:
            if not isinstance(value, uuid.UUID):
                try:
                    return uuid.UUID(value)
                except (ValueError, AttributeError):
                    return None  # Malformed UUID → None
        return value


# ============ Database URL & Engine ============

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "sqlite:///./vdo_content.db"
)

# Detect backend type
_is_sqlite = DATABASE_URL.startswith("sqlite")
_is_postgres = DATABASE_URL.startswith("postgresql")

# Backend-specific connect_args and pool settings
connect_args = {}
engine_kwargs = {
    "pool_pre_ping": True,    # Check connection health before using
    "echo": False,
}

if _is_sqlite:
    connect_args = {"check_same_thread": False}
    # SQLite: do NOT set pool_size/max_overflow — use default StaticPool-like behavior

elif _is_postgres:
    # PostgreSQL production pool settings
    engine_kwargs["pool_size"] = 5           # Keep 5 connections ready
    engine_kwargs["max_overflow"] = 10       # Allow 10 extra under load
    engine_kwargs["pool_timeout"] = 30       # Wait 30s for a connection
    engine_kwargs["pool_recycle"] = 1800     # Recycle connections every 30min
    logger.info("PostgreSQL backend detected — using connection pooling")

# Create engine
engine = create_engine(
    DATABASE_URL,
    connect_args=connect_args,
    **engine_kwargs,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


@contextmanager
def get_db():
    """Get database session with context manager"""
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


# Database availability flag
DATABASE_AVAILABLE = True
