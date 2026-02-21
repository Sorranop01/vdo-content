# =====================================================
# Strategy Engine Backend — Production Dockerfile
# Optimised for Cloud Run (multi-stage, rootless)
# =====================================================

# Stage 1: Build dependencies
FROM python:3.12-slim AS builder

WORKDIR /build

# Install build deps (needed for asyncpg C extensions)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# Add asyncpg + alembic if not already in requirements.txt
RUN pip install --no-cache-dir --prefix=/install asyncpg aiosqlite alembic


# Stage 2: Runtime image (lean)
FROM python:3.12-slim AS runtime

WORKDIR /app

# Install runtime libs only
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    && rm -rf /var/lib/apt/lists/*

# Copy installed packages from builder
COPY --from=builder /install /usr/local

# Copy application code
COPY app/ ./app/
COPY alembic.ini .

# Non-root user for security
RUN useradd -m -u 1001 appuser && chown -R appuser /app
USER appuser

# Cloud Run injects PORT env var (default 8080)
ENV PORT=8080
EXPOSE 8080

# Startup script: run migrations then start server
COPY --chown=appuser entrypoint.sh .
RUN chmod +x entrypoint.sh

ENTRYPOINT ["./entrypoint.sh"]
