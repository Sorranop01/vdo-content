#!/bin/sh
# ============================================================
# Strategy Engine Backend — Entrypoint
#
# 1. Run Alembic migrations (safe to run on every startup —
#    Alembic is idempotent when already at head)
# 2. Start Uvicorn
# ============================================================

set -e

echo "🔄 Running database migrations..."
python -m alembic upgrade head
echo "✅ Migrations complete"

echo "🚀 Starting server on port ${PORT:-8080}..."
exec uvicorn app.main:app \
    --host 0.0.0.0 \
    --port "${PORT:-8080}" \
    --workers 1 \
    --loop uvloop \
    --http h11 \
    --log-level info \
    --no-access-log
