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
# Topic → Project converter
# ============================================================

async def _create_project_from_topic(
    topic: dict,
    cluster_keyword: str,
    job_id: str,
    approved_by: str,
) -> str:
    """
    Create a vdo-content Project from a strategy-engine TopicBlueprint.

    Mapping:
        topic.title             → project.title
        topic.hook              → used as opening line in description
        topic.key_points        → project.description (bullet list)
        topic.seo.primary_keyword → project.topic
        topic.seo.secondary_keywords → appended to description
        topic.content_type      → project.video_format + target_duration
        cluster_keyword         → project.content_goal

    Returns the new project_id.
    """
    from src.core.models import Project
    from src.core.database import db_save_project

    title = topic.get("title", "Untitled Topic")
    hook = topic.get("hook", "")
    key_points: list = topic.get("key_points", [])
    content_type: str = topic.get("content_type", "video")  # video | short | article

    seo: dict = topic.get("seo", {})
    primary_kw = seo.get("primary_keyword", cluster_keyword)
    secondary_kws: list = seo.get("secondary_keywords", [])
    long_tail_kws: list = seo.get("long_tail_keywords", [])

    # Map content_type to video format and duration
    format_map = {
        "short": ("shorts", 60),
        "video": ("standard", 300),
        "article": ("standard", 180),
    }
    video_format, target_duration = format_map.get(content_type, ("standard", 180))

    # Build description from blueprint data
    desc_lines = []
    if hook:
        desc_lines.append(f"🎯 Hook: {hook}")
    if key_points:
        kp_text = "\n".join(f"• {kp}" for kp in key_points)
        desc_lines.append(f"Key Points:\n{kp_text}")
    if secondary_kws:
        desc_lines.append(f"SEO Keywords: {', '.join(secondary_kws)}")
    if long_tail_kws:
        desc_lines.append(f"Long-tail: {', '.join(long_tail_kws)}")
    desc_lines.append(f"\n[Auto-created by Strategy Engine | job={job_id} | approved_by={approved_by}]")
    description = "\n\n".join(desc_lines)

    project = Project(
        title=title,
        topic=primary_kw,
        description=description,
        content_goal=cluster_keyword,
        video_format=video_format,
        target_duration=target_duration,
        platforms=["youtube"],  # Default; user can update later in Step 2
        status="step1_project",
        workflow_step=0,
    )

    project_data = project.model_dump(mode="json")
    project_id = await _save_project_async(project_data)
    return project_id


async def _save_project_async(project_data: dict) -> str:
    """
    Async-compatible wrapper around the synchronous Firestore save.
    Runs in a thread pool to avoid blocking the event loop.
    """
    import asyncio
    from functools import partial
    from src.core.database import db_save_project

    loop = asyncio.get_event_loop()
    project_id = await loop.run_in_executor(None, partial(db_save_project, project_data))
    return project_id


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

    For each topic in the blueprint:
      1. Creates a vdo-content Project in Firestore via _create_project_from_topic()
      2. (Future) Triggers script generation automatically

    Called by:
    - Cloud Tasks HTTP worker in production
    - FastAPI BackgroundTask in local dev
    - Directly (sync) in tests
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
        # ── Wire to actual production pipeline ────────────────────────────
        # For each topic in the blueprint:
        #   1. Create a vdo-content Project in Firestore
        #   2. Trigger script generation via ScriptGenerator
        # Video prompt generation happens in Step 4 (user-driven in the UI)
        # ─────────────────────────────────────────────────────────────────

        created_projects: list[dict] = []
        failed_topics: list[dict] = []

        for topic in topics:
            topic_title = topic.get("title", "Untitled")
            topic_id = topic.get("topic_id", "")
            try:
                project_id = await _create_project_from_topic(
                    topic=topic,
                    cluster_keyword=cluster,
                    job_id=job_id,
                    approved_by=approved_by,
                )
                created_projects.append({"topic_title": topic_title, "project_id": project_id})
                logger.info(
                    json.dumps({
                        "severity": "INFO",
                        "event": "topic_project_created",
                        "job_id": job_id,
                        "topic_id": topic_id,
                        "topic_title": topic_title,
                        "project_id": project_id,
                    })
                )
            except Exception as topic_err:
                failed_topics.append({"topic_title": topic_title, "error": str(topic_err)})
                logger.error(
                    json.dumps({
                        "severity": "ERROR",
                        "event": "topic_project_failed",
                        "job_id": job_id,
                        "topic_id": topic_id,
                        "topic_title": topic_title,
                        "error": str(topic_err),
                    })
                )

        logger.info(
            json.dumps({
                "severity": "INFO",
                "event": "blueprint_processing_complete",
                "job_id": job_id,
                "cluster": cluster,
                "topics_total": len(topics),
                "topics_created": len(created_projects),
                "topics_failed": len(failed_topics),
                "projects": created_projects,
                "failures": failed_topics,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            })
        )

        # Raise if every topic failed (so caller can retry the whole blueprint)
        if topics and len(failed_topics) == len(topics):
            raise RuntimeError(
                f"All {len(topics)} topic(s) failed to create projects. "
                f"First error: {failed_topics[0]['error']}"
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
