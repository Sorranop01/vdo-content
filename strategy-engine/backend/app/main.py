"""
Strategy Engine — FastAPI Application Entry Point
"""

from __future__ import annotations

import logging
import sys
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.routers import pipeline, blueprints, content_registry, webhook
from app.middleware import (
    RequestIdMiddleware,
    RequestLoggingMiddleware,
    RateLimitMiddleware,
    ExceptionHandlerMiddleware,
)


# ============================================================
# Structured Logging
# ============================================================

def setup_logging():
    """Configure structured logging for production."""
    settings = get_settings()
    level = logging.DEBUG if settings.debug else logging.INFO

    logging.basicConfig(
        level=level,
        format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        stream=sys.stdout,
        force=True,
    )

    # Quiet noisy libraries
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("openai").setLevel(logging.WARNING)
    logging.getLogger("qdrant_client").setLevel(logging.WARNING)


# ============================================================
# Lifespan
# ============================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown lifecycle."""
    setup_logging()
    logger = logging.getLogger(__name__)

    settings = get_settings()
    logger.info(f"🚀 {settings.app_name} v{settings.app_version} starting...")
    logger.info(f"   LLM Model:  {settings.openai_model}")
    logger.info(f"   Embedding:  {settings.embedding_model}")
    logger.info(f"   Qdrant:     {settings.qdrant_url}")
    logger.info(f"   Webhook:    {settings.production_webhook_url or 'NOT CONFIGURED'}")
    logger.info(f"   CORS:       {settings.cors_origins}")
    logger.info(f"   Rate Limit: 60 req/min per IP")

    # Validate critical config
    if not settings.openai_api_key:
        logger.warning("⚠️  OPENAI_API_KEY not set — LLM calls will fail!")

    yield
    logger.info(f"👋 {settings.app_name} shutting down...")


# ============================================================
# App Factory
# ============================================================

def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    settings = get_settings()

    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description=(
            "AI Content Strategy & Topic Planning Engine. "
            "Multi-agent pipeline for generating SEO/GEO-optimized Content Blueprints."
        ),
        lifespan=lifespan,
    )

    # --- Middleware (order matters: outermost first) ---
    app.add_middleware(ExceptionHandlerMiddleware)
    app.add_middleware(RequestLoggingMiddleware)
    app.add_middleware(RequestIdMiddleware)
    app.add_middleware(
        RateLimitMiddleware,
        max_requests=60,
        window_seconds=60,
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # --- Routers ---
    app.include_router(pipeline.router, prefix="/api/pipeline", tags=["Pipeline"])
    app.include_router(blueprints.router, prefix="/api/blueprints", tags=["Blueprints"])
    app.include_router(content_registry.router, prefix="/api/content", tags=["Content Registry"])
    app.include_router(webhook.router, tags=["Webhook"])  # POST /api/webhook/production-callback

    # --- Health Check (shallow) ---
    @app.get("/health", tags=["System"])
    async def health_check():
        return {
            "status": "healthy",
            "service": settings.app_name,
            "version": settings.app_version,
        }

    # --- Deep Health Check (with dependencies) ---
    @app.get("/health/deep", tags=["System"])
    async def deep_health_check():
        """Check all dependencies: config, Qdrant, LLM key."""
        checks = {
            "api": "ok",
            "openai_key": "configured" if settings.openai_api_key else "MISSING",
            "webhook": "configured" if settings.production_webhook_url else "not_configured",
        }

        # Check Qdrant
        try:
            from app.services.rag_service import get_rag_service
            rag = get_rag_service()
            stats = await rag.get_collection_stats()
            checks["qdrant"] = stats.get("status", "unknown")
            checks["qdrant_points"] = stats.get("points_count", 0)
        except Exception as e:
            checks["qdrant"] = f"error: {e}"

        all_ok = (
            checks["openai_key"] == "configured"
            and checks.get("qdrant") not in (None, "error")
        )

        return {
            "status": "healthy" if all_ok else "degraded",
            "service": settings.app_name,
            "version": settings.app_version,
            "checks": checks,
        }

    return app


app = create_app()
