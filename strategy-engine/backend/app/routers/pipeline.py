"""
Strategy Engine — Pipeline Router

Endpoints for starting, monitoring, and managing agent pipeline runs.
"""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field

from app.models.schemas import (
    ContentBlueprintPayload,
    PipelineState,
    PipelineStatus,
)
from app.agents.graph import run_pipeline
from app.services.webhook_service import WebhookService, WebhookDispatchError

router = APIRouter()
logger = logging.getLogger(__name__)


# ============================================================
# Request / Response Models
# ============================================================


class PipelineStartRequest(BaseModel):
    """Request body when a user starts a new pipeline run."""

    raw_text: str = Field(
        ...,
        min_length=10,
        description="Raw research text (comments, notes, competitor data)",
    )
    model: str = Field(
        default="gpt-4o",
        description="LLM model to use for the pipeline",
    )


class PipelineStartResponse(BaseModel):
    """Response after successfully starting a pipeline."""

    run_id: str
    status: PipelineStatus
    message: str


class PipelineStatusResponse(BaseModel):
    """Current status of a pipeline run."""

    run_id: str
    status: PipelineStatus
    created_at: datetime
    updated_at: Optional[datetime]
    current_stage: str
    error: Optional[str] = None


class DispatchResponse(BaseModel):
    """Response after dispatching a blueprint to production."""

    run_id: str
    status: str
    webhook_result: Optional[dict] = None
    error: Optional[str] = None


# ============================================================
# In-Memory Store (will be replaced with PostgreSQL in Phase 2)
# ============================================================

_pipeline_runs: dict[str, PipelineState] = {}


# ============================================================
# Stage Map
# ============================================================

_STAGE_MAP = {
    PipelineStatus.PENDING: "Queued — waiting to start",
    PipelineStatus.EXTRACTING_INTENT: "Stage 1: Extracting Intent & Persona",
    PipelineStatus.FORMULATING_SEO: "Stage 2: Formulating SEO/GEO Strategy",
    PipelineStatus.CLUSTERING: "Stage 3: Building Topic Clusters",
    PipelineStatus.AWAITING_REVIEW: "Stage 4: Awaiting Human Review ✋",
    PipelineStatus.APPROVED: "Approved — Ready for Dispatch",
    PipelineStatus.DISPATCHING: "Stage 5: Dispatching to Production",
    PipelineStatus.COMPLETED: "✅ Completed",
    PipelineStatus.FAILED: "❌ Failed",
}


# ============================================================
# Background Task: Run Pipeline
# ============================================================


async def _run_pipeline_background(run_id: str, raw_text: str, model: str):
    """Background task that runs the LangGraph agent pipeline."""
    logger.info(f"[BG] Starting pipeline {run_id}...")

    try:
        result = await run_pipeline(
            raw_input=raw_text,
            model=model,
            run_id=run_id,
        )
        _pipeline_runs[run_id] = result
        logger.info(f"[BG] Pipeline {run_id} finished: {result.status.value}")

    except Exception as e:
        logger.error(f"[BG] Pipeline {run_id} crashed: {e}")
        # Update store with error state
        state = _pipeline_runs.get(run_id)
        if state:
            state.status = PipelineStatus.FAILED
            state.error = f"Pipeline crashed: {e}"
            state.updated_at = datetime.utcnow()


# ============================================================
# Endpoints
# ============================================================


@router.post("/start", response_model=PipelineStartResponse)
async def start_pipeline(
    request: PipelineStartRequest,
    background_tasks: BackgroundTasks,
):
    """
    Start a new agent pipeline run.

    Takes raw research text and begins the multi-agent extraction process.
    The pipeline runs asynchronously in the background.
    Poll /api/pipeline/{run_id}/status to check progress.
    """
    import uuid

    run_id = str(uuid.uuid4())

    # Create initial state
    state = PipelineState(
        run_id=run_id,
        raw_input=request.raw_text,
        model_used=request.model,
        status=PipelineStatus.PENDING,
    )
    _pipeline_runs[run_id] = state

    # Start pipeline in background
    background_tasks.add_task(
        _run_pipeline_background,
        run_id=run_id,
        raw_text=request.raw_text,
        model=request.model,
    )

    return PipelineStartResponse(
        run_id=run_id,
        status=PipelineStatus.PENDING,
        message="Pipeline started. Poll /status to track progress.",
    )


