"""
vdo-content — Strategy Engine Integration Router (v2)

Production-grade bridge between Strategy Engine and vdo-content.

Endpoints:
  POST /api/strategy/ingest        — receive approved blueprint → enqueue
  POST /api/strategy/task-worker   — Cloud Tasks worker (internal)
  POST /api/strategy/callback      — status updates from pipeline

Design:
  - Cloud Tasks queue in production (durable, retryable, dead-letter)
  - BackgroundTask in local dev
  - Firestore idempotency (survives restarts, multi-instance safe)
  - Structured JSON logging for Cloud Logging
"""

from __future__ import annotations

import hashlib
import hmac
import json
import logging
import os
import uuid
from datetime import datetime, timezone
from typing import Any, Optional

from fastapi import APIRouter, BackgroundTasks, Header, HTTPException, Request
from pydantic import BaseModel, Field

from src.backend.services.blueprint_queue import get_queue, process_blueprint

logger = logging.getLogger("vdo_content.strategy")

router = APIRouter(prefix="/api/strategy", tags=["Strategy Engine"])


# ============================================================
# Payload Schemas (mirrors strategy-engine's ContentBlueprintPayload)
# No import of strategy-engine code — strict decoupling maintained.
# ============================================================


class SEOMetadataPayload(BaseModel):
    primary_keyword: str
    secondary_keywords: list[str] = []
    long_tail_keywords: list[str] = []
    search_intent: str = ""
    search_volume: Optional[int] = None
    keyword_difficulty: Optional[float] = None


class GEOQueryPayload(BaseModel):
    query_text: str
    constraints: list[str] = []
    mandatory_elements: list[str] = []


class TopicBlueprintPayload(BaseModel):
    topic_id: str
    title: str
    slug: str
    role: str  # "hub" | "spoke"
    content_type: str  # "video" | "short" | "article"
    seo: SEOMetadataPayload
    geo_queries: list[GEOQueryPayload] = []
    hook: str = ""
    key_points: list[str] = []


class ContentBlueprintPayload(BaseModel):
    """Blueprint received from Strategy Engine after human approval."""
    correlation_id: str = Field(description="Strategy Engine correlation ID")
    cluster_primary_keyword: str
    proposed_topics: list[TopicBlueprintPayload]
    estimated_total_search_volume: Optional[int] = None
    seo_mode: str = "seo_primary"
    approved_by: Optional[str] = None
    approved_at: Optional[str] = None
    metadata: dict[str, Any] = {}


class IngestResponse(BaseModel):
    """202 Accepted response returned to Strategy Engine."""
    production_job_id: str
    correlation_id: str
    queue_method: str  # "cloud_tasks" | "background_task" | "synchronous"
    status: str = "queued"
    message: str = "Blueprint received and queued for production pipeline"
    received_at: str


class TaskWorkerPayload(BaseModel):
    """Payload sent by Cloud Tasks to the task-worker endpoint."""
    job_id: str
    idempotency_key: str
    blueprint: dict[str, Any]


# ============================================================
# Security Helpers
# ============================================================


def _get_token() -> str:
    return os.getenv("STRATEGY_ENGINE_TOKEN", "")


def _verify_bearer_token(authorization: Optional[str]) -> bool:
    """Validate the Bearer token from Authorization header."""
    token = _get_token()
    if not token:
        logger.warning(
            json.dumps({"severity": "WARNING", "event": "auth_token_missing",
                        "message": "STRATEGY_ENGINE_TOKEN not set — auth disabled"})
        )
        return True
    if not authorization or not authorization.startswith("Bearer "):
        return False
    return hmac.compare_digest(authorization.removeprefix("Bearer ").strip(), token)


def _verify_hmac(body: bytes, signature_header: Optional[str]) -> bool:
    """Verify HMAC-SHA256 signature in X-Signature-256 header."""
    token = _get_token()
    if not token or not signature_header:
        return True
    try:
        _, sig_hex = signature_header.split("=", 1)
    except ValueError:
        return False
    expected = hmac.new(token.encode(), body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, sig_hex)


# ============================================================
# Endpoint 1: Receive Blueprint
# ============================================================


