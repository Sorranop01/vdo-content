"""
Alembic environment configuration for the Strategy Engine.

Reads DATABASE_URL from the application settings so that migrations
use the same connection as the running application.

Supports both:
  - `alembic upgrade head`            (synchronous, used in CI)
  - Async engine for runtime autogenerate
"""

from __future__ import annotations

import asyncio
from logging.config import fileConfig

from alembic import context
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

# Import the Base and all models to populate metadata for autogenerate
from app.db.base import Base
from app.db import models as _models  # noqa: F401 — ensure models are registered
from app.config import get_settings

# ── Alembic Config ──────────────────────────────────────────────────────────
config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def get_url() -> str:
    settings = get_settings()
    url = settings.database_url
    # Ensure asyncpg driver for async migrations
    if url and url.startswith("postgresql://"):
        url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
    return url or "postgresql+asyncpg://strategy:strategy@localhost:5432/strategy_engine"


# ── Offline mode (generates SQL script without DB connection) ───────────────
def run_migrations_offline() -> None:
    url = get_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()


# ── Online mode (connects to DB and applies migrations) ────────────────────
def do_run_migrations(connection: Connection) -> None:
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """Run migrations using the async SQLAlchemy engine."""
    connectable = async_engine_from_config(
        {"sqlalchemy.url": get_url()},
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await connectable.dispose()


def run_migrations_online() -> None:
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
