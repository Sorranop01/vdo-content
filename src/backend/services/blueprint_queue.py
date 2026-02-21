"""
vdo-content — Blueprint Queue Service

Production-grade async queue for processing content blueprints received
from the Strategy Engine.

Architecture:
  - Cloud Tasks (GCP) in production → durable, retryable, dead-letter queue
  - In-process BackgroundTasks in local/dev → zero infra needed
  - Firestore for idempotency tracking → survives container restarts

Flow:
  POST /api/strategy/ingest
      │
      ▼
  BlueprintQueueService.enqueue(blueprint, job_id)
      │
      ├─ Production: Cloud Tasks → POST /api/strategy/task-worker
      └─ Local/Dev:  FastAPI BackgroundTask → process_blueprint()

  task-worker endpoint receives the Cloud Tasks HTTP request and calls
  process_blueprint() — same function as local dev.
"""

from __future__ import annotations

import json
import logging
import os
from datetime import datetime, timezone
from typing import Any, Optional

logger = logging.getLogger("vdo_content.blueprint_queue")

# ── Optional Cloud Tasks import (graceful if not installed) ──────────────────
try:
    from google.cloud import tasks_v2
    from google.protobuf import duration_pb2
    CLOUD_TASKS_AVAILABLE = True
except ImportError:
    CLOUD_TASKS_AVAILABLE = False
    logger.info("[Queue] google-cloud-tasks not installed — will use local fallback")

# ── Optional Firestore import ─────────────────────────────────────────────────
try:
    import firebase_admin
    from firebase_admin import firestore
    FIRESTORE_AVAILABLE = True
except ImportError:
    FIRESTORE_AVAILABLE = False


# ============================================================
# Configuration (from env vars)
# ============================================================

def _get_config() -> dict:
    return {
        "project_id": os.getenv("GCP_PROJECT_ID", "ecol-b0859"),
        "region": os.getenv("CLOUD_TASKS_REGION", "asia-southeast1"),
        "queue_name": os.getenv("CLOUD_TASKS_QUEUE", "blueprint-processing"),
        "worker_url": os.getenv(
            "CLOUD_TASKS_WORKER_URL",
            "https://vdo-content-1040928076984.asia-southeast1.run.app/api/strategy/task-worker",
        ),
        "service_account": os.getenv(
            "CLOUD_TASKS_SA",
            "1040928076984-compute@developer.gserviceaccount.com",
        ),
        "strategy_token": os.getenv("STRATEGY_ENGINE_TOKEN", ""),
        "firestore_collection": os.getenv("IDEMPOTENCY_COLLECTION", "blueprint_jobs"),
    }


# ============================================================
# Firestore Idempotency Store
# ============================================================

class FirestoreIdempotencyStore:
    """
    Persistent idempotency store backed by Firestore.
    Survives Cloud Run restarts and scales across multiple instances.
    """

    def __init__(self, collection: str = "blueprint_jobs"):
        self._collection = collection
        self._db = None

    def _get_db(self):
        """Lazy-init Firestore client (reuses firebase_admin from the main app)."""
        if self._db is None:
            try:
                self._db = firestore.client()
            except Exception as e:
                logger.warning(f"[Queue] Firestore not available: {e}")
        return self._db

    def is_processed(self, idempotency_key: str) -> bool:
        """Return True if this key was already processed."""
        db = self._get_db()
        if db is None:
            return False  # Fallback: treat as new (safe — Cloud Tasks handles deduplciation)
        try:
            doc = db.collection(self._collection).document(idempotency_key).get()
            return doc.exists
        except Exception as e:
            logger.warning(f"[Queue] Firestore read failed: {e} — allowing through")
            return False

    def mark_processed(self, idempotency_key: str, job_id: str, blueprint_summary: dict) -> None:
        """Mark an idempotency key as processed."""
        db = self._get_db()
        if db is None:
            return
        try:
            db.collection(self._collection).document(idempotency_key).set({
                "job_id": job_id,
                "processed_at": datetime.now(timezone.utc).isoformat(),
                "cluster_keyword": blueprint_summary.get("cluster_primary_keyword", ""),
                "topic_count": blueprint_summary.get("topic_count", 0),
                "approved_by": blueprint_summary.get("approved_by", ""),
                "status": "queued",
            })
        except Exception as e:
            logger.warning(f"[Queue] Firestore write failed: {e}")

    def update_status(self, idempotency_key: str, status: str, **extra) -> None:
        """Update job status (called by task worker on completion/failure)."""
        db = self._get_db()
        if db is None:
            return
        try:
            update = {"status": status, "updated_at": datetime.now(timezone.utc).isoformat()}
            update.update(extra)
            db.collection(self._collection).document(idempotency_key).update(update)
        except Exception as e:
            logger.warning(f"[Queue] Firestore status update failed: {e}")


# ============================================================
# Local In-Memory Fallback (development only)
# ============================================================

class InMemoryIdempotencyStore:
    """
    In-memory fallback for local development.
    NOT safe for production (lost on restart).
    """

    def __init__(self):
        self._keys: dict[str, dict] = {}

    def is_processed(self, key: str) -> bool:
        return key in self._keys

    def mark_processed(self, key: str, job_id: str, blueprint_summary: dict) -> None:
        self._keys[key] = {"job_id": job_id, **blueprint_summary}

    def update_status(self, key: str, status: str, **extra) -> None:
        if key in self._keys:
            self._keys[key]["status"] = status


# ============================================================
# Blueprint Queue Service
# ============================================================

