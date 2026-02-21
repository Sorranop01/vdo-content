"""
Strategy Engine — Campaign Repository

Data access layer for StrategyCampaign, covering:
  - Campaign creation (from a blueprint)
  - State machine transitions (with validation)
  - Correlation ID and production_job_id tracking
  - Status queries for the pipeline API
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.models import (
    ContentNode,
    ExtractedIntent,
    InternalLink,
    StrategyCampaign,
    TopicCluster,
    UserResearchInput,
)
from app.models.schemas import ContentBlueprintPayload

logger = logging.getLogger(__name__)

# Valid state machine transitions (Architecture Phase 2)
VALID_TRANSITIONS: dict[str, list[str]] = {
    "DRAFT_GENERATING":         ["PENDING_HUMAN_APPROVAL", "REJECTED", "FAILED"],
    "PENDING_HUMAN_APPROVAL":   ["APPROVED", "FAILED"],
    "APPROVED":                 ["DISPATCHING_TO_API"],
    "DISPATCHING_TO_API":       ["PRODUCTION_PROCESSING", "APPROVED", "DISPATCH_FAILED"],
    "PRODUCTION_PROCESSING":    ["COMPLETED", "PRODUCTION_FAILED"],
    "DISPATCH_FAILED":          ["APPROVED"],    # Manual operator retry
    "PRODUCTION_FAILED":        ["APPROVED"],    # Manual operator retry
    # Terminal states — no further transitions
    "COMPLETED":                [],
    "FAILED":                   [],
    "REJECTED":                 [],
}


class InvalidTransitionError(Exception):
    def __init__(self, current: str, target: str):
        super().__init__(f"Invalid transition {current!r} → {target!r}")
        self.current = current
        self.target = target


class CampaignRepository:
    """
    Repository for StrategyCampaign — the aggregate root of the state machine.
    All state transitions are validated before writing to prevent illegal states.
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    # ── Create ─────────────────────────────────────────────────────────────

    async def create_from_blueprint(
        self,
        blueprint: ContentBlueprintPayload,
        tenant_id: str,
        run_id: str,
        model_used: str = "deepseek-chat",
        raw_text: Optional[str] = None,
    ) -> StrategyCampaign:
        """
        Persist a completed blueprint as a StrategyCampaign with all child entities.
        Sets status = PENDING_HUMAN_APPROVAL (pipeline has completed, awaiting review).
        """
        # 1. Optionally store raw input
        research_input = None
        if raw_text:
            research_input = UserResearchInput(
                tenant_id=tenant_id,
                raw_text=raw_text,
                char_count=len(raw_text),
                passed_guard=True,  # Only stored if EC1 passed
                source_type="manual",
            )
            self.db.add(research_input)
            await self.db.flush()

        # 2. Create campaign
        campaign = StrategyCampaign(
            id=run_id,
            tenant_id=tenant_id,
            research_input_id=research_input.id if research_input else None,
            status="PENDING_HUMAN_APPROVAL",
            seo_mode=getattr(blueprint, "seo_mode", "full_seo_geo"),
            seo_mode_reason=getattr(blueprint, "seo_mode_reason", None),
            cluster_primary_keyword=blueprint.cluster_primary_keyword,
            estimated_search_volume=blueprint.estimated_total_search_volume,
            cannibalization_checked=blueprint.cannibalization_checked,
            model_used=model_used,
        )
        self.db.add(campaign)
        await self.db.flush()

        # 3. Persist ExtractedIntent
        intent = ExtractedIntent(
            campaign_id=campaign.id,
            research_input_id=research_input.id if research_input else None,
            target_persona=blueprint.target_persona,
            core_pain_points=blueprint.core_pain_points,
            underlying_emotions=blueprint.underlying_emotions,
            raw_input_snippet=blueprint.raw_input_snippet,
            model_used=model_used,
        )
        self.db.add(intent)

        # 4. Persist TopicCluster
        cluster = TopicCluster(
            campaign_id=campaign.id,
            cluster_name=blueprint.hub.title,
            cluster_slug=blueprint.hub.slug,
            primary_keyword=blueprint.cluster_primary_keyword,
            total_search_volume=blueprint.estimated_total_search_volume,
            node_count=1 + len(blueprint.spokes),
        )
        self.db.add(cluster)
        await self.db.flush()

        # 5. Persist ContentNodes (hub + spokes)
        node_id_map: dict[str, str] = {}  # topic_id → ContentNode.id

        for topic in [blueprint.hub] + list(blueprint.spokes):
            node = ContentNode(
                cluster_id=cluster.id,
                campaign_id=campaign.id,
                topic_id=topic.topic_id,
                role=topic.role.value if hasattr(topic.role, "value") else topic.role,
                content_type=topic.content_type.value if hasattr(topic.content_type, "value") else topic.content_type,
                title=topic.title,
                slug=topic.slug,
                hook=topic.hook,
                key_points=topic.key_points,
                target_duration_s=topic.target_duration_seconds,
                tone=topic.tone.value if hasattr(topic.tone, "value") else topic.tone,
                cta=topic.cta,
                primary_keyword=topic.seo.primary_keyword,
                secondary_keywords=topic.seo.secondary_keywords,
                long_tail_keywords=topic.seo.long_tail_keywords,
                search_volume=topic.seo.search_volume,
                search_volume_verified=False,
                keyword_difficulty=topic.seo.keyword_difficulty,
                search_intent=topic.seo.search_intent.value if hasattr(topic.seo.search_intent, "value") else topic.seo.search_intent,
                seo_mode=getattr(blueprint, "seo_mode", "full_seo_geo"),
                geo_queries=[q.model_dump() for q in topic.geo_queries],
            )
            self.db.add(node)
            await self.db.flush()
            node_id_map[topic.topic_id] = node.id

        # 6. Persist InternalLinks
        for link in blueprint.internal_links:
            from_id = node_id_map.get(link.from_topic_id)
            to_id = node_id_map.get(link.to_topic_id)
            if from_id and to_id:
                self.db.add(InternalLink(
                    campaign_id=campaign.id,
                    from_node_id=from_id,
                    to_node_id=to_id,
                    anchor_text=link.anchor_text,
                    link_type=link.link_type,
                    existing_url=link.existing_url,
                ))

        logger.info(
            f"[CampaignRepo] Created campaign {campaign.id} with "
            f"{1 + len(blueprint.spokes)} nodes and {len(blueprint.internal_links)} links"
        )
        return campaign

    # ── State Transitions ───────────────────────────────────────────────────

    async def transition(
        self,
        campaign_id: str,
        target_status: str,
        *,
        approved_by: Optional[str] = None,
        correlation_id: Optional[str] = None,
        idempotency_key: Optional[str] = None,
        production_job_id: Optional[str] = None,
        dispatch_error: Optional[str] = None,
    ) -> StrategyCampaign:
        """
        Apply a validated state machine transition.
        Raises InvalidTransitionError if the transition is not allowed.
        """
        campaign = await self.get_by_id(campaign_id)
        if not campaign:
            raise ValueError(f"Campaign not found: {campaign_id}")

        allowed = VALID_TRANSITIONS.get(campaign.status, [])
        if target_status not in allowed:
            raise InvalidTransitionError(campaign.status, target_status)

        now = datetime.now(timezone.utc)
        campaign.status = target_status
        campaign.updated_at = now

        # Status-specific field updates
        if target_status == "APPROVED":
            campaign.approved_by = approved_by
            campaign.approved_at = now

        elif target_status == "DISPATCHING_TO_API":
            campaign.correlation_id = correlation_id or campaign.correlation_id
            campaign.idempotency_key = idempotency_key or campaign.idempotency_key
            campaign.dispatch_attempts = (campaign.dispatch_attempts or 0) + 1
            campaign.dispatched_at = now

        elif target_status == "PRODUCTION_PROCESSING":
            campaign.production_job_id = production_job_id

        elif target_status in ("DISPATCH_FAILED", "PRODUCTION_FAILED", "FAILED"):
            campaign.dispatch_error = dispatch_error

        elif target_status == "COMPLETED":
            campaign.completed_at = now

        self.db.add(campaign)
        logger.info(
            f"[CampaignRepo] Campaign {campaign_id}: {campaign.status} → {target_status}"
        )
        return campaign

    # ── Queries ─────────────────────────────────────────────────────────────

    async def get_by_id(self, campaign_id: str) -> Optional[StrategyCampaign]:
        result = await self.db.execute(
            select(StrategyCampaign).where(StrategyCampaign.id == campaign_id)
        )
        return result.scalar_one_or_none()

    async def get_by_correlation_id(self, correlation_id: str) -> Optional[StrategyCampaign]:
        result = await self.db.execute(
            select(StrategyCampaign).where(StrategyCampaign.correlation_id == correlation_id)
        )
        return result.scalar_one_or_none()

    async def list_for_tenant(
        self,
        tenant_id: str,
        limit: int = 50,
        offset: int = 0,
    ) -> list[StrategyCampaign]:
        result = await self.db.execute(
            select(StrategyCampaign)
            .where(StrategyCampaign.tenant_id == tenant_id)
            .order_by(StrategyCampaign.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return list(result.scalars().all())

    async def get_stuck_in_processing(
        self,
        hours: int = 24,
    ) -> list[StrategyCampaign]:
        """
        Find campaigns stuck in PRODUCTION_PROCESSING for longer than `hours`.
        Used by the TTL watchdog cron job.
        """
        from datetime import timedelta
        cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
        result = await self.db.execute(
            select(StrategyCampaign).where(
                StrategyCampaign.status == "PRODUCTION_PROCESSING",
                StrategyCampaign.dispatched_at < cutoff,
            )
        )
        return list(result.scalars().all())
