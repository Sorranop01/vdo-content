"""
Strategy Engine — Firestore Client

Initializes the Firestore client using Application Default Credentials (ADC).
On Cloud Run, no credentials file needed — uses the service account attached
to the Cloud Run service (strategy-engine-sa).
For local dev, set GOOGLE_APPLICATION_CREDENTIALS to a service account key file.

Matches the pattern used in the main vdo-content app (src/core/firestore_client.py).
"""

from __future__ import annotations

import logging
import os
from typing import Optional

logger = logging.getLogger(__name__)

# Lazy singleton
_db_client = None


def get_firestore_client():
    """
    Get or initialize the Firestore async client.

    Uses firebase_admin with Application Default Credentials.
    Singleton — safe to call repeatedly.
    """
    global _db_client

    if _db_client is not None:
        return _db_client

    try:
        import firebase_admin
        from firebase_admin import credentials, firestore

        # Check if Firebase app is already initialized
        try:
            firebase_admin.get_app()
        except ValueError:
            project_id = os.getenv("FIREBASE_PROJECT_ID", "vdo-content-4e158")
            cred = credentials.ApplicationDefault()
            firebase_admin.initialize_app(cred, {"projectId": project_id})

        _db_client = firestore.client()
        logger.info(
            f"[Firestore] Client initialized "
            f"(project={os.getenv('FIREBASE_PROJECT_ID', 'vdo-content-4e158')})"
        )
        return _db_client

    except Exception as e:
        logger.error(f"[Firestore] Failed to initialize client: {e}")
        raise


def reset_client():
    """Reset the singleton (used in tests)."""
    global _db_client
    _db_client = None
