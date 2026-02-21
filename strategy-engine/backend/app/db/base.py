"""
Strategy Engine — SQLAlchemy async engine & session factory.

Uses asyncpg driver via DATABASE_URL (postgresql+asyncpg://...).
Session is injected via FastAPI dependency (get_db).

Engine creation is LAZY (first call to get_db) so test modules can
import this file without requiring asyncpg to be available at import time.
"""

from __future__ import annotations

from typing import AsyncGenerator, Optional

from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.config import get_settings


class Base(DeclarativeBase):
    """Base class for all ORM models."""
    pass


# ── Lazy singletons ───────────────────────────────────────────────────────────
_engine: Optional[AsyncEngine] = None
_session_factory: Optional[async_sessionmaker] = None


def _make_engine() -> AsyncEngine:
    settings = get_settings()
    url = settings.database_url or ""
    # Normalise to asyncpg driver
    if url.startswith("postgresql://"):
        url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
    # Fall back to in-memory SQLite for local dev / CI without PostgreSQL
    if not url or url.startswith("postgresql") and "localhost" not in url and "127.0.0.1" not in url:
        url = url  # keep as-is even for remote URLs
    if not url:
        url = "sqlite+aiosqlite:///./strategy_engine_dev.db"
    return create_async_engine(
        url,
        echo=settings.debug,
        pool_pre_ping=True,
    )


def get_engine() -> AsyncEngine:
    """Return the singleton engine, creating it on first call."""
    global _engine
    if _engine is None:
        _engine = _make_engine()
    return _engine


def get_session_factory() -> async_sessionmaker:
    """Return the singleton session factory, creating it on first call."""
    global _session_factory
    if _session_factory is None:
        _session_factory = async_sessionmaker(
            get_engine(),
            class_=AsyncSession,
            expire_on_commit=False,
        )
    return _session_factory


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency that yields an async database session."""
    factory = get_session_factory()
    async with factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()

