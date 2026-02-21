"""
Strategy Engine — Firestore Pipeline Run Repository

Replaces the SQLAlchemy CampaignRepository with a simple Firestore-backed store.

Collections:
  strategy_engine_runs/{run_id}   — PipelineState (status, blueprint, etc.)
  strategy_engine_runs/{run_id}/blueprints/{run_id}  — full ContentBlueprintPayload

This uses the SAME Firebase project as vdo-content (vdo-content-4e158).
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Optional

from app.db.firestore_client import get_firestore_client
from app.models.schemas import (
    PipelineState,
    PipelineStatus,
    ContentBlueprintPayload,
    IntentExtractionOutput,
    SEOStrategyOutput,
    ClusterOutput,
)

logger = logging.getLogger(__name__)

# Firestore top-level collection for all pipeline runs
RUNS_COLLECTION = "strategy_engine_runs"


def _serialize_pydantic(obj) -> dict:
    """Serialize a Pydantic model to a plain dict safe for Firestore."""
    if obj is None:
        return None
    if hasattr(obj, "model_dump"):
        return obj.model_dump(mode="json")
    return obj


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class RunRepository:
    """
    Firestore-backed repository for pipeline run state.

    All methods are synchronous (firebase-admin uses sync Firestore client).
    Called from FastAPI background tasks, not from async endpoints directly.
    """

    def __init__(self):
        self.db = get_firestore_client()

    def _ref(self, run_id: str):
        """Return the Firestore document reference for a pipeline run."""
        return self.db.collection(RUNS_COLLECTION).document(run_id)

    def create(self, state: PipelineState) -> None:
        """Persist initial pipeline state to Firestore."""
        doc = {
            "run_id": state.run_id,
            "status": state.status.value,
            "raw_input": state.raw_input,
            "model_used": state.model_used,
            "intent": _serialize_pydantic(state.intent),
            "seo_strategy": _serialize_pydantic(state.seo_strategy),
            "cluster": _serialize_pydantic(state.cluster),
            "blueprint": _serialize_pydantic(state.blueprint),
            "error": state.error,
            "created_at": state.created_at.isoformat() if state.created_at else _now_iso(),
            "updated_at": None,
        }
        self._ref(state.run_id).set(doc)
        logger.info(f"[RunRepo] Created run {state.run_id}")

    def update(self, run_id: str, updates: dict) -> None:
        """Partial update — only provided fields are written."""
        updates["updated_at"] = _now_iso()
        self._ref(run_id).update(updates)
        logger.debug(f"[RunRepo] Updated run {run_id}: {list(updates.keys())}")

    def update_from_state(self, state: PipelineState) -> None:
        """Full overwrite from a PipelineState object."""
        doc = {
            "status": state.status.value,
            "intent": _serialize_pydantic(state.intent),
            "seo_strategy": _serialize_pydantic(state.seo_strategy),
            "cluster": _serialize_pydantic(state.cluster),
            "blueprint": _serialize_pydantic(state.blueprint),
            "error": state.error,
            "updated_at": _now_iso(),
        }
        self._ref(state.run_id).update(doc)
        logger.info(f"[RunRepo] Saved run {state.run_id} → {state.status.value}")

    def get(self, run_id: str) -> Optional[dict]:
        """Fetch a pipeline run document. Returns None if not found."""
        doc = self._ref(run_id).get()
        return doc.to_dict() if doc.exists else None

    def list_recent(self, limit: int = 50) -> list[dict]:
        """List recent pipeline runs ordered by created_at desc."""
        docs = (
            self.db.collection(RUNS_COLLECTION)
            .order_by("created_at", direction="DESCENDING")
            .limit(limit)
            .stream()
        )
        return [d.to_dict() for d in docs]

    def mark_approved(self, run_id: str, approved_by: str) -> None:
        """Mark a run as approved with who approved it."""
        self.update(run_id, {
            "status": PipelineStatus.APPROVED.value,
            "approved_by": approved_by,
            "approved_at": _now_iso(),
        })

    def mark_completed(self, run_id: str, webhook_result: Optional[dict] = None) -> None:
        """Mark a run as completed after successful dispatch."""
        self.update(run_id, {
            "status": PipelineStatus.COMPLETED.value,
            "webhook_result": webhook_result,
            "completed_at": _now_iso(),
        })

    def mark_failed(self, run_id: str, error: str) -> None:
        """Mark a run as failed with an error message."""
        self.update(run_id, {
            "status": PipelineStatus.FAILED.value,
            "error": error,
        })


def get_run_repository() -> RunRepository:
    """FastAPI dependency / direct factory for the run repository."""
    return RunRepository()
