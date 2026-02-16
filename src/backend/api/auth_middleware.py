"""
API Key Authentication Middleware
Protects FastAPI endpoints with X-API-Key header authentication.

When API_SECRET_KEY env var is set:
  - All requests must include X-API-Key header or api_key query param
  - Public paths (/health, /docs, /redoc, /openapi.json) are exempted
  
When API_SECRET_KEY is empty/unset:
  - Auth is disabled (development mode)
"""

import os
import logging
from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger("vdo_content.auth")

# Public paths that skip authentication
PUBLIC_PATHS = {
    "/",
    "/health",
    "/docs",
    "/redoc",
    "/openapi.json",
}


class APIKeyMiddleware(BaseHTTPMiddleware):
    """Middleware that validates API key on protected endpoints."""

    def __init__(self, app, api_key: str = None):
        super().__init__(app)
        self.api_key = api_key or os.getenv("API_SECRET_KEY", "")
        if self.api_key:
            logger.info("API key authentication enabled")
        else:
            logger.info("API key authentication disabled (no API_SECRET_KEY set)")

    async def dispatch(self, request: Request, call_next):
        # Skip auth if no key is configured (dev mode)
        if not self.api_key:
            return await call_next(request)

        # Skip auth for public paths
        path = request.url.path.rstrip("/") or "/"
        if path in PUBLIC_PATHS:
            return await call_next(request)

        # Skip auth for static docs assets (Swagger UI CSS/JS)
        if path.startswith("/docs") or path.startswith("/redoc"):
            return await call_next(request)

        # Check API key from header or query param
        provided_key = (
            request.headers.get("X-API-Key")
            or request.query_params.get("api_key")
        )

        if not provided_key:
            return JSONResponse(
                status_code=401,
                content={
                    "success": False,
                    "error": {
                        "code": "MISSING_API_KEY",
                        "message": "API key required. Pass via X-API-Key header or api_key query parameter.",
                    },
                },
            )

        if provided_key != self.api_key:
            logger.warning(f"Invalid API key attempt from {request.client.host}")
            return JSONResponse(
                status_code=403,
                content={
                    "success": False,
                    "error": {
                        "code": "INVALID_API_KEY",
                        "message": "Invalid API key.",
                    },
                },
            )

        return await call_next(request)
