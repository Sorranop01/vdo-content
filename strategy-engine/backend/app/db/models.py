"""
Strategy Engine — SQLAlchemy ORM Models (Architecture Phase 2)

Implements the 5-entity ERD from the approved architecture document:

  1. UserResearchInput  — raw scraped text pasted by the user
  2. ExtractedIntent    — Agent 1 output (persona, pain points, emotions)
  3. StrategyCampaign   — aggregate root / state machine owner
  4. TopicCluster       — Hub + Spoke grouping (Agent 3 output)
  5. ContentNode        — Individual article/video with SEO/GEO metadata

Plus:
  6. InternalLink       — N:M join table for inter-node links

Storage: PostgreSQL (private to Strategy Engine — NOT shared with Production System).
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


def _uuid() -> str:
    return str(uuid.uuid4())


def _now() -> datetime:
    return datetime.now(timezone.utc)


# ============================================================
# 1. UserResearchInput
# ============================================================


class UserResearchInput(Base):
    """
    The raw scraped/pasted text from the user that seeds a campaign.

    Relationship: 1 input can spawn multiple StrategyCampaigns
    (e.g., A/B testing the same research with different models).
    """

    __tablename__ = "user_research_inputs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    tenant_id: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    raw_text: Mapped[str] = mapped_column(Text, nullable=False)
    source_type: Mapped[str] = mapped_column(
        String(32), nullable=False, default="manual"
    )  # manual | scraped | import
    char_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    # EC1 guard result
    passed_guard: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    guard_reject_reason: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_now
    )

    # Relationships
    campaigns: Mapped[list["StrategyCampaign"]] = relationship(
        "StrategyCampaign", back_populates="research_input", lazy="select"
    )


# ============================================================
# 2. StrategyCampaign (aggregate root / state machine)
# ============================================================


class StrategyCampaign(Base):
    """
    The overarching planning session and state machine owner.

    States: DRAFT_GENERATING → PENDING_HUMAN_APPROVAL → APPROVED →
            DISPATCHING_TO_API → PRODUCTION_PROCESSING → COMPLETED
            (plus REJECTED, FAILED, DISPATCH_FAILED, PRODUCTION_FAILED)

    Cross-system fields:
      correlation_id    — sent to Production; Production echoes in Webhooks
      idempotency_key   — SHA256 hash; prevents double-processing on retry
      production_job_id — returned by Production System ACK
    """

    __tablename__ = "strategy_campaigns"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    tenant_id: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    research_input_id: Mapped[str | None] = mapped_column(
        ForeignKey("user_research_inputs.id", ondelete="SET NULL"), nullable=True, index=True
    )

    # State machine
    status: Mapped[str] = mapped_column(
        String(32), nullable=False, default="DRAFT_GENERATING", index=True
    )

    # EC4 SEO mode
    seo_mode: Mapped[str] = mapped_column(
        String(32), nullable=False, default="full_seo_geo"
    )
    seo_mode_reason: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Cluster-level SEO summary
    cluster_primary_keyword: Mapped[str | None] = mapped_column(String(256), nullable=True)
    estimated_search_volume: Mapped[int | None] = mapped_column(Integer, nullable=True)
    cannibalization_checked: Mapped[bool] = mapped_column(Boolean, default=False)
    model_used: Mapped[str] = mapped_column(String(64), nullable=False, default="gpt-4o")

    # Human approval
    approved_by: Mapped[str | None] = mapped_column(String(256), nullable=True)
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Cross-system integration (Architecture Phase 2)
    correlation_id: Mapped[str | None] = mapped_column(
        String(128), nullable=True, unique=True, index=True
    )
    idempotency_key: Mapped[str | None] = mapped_column(
        String(256), nullable=True, unique=True
    )
    production_job_id: Mapped[str | None] = mapped_column(String(256), nullable=True)
    dispatch_attempts: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    dispatch_error: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Timestamps
    dispatched_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_now
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_now, onupdate=_now
    )

    # Relationships
    research_input: Mapped["UserResearchInput | None"] = relationship(
        "UserResearchInput", back_populates="campaigns"
    )
    intent: Mapped["ExtractedIntent | None"] = relationship(
        "ExtractedIntent", back_populates="campaign", uselist=False, cascade="all, delete-orphan"
    )
    cluster: Mapped["TopicCluster | None"] = relationship(
        "TopicCluster", back_populates="campaign", uselist=False, cascade="all, delete-orphan"
    )
    content_nodes: Mapped[list["ContentNode"]] = relationship(
        "ContentNode", back_populates="campaign", cascade="all, delete-orphan"
    )


# ============================================================
# 3. ExtractedIntent
# ============================================================


class ExtractedIntent(Base):
    """
    Structured output from Agent 1 (Intent Extractor).
    Relationship: 1:1 with StrategyCampaign.
    """

    __tablename__ = "extracted_intents"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    campaign_id: Mapped[str] = mapped_column(
        ForeignKey("strategy_campaigns.id", ondelete="CASCADE"), nullable=False, unique=True, index=True
    )
    research_input_id: Mapped[str | None] = mapped_column(
        ForeignKey("user_research_inputs.id", ondelete="SET NULL"), nullable=True
    )

    target_persona: Mapped[str] = mapped_column(Text, nullable=False)
    core_pain_points: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    underlying_emotions: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    raw_input_snippet: Mapped[str | None] = mapped_column(Text, nullable=True)
    model_used: Mapped[str] = mapped_column(String(64), nullable=False, default="gpt-4o")
    extraction_confidence: Mapped[float | None] = mapped_column(Float, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_now
    )

    # Relationships
    campaign: Mapped["StrategyCampaign"] = relationship(
        "StrategyCampaign", back_populates="intent"
    )


# ============================================================
# 4. TopicCluster
# ============================================================


class TopicCluster(Base):
    """
    The Hub & Spoke grouping logic generated by Agent 3.
    Relationship: 1:1 with StrategyCampaign, 1:N with ContentNode.
    """

    __tablename__ = "topic_clusters"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    campaign_id: Mapped[str] = mapped_column(
        ForeignKey("strategy_campaigns.id", ondelete="CASCADE"), nullable=False, unique=True, index=True
    )

    cluster_name: Mapped[str | None] = mapped_column(String(512), nullable=True)
    cluster_slug: Mapped[str | None] = mapped_column(String(512), nullable=True)
    primary_keyword: Mapped[str | None] = mapped_column(String(256), nullable=True)
    total_search_volume: Mapped[int | None] = mapped_column(Integer, nullable=True)
    node_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_now
    )

    # Relationships
    campaign: Mapped["StrategyCampaign"] = relationship(
        "StrategyCampaign", back_populates="cluster"
    )
    content_nodes: Mapped[list["ContentNode"]] = relationship(
        "ContentNode", back_populates="cluster", cascade="all, delete-orphan"
    )


# ============================================================
# 5. ContentNode
# ============================================================


class ContentNode(Base):
    """
    Individual article/video inside a cluster — the finest-grained unit.
    Maps 1:1 to a TopicBlueprint from the agent pipeline.

    'production_url' is NULL until the Production System fires the
    SUCCESS Webhook callback — then it is populated and ingested into Qdrant.
    """

    __tablename__ = "content_nodes"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    cluster_id: Mapped[str] = mapped_column(
        ForeignKey("topic_clusters.id", ondelete="CASCADE"), nullable=False, index=True
    )
    campaign_id: Mapped[str] = mapped_column(
        ForeignKey("strategy_campaigns.id", ondelete="CASCADE"), nullable=False, index=True
    )

    # Content identity
    topic_id: Mapped[str] = mapped_column(String(128), nullable=False)  # hub-main, spoke-before, etc.
    role: Mapped[str] = mapped_column(String(16), nullable=False)  # hub | spoke
    content_type: Mapped[str] = mapped_column(String(16), nullable=False)  # video | short | article
    title: Mapped[str] = mapped_column(String(512), nullable=False)
    slug: Mapped[str] = mapped_column(String(512), nullable=False, index=True)
    hook: Mapped[str | None] = mapped_column(Text, nullable=True)
    key_points: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    target_duration_s: Mapped[int | None] = mapped_column(Integer, nullable=True)
    tone: Mapped[str | None] = mapped_column(String(32), nullable=True)
    cta: Mapped[str | None] = mapped_column(String(512), nullable=True)

    # SEO metadata
    primary_keyword: Mapped[str | None] = mapped_column(String(256), nullable=True)
    secondary_keywords: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    long_tail_keywords: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    search_volume: Mapped[int | None] = mapped_column(Integer, nullable=True)
    search_volume_verified: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    keyword_difficulty: Mapped[float | None] = mapped_column(Float, nullable=True)
    search_intent: Mapped[str | None] = mapped_column(String(32), nullable=True)
    seo_mode: Mapped[str | None] = mapped_column(String(32), nullable=True)

    # GEO queries stored as JSONB array
    geo_queries: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)

    # Production tracking (populated by Webhook callback)
    production_url: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    production_status: Mapped[str | None] = mapped_column(
        String(32), nullable=True
    )  # null | processing | live | failed
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_now
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_now, onupdate=_now
    )

    __table_args__ = (
        UniqueConstraint("campaign_id", "slug", name="uq_node_campaign_slug"),
    )

    # Relationships
    cluster: Mapped["TopicCluster"] = relationship("TopicCluster", back_populates="content_nodes")
    campaign: Mapped["StrategyCampaign"] = relationship("StrategyCampaign", back_populates="content_nodes")
    outgoing_links: Mapped[list["InternalLink"]] = relationship(
        "InternalLink",
        foreign_keys="InternalLink.from_node_id",
        back_populates="from_node",
        cascade="all, delete-orphan",
    )
    incoming_links: Mapped[list["InternalLink"]] = relationship(
        "InternalLink",
        foreign_keys="InternalLink.to_node_id",
        back_populates="to_node",
        cascade="all, delete-orphan",
    )


# ============================================================
# 6. InternalLink (N:M join via explicit table)
# ============================================================


class InternalLink(Base):
    """
    Directed link between two ContentNodes.
    N:M relationship modelled as an explicit entity so links are
    queryable (e.g., 'find all CTAs that point to the hub').
    """

    __tablename__ = "internal_links"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    campaign_id: Mapped[str] = mapped_column(
        ForeignKey("strategy_campaigns.id", ondelete="CASCADE"), nullable=False, index=True
    )
    from_node_id: Mapped[str] = mapped_column(
        ForeignKey("content_nodes.id", ondelete="CASCADE"), nullable=False, index=True
    )
    to_node_id: Mapped[str] = mapped_column(
        ForeignKey("content_nodes.id", ondelete="CASCADE"), nullable=False, index=True
    )
    anchor_text: Mapped[str | None] = mapped_column(String(512), nullable=True)
    link_type: Mapped[str] = mapped_column(
        String(32), nullable=False, default="contextual"
    )  # contextual | cta | related
    existing_url: Mapped[str | None] = mapped_column(String(2048), nullable=True)

    # Relationships
    from_node: Mapped["ContentNode"] = relationship(
        "ContentNode", foreign_keys=[from_node_id], back_populates="outgoing_links"
    )
    to_node: Mapped["ContentNode"] = relationship(
        "ContentNode", foreign_keys=[to_node_id], back_populates="incoming_links"
    )