@router.get("/{run_id}/status", response_model=PipelineStatusResponse)
async def get_pipeline_status(run_id: str):
    """Get the current status of a pipeline run."""
    state = _pipeline_runs.get(run_id)
    if not state:
        raise HTTPException(status_code=404, detail=f"Pipeline run '{run_id}' not found")

    return PipelineStatusResponse(
        run_id=state.run_id,
        status=state.status,
        created_at=state.created_at,
        updated_at=state.updated_at,
        current_stage=_STAGE_MAP.get(state.status, "Unknown"),
        error=state.error,
    )


@router.get("/{run_id}/blueprint")
async def get_pipeline_blueprint(run_id: str):
    """
    Get the generated blueprint for a pipeline run.

    Only available after the pipeline reaches AWAITING_REVIEW or later.
    Returns the full ContentBlueprintPayload.
    """
    state = _pipeline_runs.get(run_id)
    if not state:
        raise HTTPException(status_code=404, detail=f"Pipeline run '{run_id}' not found")

    if state.blueprint is None:
        raise HTTPException(
            status_code=409,
            detail=f"Blueprint not yet generated. Current status: {state.status.value}",
        )

    return {"run_id": run_id, "status": state.status, "blueprint": state.blueprint}


@router.post("/{run_id}/approve", response_model=DispatchResponse)
async def approve_and_dispatch(run_id: str, approved_by: str = "operator"):
    """
    Approve the blueprint and dispatch to the production system.

    This is the HITL approval step (Stage 4 → Stage 5).
    Triggers the webhook dispatch to the existing vdo-content system.
    """
    state = _pipeline_runs.get(run_id)
    if not state:
        raise HTTPException(status_code=404, detail=f"Pipeline run '{run_id}' not found")

    if state.status != PipelineStatus.AWAITING_REVIEW:
        raise HTTPException(
            status_code=409,
            detail=f"Cannot approve: pipeline is '{state.status.value}', expected 'awaiting_review'",
        )

    if not state.blueprint:
        raise HTTPException(status_code=409, detail="No blueprint available to approve")

    # Mark as approved
    state.status = PipelineStatus.APPROVED
    state.blueprint.approved_by = approved_by
    state.updated_at = datetime.utcnow()

    # Attempt webhook dispatch
    state.status = PipelineStatus.DISPATCHING
    webhook_service = WebhookService()

    try:
        result = await webhook_service.dispatch(state.blueprint)
        state.status = PipelineStatus.COMPLETED
        state.updated_at = datetime.utcnow()
        return DispatchResponse(
            run_id=run_id,
            status="completed",
            webhook_result=result,
        )
    except WebhookDispatchError as e:
        state.status = PipelineStatus.FAILED
        state.error = f"Webhook dispatch failed: {e.message}"
        state.updated_at = datetime.utcnow()
        return DispatchResponse(
            run_id=run_id,
            status="dispatch_failed",
            error=e.message,
        )


@router.get("/", response_model=list[PipelineStatusResponse])
async def list_pipeline_runs():
    """List all pipeline runs (most recent first)."""
    runs = sorted(
        _pipeline_runs.values(),
        key=lambda s: s.created_at,
        reverse=True,
    )
    return [
        PipelineStatusResponse(
            run_id=s.run_id,
            status=s.status,
            created_at=s.created_at,
            updated_at=s.updated_at,
            current_stage=_STAGE_MAP.get(s.status, "Unknown"),
            error=s.error,
        )
        for s in runs
    ]
