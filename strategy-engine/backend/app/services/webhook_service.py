"""
Strategy Engine — Outbound Dispatch Service (Architecture Phase 2)

Upgrades the existing webhook_service.py to the full Phase 2 protocol:

  1. Generates Correlation ID (if not already set)
  2. Generates Idempotency Key (immutable per blueprint approval)
  3. Signs outbound payload with HMAC-SHA256 (X-Signature-256)
  4. Sends blueprint to Production System with correct headers
  5. Parses 202 ACK to extract production_job_id
  6. Returns full DispatchResult for campaign state machine

Error taxonomy:
  - WebhookDispatchError: all retries exhausted (retryable at caller)
  - NonRetryableDispatchError: client error 4xx (stop retrying)
"""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional

import httpx

from app.config import get_settings
from app.models.schemas import ContentBlueprintPayload
from app.services.correlation import (
    generate_correlation_id,
    generate_idempotency_key,
    sign_webhook_payload,
)

logger = logging.getLogger(__name__)


# ============================================================
# Errors
# ============================================================


class WebhookDispatchError(Exception):
    """Raised when dispatch fails after all retries (caller may retry later)."""

    def __init__(self, message: str, status_code: Optional[int] = None, attempts: int = 0):
        self.message = message
        self.status_code = status_code
        self.attempts = attempts
        super().__init__(self.message)


class NonRetryableDispatchError(WebhookDispatchError):
    """Raised on 4xx errors (except 429) — no point retrying."""
    pass


# ============================================================
# Result
# ============================================================


@dataclass
class DispatchResult:
    """
    Returned by WebhookService.dispatch() on success.

    correlation_id and idempotency_key are stored on StrategyCampaign
    immediately before dispatch. production_job_id comes back in the 202 ACK.
    """
    correlation_id: str
    idempotency_key: str
    production_job_id: Optional[str]
    response_code: int
    attempts: int


# ============================================================
# Service
# ============================================================


class WebhookService:
    """
    Dispatches approved blueprints to the Production System.

    Phase 2 additions over the original stub:
      - Embeds correlation_id in payload body + X-Correlation-ID header
      - Embeds idempotency_key in Idempotency-Key header
      - Signs payload with HMAC-SHA256 (X-Signature-256)
      - Parses production_job_id from 202 ACK
    """

    def __init__(self):
        self.settings = get_settings()

    async def dispatch(
        self,
        blueprint: ContentBlueprintPayload,
        *,
        tenant_id: str,
        correlation_id: Optional[str] = None,
        idempotency_key: Optional[str] = None,
        approved_at: Optional[datetime] = None,
    ) -> DispatchResult:
        """
        Send the approved blueprint to the Production System.

        Args:
            blueprint:        The validated ContentBlueprintPayload.
            tenant_id:        Used as prefix in the correlation_id.
            correlation_id:   Pre-generated if retrying an existing campaign.
            idempotency_key:  Pre-generated if retrying an existing campaign.
                              MUST be the same value on every retry attempt.
            approved_at:      Timestamp of human approval (for idempotency key seed).

        Returns:
            DispatchResult with correlation_id, idempotency_key, production_job_id.

        Raises:
            WebhookDispatchError:           All retries exhausted (transient failure).
            NonRetryableDispatchError:      4xx permanent failure.
        """
        url = self.settings.production_webhook_url
        if not url:
            raise WebhookDispatchError("PRODUCTION_WEBHOOK_URL is not configured", attempts=0)

        # ── Generate cross-system identifiers (once, then immutable) ─────
        if not correlation_id:
            correlation_id = generate_correlation_id(
                tenant_id=tenant_id,
                blueprint_id=blueprint.blueprint_id,
            )
        if not idempotency_key:
            _approved_at = approved_at or datetime.now(timezone.utc)
            idempotency_key = generate_idempotency_key(
                blueprint_id=blueprint.blueprint_id,
                tenant_id=tenant_id,
                approved_at=_approved_at,
            )

        # ── Build payload (inject correlation_id into body) ───────────────
        payload_dict = blueprint.model_dump(mode="json")
        payload_dict["correlation_id"] = correlation_id
        payload_dict["idempotency_key"] = idempotency_key

        import json
        raw_body = json.dumps(payload_dict, ensure_ascii=False).encode()

        # ── Build headers ─────────────────────────────────────────────────
        headers: dict[str, str] = {
            "Content-Type": "application/json; charset=utf-8",
            "X-Correlation-ID": correlation_id,
            "Idempotency-Key": idempotency_key,
        }

        if self.settings.production_webhook_token:
            # HMAC-sign the outbound payload
            sig = sign_webhook_payload(raw_body, self.settings.production_webhook_token)
            headers["X-Signature-256"] = sig
            headers["Authorization"] = f"Bearer {self.settings.production_webhook_token}"

        # ── Retry loop with exponential backoff ───────────────────────────
        max_retries = self.settings.webhook_max_retries
        timeout = self.settings.webhook_timeout_seconds
        last_error: Optional[Exception] = None

        for attempt in range(1, max_retries + 1):
            try:
                logger.info(
                    f"[Dispatch] Attempt {attempt}/{max_retries} → {url} "
                    f"(correlation_id={correlation_id})"
                )

                async with httpx.AsyncClient(timeout=timeout) as client:
                    response = await client.post(
                        url,
                        content=raw_body,
                        headers=headers,
                    )

                if response.status_code in (200, 201, 202):
                    # Parse production_job_id from ACK (optional — Production may not return it)
                    production_job_id: Optional[str] = None
                    try:
                        ack_body = response.json()
                        production_job_id = ack_body.get("production_job_id") or ack_body.get("job_id")
                    except Exception:
                        pass

                    logger.info(
                        f"[Dispatch] ✅ Success (status={response.status_code}, "
                        f"job_id={production_job_id}, attempts={attempt})"
                    )
                    return DispatchResult(
                        correlation_id=correlation_id,
                        idempotency_key=idempotency_key,
                        production_job_id=production_job_id,
                        response_code=response.status_code,
                        attempts=attempt,
                    )

                # Non-retryable client error
                if 400 <= response.status_code < 500 and response.status_code != 429:
                    raise NonRetryableDispatchError(
                        f"Client error {response.status_code}: {response.text}",
                        status_code=response.status_code,
                        attempts=attempt,
                    )

                # Retryable server/rate-limit error
                last_error = WebhookDispatchError(
                    f"Retryable error {response.status_code}: {response.text}",
                    status_code=response.status_code,
                )
                logger.warning(f"[Dispatch] Attempt {attempt} → {response.status_code}, retrying…")

            except NonRetryableDispatchError:
                raise  # Never retry 4xx

            except httpx.TimeoutException as e:
                last_error = WebhookDispatchError(f"Timeout after {timeout}s: {e}")
                logger.warning(f"[Dispatch] Attempt {attempt} timed out, retrying…")

            except httpx.ConnectError as e:
                last_error = WebhookDispatchError(f"Connection error: {e}")
                logger.warning(f"[Dispatch] Attempt {attempt} connection failed, retrying…")

            if attempt < max_retries:
                wait = 2 ** (attempt - 1)  # 1s, 2s, 4s…
                logger.info(f"[Dispatch] Waiting {wait}s before retry…")
                await asyncio.sleep(wait)

        logger.error(f"[Dispatch] ❌ All {max_retries} attempts exhausted for {correlation_id}")
        raise WebhookDispatchError(
            f"All {max_retries} attempts exhausted. Last error: {last_error}",
            attempts=max_retries,
        )