class BlueprintQueueService:
    """
    Enqueues approved content blueprints for async processing.
    Uses Cloud Tasks in production, BackgroundTasks in local dev.
    """

    def __init__(self):
        cfg = _get_config()
        self._cfg = cfg
        # Choose idempotency backend
        if FIRESTORE_AVAILABLE:
            self.idempotency = FirestoreIdempotencyStore(cfg["firestore_collection"])
            logger.info("[Queue] Using Firestore-backed idempotency store")
        else:
            self.idempotency = InMemoryIdempotencyStore()
            logger.warning("[Queue] Using in-memory idempotency (local dev only)")

    def is_processed(self, idempotency_key: str) -> bool:
        return self.idempotency.is_processed(idempotency_key)

    def mark_processed(self, idempotency_key: str, job_id: str, blueprint_summary: dict) -> None:
        self.idempotency.mark_processed(idempotency_key, job_id, blueprint_summary)

    async def enqueue(
        self,
        blueprint_dict: dict,
        job_id: str,
        idempotency_key: str,
        background_tasks=None,
    ) -> str:
        """
        Queue the blueprint for async processing.

        Returns the queue method used: 'cloud_tasks' | 'background_task'
        """
        # Mark as processed before enqueuing (prevents duplicate tasks
        # even if we crash mid-enqueue)
        self.mark_processed(
            idempotency_key,
            job_id,
            {
                "cluster_primary_keyword": blueprint_dict.get("cluster_primary_keyword", ""),
                "topic_count": len(blueprint_dict.get("proposed_topics", [])),
                "approved_by": blueprint_dict.get("approved_by", ""),
            },
        )

        if CLOUD_TASKS_AVAILABLE and self._use_cloud_tasks():
            await self._enqueue_cloud_tasks(blueprint_dict, job_id, idempotency_key)
            return "cloud_tasks"
        elif background_tasks is not None:
            background_tasks.add_task(process_blueprint, blueprint_dict, job_id, idempotency_key)
            return "background_task"
        else:
            # Synchronous fallback (tests)
            await process_blueprint(blueprint_dict, job_id, idempotency_key)
            return "synchronous"

    def _use_cloud_tasks(self) -> bool:
        """True if Cloud Tasks should be used (production = PROJECT_ID is set and not local)."""
        project = self._cfg["project_id"]
        worker_url = self._cfg["worker_url"]
        return bool(project and "localhost" not in worker_url and "127.0.0.1" not in worker_url)

    async def _enqueue_cloud_tasks(
        self,
        blueprint_dict: dict,
        job_id: str,
        idempotency_key: str,
    ) -> None:
        """Create a Cloud Tasks HTTP task targeting our task-worker endpoint."""
        cfg = self._cfg
        client = tasks_v2.CloudTasksAsyncClient()
        parent = client.queue_path(cfg["project_id"], cfg["region"], cfg["queue_name"])

        payload = json.dumps({
            "job_id": job_id,
            "idempotency_key": idempotency_key,
            "blueprint": blueprint_dict,
        }).encode()

        headers = {"Content-Type": "application/json"}
        if cfg["strategy_token"]:
            headers["Authorization"] = f"Bearer {cfg['strategy_token']}"

        task = {
            "http_request": {
                "http_method": tasks_v2.HttpMethod.POST,
                "url": cfg["worker_url"],
                "headers": headers,
                "body": payload,
                "oidc_token": {
                    "service_account_email": cfg["service_account"],
                    "audience": cfg["worker_url"],
                },
            }
        }

        response = await client.create_task(parent=parent, task=task)
        logger.info(f"[Queue] Cloud Task created: {response.name} | job_id={job_id}")


# ============================================================
# Blueprint Processor (the actual work)
# ============================================================

async def process_blueprint(
    blueprint_dict: dict,
    job_id: str,
    idempotency_key: str,
) -> None:
    """
    Process an approved Content Blueprint from the Strategy Engine.

    This function is called by:
    - Cloud Tasks HTTP worker in production
    - FastAPI BackgroundTask in local dev
    - Directly (sync) in tests

    Current implementation: structured log (ready for production pipeline).
    Replace the TODO section with actual video/script generation logic.
    """
    cluster = blueprint_dict.get("cluster_primary_keyword", "unknown")
    topics = blueprint_dict.get("proposed_topics", [])
    approved_by = blueprint_dict.get("approved_by", "system")

    logger.info(
        json.dumps({
            "severity": "INFO",
            "event": "blueprint_processing_started",
            "job_id": job_id,
            "correlation_id": blueprint_dict.get("correlation_id", ""),
            "cluster": cluster,
            "topic_count": len(topics),
            "approved_by": approved_by,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })
    )

    try:
        # ── TODO: Wire to actual production pipeline ────────────────────────
        # 1. Create a Project in vdo-content for each topic
        # 2. Generate scripts via ScriptGenerator
        # 3. Generate video prompts via VeoPromptGenerator
        # 4. Queue for video generation
        # Example:
        #   for topic in topics:
        #       project_id = await create_project_from_topic(topic, cluster)
        #       await schedule_script_generation(project_id)
        # ───────────────────────────────────────────────────────────────────

        logger.info(
            json.dumps({
                "severity": "INFO",
                "event": "blueprint_processing_complete",
                "job_id": job_id,
                "cluster": cluster,
                "topics_queued": [t.get("title", "") for t in topics],
                "timestamp": datetime.now(timezone.utc).isoformat(),
            })
        )

    except Exception as e:
        logger.error(
            json.dumps({
                "severity": "ERROR",
                "event": "blueprint_processing_failed",
                "job_id": job_id,
                "error": str(e),
                "timestamp": datetime.now(timezone.utc).isoformat(),
            })
        )
        raise


# ============================================================
# Singleton
# ============================================================

_queue: Optional[BlueprintQueueService] = None


def get_queue() -> BlueprintQueueService:
    """Return the queue service singleton."""
    global _queue
    if _queue is None:
        _queue = BlueprintQueueService()
    return _queue