@router.post(
    "/ingest",
    status_code=202,
    response_model=IngestResponse,
    summary="Receive approved Content Blueprint from Strategy Engine",
)
async def ingest_blueprint(
    request: Request,
    background_tasks: BackgroundTasks,
    authorization: Optional[str] = Header(default=None),
    x_correlation_id: Optional[str] = Header(default=None),
    x_idempotency_key: Optional[str] = Header(default=None),
    x_signature_256: Optional[str] = Header(default=None),
) -> IngestResponse:
    """
    Receive an approved Content Blueprint from the Strategy Engine.

    Production flow:
      validate → idempotency check → enqueue (Cloud Tasks) → 202

    This endpoint returns immediately. The actual blueprint processing
    happens asynchronously via Cloud Tasks (or BackgroundTask in dev).
    """
    # ── Auth ─────────────────────────────────────────────────────────────
    if not _verify_bearer_token(authorization):
        raise HTTPException(status_code=401, detail="Unauthorized — invalid token")

    # ── Body + HMAC ───────────────────────────────────────────────────────
    body = await request.body()
    if not _verify_hmac(body, x_signature_256):
        raise HTTPException(status_code=401, detail="Unauthorized — invalid HMAC signature")

    # ── Parse payload ─────────────────────────────────────────────────────
    try:
        blueprint = ContentBlueprintPayload(**json.loads(body))
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"Invalid blueprint payload: {e}")

    # ── Idempotency check ─────────────────────────────────────────────────
    idem_key = x_idempotency_key or blueprint.correlation_id
    queue = get_queue()

    if queue.is_processed(idem_key):
        logger.info(
            json.dumps({"severity": "INFO", "event": "blueprint_duplicate",
                        "idempotency_key": idem_key, "correlation_id": blueprint.correlation_id})
        )
        return IngestResponse(
            production_job_id=f"dup-{idem_key[:12]}",
            correlation_id=blueprint.correlation_id,
            queue_method="idempotent",
            status="already_processed",
            message="Blueprint already received — idempotency key matched",
            received_at=datetime.now(timezone.utc).isoformat(),
        )

    # ── Generate job ID + enqueue ─────────────────────────────────────────
    job_id = f"pjob-{uuid.uuid4().hex[:12]}"
    blueprint_dict = json.loads(body)  # Raw dict for queue serialization

    queue_method = await queue.enqueue(
        blueprint_dict=blueprint_dict,
        job_id=job_id,
        idempotency_key=idem_key,
        background_tasks=background_tasks,
    )

    logger.info(
        json.dumps({
            "severity": "INFO",
            "event": "blueprint_received",
            "job_id": job_id,
            "correlation_id": blueprint.correlation_id,
            "cluster": blueprint.cluster_primary_keyword,
            "topic_count": len(blueprint.proposed_topics),
            "approved_by": blueprint.approved_by,
            "queue_method": queue_method,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })
    )

    return IngestResponse(
        production_job_id=job_id,
        correlation_id=blueprint.correlation_id,
        queue_method=queue_method,
        status="queued",
        received_at=datetime.now(timezone.utc).isoformat(),
    )


# ============================================================
# Endpoint 2: Cloud Tasks Worker
# Called by Cloud Tasks service to process the blueprint async.
# This is an INTERNAL endpoint — protected by OIDC + Bearer token.
# ============================================================


@router.post(
    "/task-worker",
    status_code=200,
    summary="[Internal] Cloud Tasks worker endpoint",
    include_in_schema=False,  # Hide from public docs
)
async def task_worker(
    request: Request,
    authorization: Optional[str] = Header(default=None),
) -> dict:
    """
    Cloud Tasks HTTP target. Called by GCP Cloud Tasks to process blueprints.
    NOT meant to be called directly.
    """
    if not _verify_bearer_token(authorization):
        raise HTTPException(status_code=401, detail="Unauthorized")

    try:
        payload = TaskWorkerPayload(**await request.json())
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"Invalid task payload: {e}")

    await process_blueprint(
        payload.blueprint,
        payload.job_id,
        payload.idempotency_key,
    )

    # Update Firestore status
    get_queue().idempotency.update_status(
        payload.idempotency_key,
        status="completed",
        completed_at=datetime.now(timezone.utc).isoformat(),
    )

    return {"ok": True, "job_id": payload.job_id}


# ============================================================
# Endpoint 3: Pipeline callback
# ============================================================


@router.post(
    "/callback",
    status_code=200,
    summary="Status update callback from production pipeline",
)
async def production_callback(
    request: Request,
    authorization: Optional[str] = Header(default=None),
) -> dict:
    """
    Called by vdo-content's production pipeline when a job completes/fails.
    Updates the Firestore job record with final status.
    """
    if not _verify_bearer_token(authorization):
        raise HTTPException(status_code=401, detail="Unauthorized")

    body = await request.json()
    job_id = body.get("production_job_id", "unknown")
    idempotency_key = body.get("idempotency_key", job_id)
    status = body.get("status", "unknown")

    get_queue().idempotency.update_status(idempotency_key, status=status, **{
        k: v for k, v in body.items()
        if k not in ("status", "production_job_id", "idempotency_key")
    })

    logger.info(
        json.dumps({"severity": "INFO", "event": "pipeline_callback",
                    "job_id": job_id, "status": status})
    )
    return {"received": True, "job_id": job_id}
