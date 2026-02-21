"""
Strategy Engine — Pydantic Schemas (SSOT)

This module defines ALL data models for the Strategy Engine.
The `ContentBlueprintPayload` is the API Contract — the strict JSON
payload sent to the Production System via webhook.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field, model_validator


# ============================================================
# Enums
# ============================================================


class ContentType(str, Enum):
    """Supported output content types."""
    VIDEO = "video"
    ARTICLE = "article"
    SHORT = "short"
    CAROUSEL = "carousel"


class SearchIntent(str, Enum):
    """SEO search intent classification."""
    INFORMATIONAL = "informational"
    COMMERCIAL = "commercial"
    TRANSACTIONAL = "transactional"
    NAVIGATIONAL = "navigational"


class GEOIntent(str, Enum):
    """Intent type for AI-search (GEO) queries."""
    INFORMATIONAL = "informational"
    COMPARISON = "comparison"
    SOLUTION = "solution"


class Tone(str, Enum):
    """Tone of voice for content."""
    EMPATHETIC = "empathetic"
    AUTHORITATIVE = "authoritative"
    CASUAL = "casual"
    URGENT = "urgent"


class LinkType(str, Enum):
    """Internal link relationship type."""
    CONTEXTUAL = "contextual"
    CTA = "cta"
    RELATED = "related"


class TopicRole(str, Enum):
    """Role of a topic in the Hub & Spoke model."""
    HUB = "hub"
    SPOKE = "spoke"


class PipelineStatus(str, Enum):
    """Status of a pipeline run."""
    PENDING = "pending"
    EXTRACTING_INTENT = "extracting_intent"
    FORMULATING_SEO = "formulating_seo"
    CLUSTERING = "clustering"
    AWAITING_REVIEW = "awaiting_review"
    APPROVED = "approved"
    DISPATCHING = "dispatching"
    COMPLETED = "completed"
    FAILED = "failed"
    REJECTED = "rejected"  # EC1: input rejected before agent pipeline ran


# ============================================================
# Sub-Models
# ============================================================


class GEOQuery(BaseModel):
    """A conversational query for AI search engines (ChatGPT, Perplexity, etc.)."""

    query_text: str = Field(description="The natural-language conversational query")
    intent: GEOIntent = Field(
        default=GEOIntent.INFORMATIONAL,
        description="Query intent type",
    )
    constraints: list[str] = Field(
        default_factory=list,
        description="Budget, physical, or situational constraints embedded in the query",
    )
    mandatory_elements: list[str] = Field(
        default_factory=list,
        description="Contextual elements the content MUST include to satisfy AI search engines",
    )


class SEOMetadata(BaseModel):
    """SEO strategy for a single topic."""

    primary_keyword: str = Field(description="Main target keyword")
    secondary_keywords: list[str] = Field(default_factory=list)
    long_tail_keywords: list[str] = Field(default_factory=list)
    search_volume: Optional[int] = Field(
        default=None,
        description="Monthly search volume (null = unverified/AI-estimated)",
    )
    search_volume_verified: bool = Field(
        default=False,
        description="True = real DataForSEO data. False = AI estimate (treat as approximate).",
    )
    keyword_difficulty: Optional[float] = Field(
        default=None,
        description="0-100 difficulty score from external API (null = unverified)",
    )
    search_intent: SearchIntent = Field(default=SearchIntent.INFORMATIONAL)


class InternalLink(BaseModel):
    """A directed internal link between two content pieces."""

    from_topic_id: str = Field(description="Source topic ID")
    to_topic_id: str = Field(description="Target topic ID")
    anchor_text: str = Field(description="Anchor text for the hyperlink")
    link_type: LinkType = Field(default=LinkType.CONTEXTUAL)
    existing_url: Optional[str] = Field(
        default=None,
        description="URL if linking to already-published content",
    )


class TopicBlueprint(BaseModel):
    """Blueprint for a single content piece (hub or spoke)."""

    topic_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str = Field(description="Proposed content title")
    slug: str = Field(description="URL-safe slug for the content")
    role: TopicRole = Field(description="'hub' or 'spoke'")
    content_type: ContentType = Field(default=ContentType.VIDEO)

    # Content guidance
    hook: str = Field(description="Opening hook or angle")
    key_points: list[str] = Field(description="3-7 key points to cover")
    target_word_count: Optional[int] = Field(default=None)
    target_duration_seconds: Optional[int] = Field(default=None)

    # SEO & GEO
    seo: SEOMetadata
    geo_queries: list[GEOQuery] = Field(default_factory=list)

    # Persona context
    tone: Tone = Field(default=Tone.EMPATHETIC)
    cta: Optional[str] = Field(
        default=None,
        description="Call-to-action for this content piece",
    )

    @model_validator(mode="after")
    def spokes_require_geo_queries(self) -> "TopicBlueprint":
        """
        ARCHITECTURE RULE: Every spoke MUST have at least 1 GEO query.
        This ensures constraints (height, budget) always survive to the
        final payload and downstream AI search content is always specified.
        """
        if self.role == TopicRole.SPOKE and len(self.geo_queries) == 0:
            raise ValueError(
                f"Spoke '{self.topic_id}' must have at least 1 GEO query. "
                "Spokes without GEO queries lose persona-specific constraints "
                "(height, budget, etc.) from the final payload."
            )
        return self


# ============================================================
# THE API CONTRACT — Master Payload
# ============================================================


class ContentBlueprintPayload(BaseModel):
    """
    THE MASTER API CONTRACT.

    This is the exact JSON payload sent from the Strategy Engine
    to the existing Production System (vdo-content) via webhook.
    Both systems MUST agree on this schema.
    """

    # --- Metadata ---
    blueprint_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    version: str = Field(default="1.0.0")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    approved_by: Optional[str] = Field(
        default=None,
        description="Username of the human who approved this blueprint",
    )

    # --- Persona & Context ---
    target_persona: str = Field(
        description="Description of the target audience persona",
    )
    core_pain_points: list[str] = Field(
        description="Extracted pain points from raw research",
    )
    underlying_emotions: list[str] = Field(
        description="Emotional drivers (frustration, fear, hope, etc.)",
    )
    raw_input_snippet: Optional[str] = Field(
        default=None,
        description="Original raw text excerpt for audit trail",
    )

    # --- Topic Cluster (Hub & Spoke) ---
    hub: TopicBlueprint = Field(description="Main pillar/hub content piece")
    spokes: list[TopicBlueprint] = Field(
        description="2-3 supporting spoke content pieces",
    )

    # --- Internal Linking Map ---
    internal_links: list[InternalLink] = Field(
        description="Directed links between hub, spokes, and existing content",
    )

    # --- Strategy-Level SEO Summary ---
    cluster_primary_keyword: str = Field(
        description="Overarching keyword theme for the entire cluster",
    )
    estimated_total_search_volume: Optional[int] = Field(
        default=None,
        description="Combined monthly search volume across all keywords",
    )

    # --- Pipeline Metadata ---
    pipeline_run_id: str = Field(
        default_factory=lambda: str(uuid.uuid4()),
        description="Tracing ID for the agent pipeline run",
    )
    agent_model_used: str = Field(
        default="deepseek-chat",
        description="LLM model used for generation",
    )
    cannibalization_checked: bool = Field(
        default=False,
        description="Whether RAG check for keyword cannibalization was performed",
    )
    existing_content_links: list[str] = Field(
        default_factory=list,
        description="URLs of existing published content referenced during planning",
    )


# ============================================================
# Agent Intermediate Outputs (used between pipeline stages)
# ============================================================


class IntentExtractionOutput(BaseModel):
    """Output of Agent 1: Intent Extractor."""

    target_persona: str
    core_pain_points: list[str]
    underlying_emotions: list[str]
    raw_input_snippet: Optional[str] = None


class SEOStrategyOutput(BaseModel):
    """Output of Agent 2: SEO/GEO Strategist."""

    proposed_topics: list[TopicBlueprint]
    cluster_primary_keyword: str
    estimated_total_search_volume: Optional[int] = None
    seo_mode: str = Field(
        default="full_seo_geo",
        description="EC4 strategy mode: full_seo_geo | geo_only | hitl_required",
    )
    seo_mode_reason: str = Field(
        default="",
        description="EC4 explanation of why this mode was chosen",
    )


class ClusterOutput(BaseModel):
    """Output of Agent 3: Topic Cluster Orchestrator."""

    hub: TopicBlueprint
    spokes: list[TopicBlueprint]
    internal_links: list[InternalLink]
    cannibalization_risks: list[str] = Field(default_factory=list)
    existing_content_links: list[str] = Field(default_factory=list)


# ============================================================
# Pipeline State (LangGraph)
# ============================================================


class PipelineState(BaseModel):
    """Full state object for the LangGraph pipeline."""

    run_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    status: PipelineStatus = Field(default=PipelineStatus.PENDING)
    raw_input: str = Field(description="Original raw text input from user")

    # Stage outputs (populated as pipeline progresses)
    intent: Optional[IntentExtractionOutput] = None
    seo_strategy: Optional[SEOStrategyOutput] = None
    cluster: Optional[ClusterOutput] = None

    # Final output
    blueprint: Optional[ContentBlueprintPayload] = None

    # Metadata
    model_used: str = Field(default="deepseek-chat")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None
    error: Optional[str] = None
