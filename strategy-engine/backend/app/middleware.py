"""
Strategy Engine — Production Middleware

Request ID tracing, structured logging, rate limiting, and error handling.
"""

from __future__ import annotations

import logging
import time
import uuid
from collections import defaultdict

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

logger = logging.getLogger(__name__)


# ============================================================
# 1. Request ID Tracing
# ============================================================


class RequestIdMiddleware(BaseHTTPMiddleware):
    """
    Adds a unique X-Request-ID header to every request/response.
    If the client sends one, it's preserved; otherwise a UUID is generated.
    """

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        request.state.request_id = request_id

        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response


# ============================================================
# 2. Request Logging
# ============================================================


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Logs every request with method, path, status, and duration."""

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        start = time.perf_counter()
        request_id = getattr(request.state, "request_id", "unknown")

        response = await call_next(request)

        duration_ms = (time.perf_counter() - start) * 1000
        logger.info(
            f"[{request_id[:8]}] {request.method} {request.url.path} "
            f"→ {response.status_code} ({duration_ms:.0f}ms)"
        )
        return response


# ============================================================
# 3. Rate Limiting (Simple in-memory, per-IP)
# ============================================================


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Simple in-memory rate limiter.
    Limits requests per IP per time window.
    """

    def __init__(
        self,
        app,
        max_requests: int = 60,
        window_seconds: int = 60,
    ):
        super().__init__(app)
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._requests: dict[str, list[float]] = defaultdict(list)

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        # Skip rate limiting for health checks
        if request.url.path in ("/health", "/docs", "/openapi.json"):
            return await call_next(request)

        client_ip = request.client.host if request.client else "unknown"
        now = time.time()

        # Clean old entries
        self._requests[client_ip] = [
            ts for ts in self._requests[client_ip]
            if now - ts < self.window_seconds
        ]

        if len(self._requests[client_ip]) >= self.max_requests:
            return JSONResponse(
                status_code=429,
                content={
                    "error": "Rate limit exceeded",
                    "detail": f"Max {self.max_requests} requests per {self.window_seconds}s",
                    "retry_after": self.window_seconds,
                },
                headers={"Retry-After": str(self.window_seconds)},
            )

        self._requests[client_ip].append(now)
        return await call_next(request)


# ============================================================
# 4. Global Exception Handler
# ============================================================


class ExceptionHandlerMiddleware(BaseHTTPMiddleware):
    """Catches unhandled exceptions and returns a clean JSON error."""

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        try:
            return await call_next(request)
        except Exception as e:
            request_id = getattr(request.state, "request_id", "unknown")
            logger.exception(
                f"[{request_id[:8]}] Unhandled error on {request.method} {request.url.path}: {e}"
            )
            return JSONResponse(
                status_code=500,
                content={
                    "error": "Internal server error",
                    "request_id": request_id,
                    "detail": str(e) if logger.isEnabledFor(logging.DEBUG) else None,
                },
            )
