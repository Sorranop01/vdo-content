"""
Strategy Engine — Correlation ID & Idempotency Service

Implements the cross-system tracking protocol from Architecture Phase 2:

  - Correlation ID:  SE-{tenant_prefix}-{blueprint_prefix}-{unix_ts}
  - Idempotency Key: SHA256("{blueprint_id}:{tenant_id}:{approved_at_unix}")
  - Webhook HMAC:    SHA256-HMAC over raw request body with SHARED_WEBHOOK_SECRET
"""

from __future__ import annotations

import hashlib
import hmac
import time
from datetime import datetime, timezone


def generate_correlation_id(tenant_id: str, blueprint_id: str) -> str:
    """
    Generate a cross-system Correlation ID.

    Format: SE-{tenant_8chars}-{blueprint_8chars}-{unix_ts}
    Example: SE-eco-corp1-a1b2c3d4-1740139723

    The Production System MUST store this and echo it back in every
    Webhook callback. The Strategy Engine uses it to look up the campaign.
    """
    tenant_prefix = tenant_id[:8].replace("-", "")[:8]
    blueprint_prefix = blueprint_id[:8].replace("-", "")[:8]
    ts = int(time.time())
    return f"SE-{tenant_prefix}-{blueprint_prefix}-{ts}"


def generate_idempotency_key(
    blueprint_id: str,
    tenant_id: str,
    approved_at: datetime,
) -> str:
    """
    Generate an idempotency key for the Production System dispatch.

    Format: SHA256("{blueprint_id}:{tenant_id}:{approved_at_unix}")
    This key is IMMUTABLE — the same key is reused on every retry for the
    same approved blueprint. The Production System deduplicates on this.
    """
    approved_ts = int(approved_at.replace(tzinfo=timezone.utc).timestamp()
                      if approved_at.tzinfo is None else approved_at.timestamp())
    raw = f"{blueprint_id}:{tenant_id}:{approved_ts}"
    return hashlib.sha256(raw.encode()).hexdigest()


def sign_webhook_payload(raw_body: bytes, secret: str) -> str:
    """
    Sign a raw request body for Webhook authentication.

    Returns the HMAC-SHA256 hex digest. The Strategy Engine sends this
    in the `X-Signature-256` header when calling back to the Production System.
    The Production System validates it before accepting any payload.
    """
    return hmac.new(
        secret.encode(),
        raw_body,
        hashlib.sha256,
    ).hexdigest()


def verify_webhook_signature(raw_body: bytes, secret: str, received_sig: str) -> bool:
    """
    Verify a Webhook callback signature from the Production System.

    The Production System signs its callbacks with the shared secret.
    The Strategy Engine calls this before processing any /webhook/production-callback.

    Uses constant-time comparison to prevent timing attacks.
    """
    expected = sign_webhook_payload(raw_body, secret)
    return hmac.compare_digest(expected, received_sig)
