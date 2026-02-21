"""Initial migration — create all Strategy Engine tables

Revision ID: 0001_initial
Revises: (none)
Create Date: 2026-02-21

Creates:
  - user_research_inputs
  - strategy_campaigns
  - extracted_intents
  - topic_clusters
  - content_nodes
  - internal_links
"""

from __future__ import annotations

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers
revision: str = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── user_research_inputs ───────────────────────────────────────────────
    op.create_table(
        "user_research_inputs",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("tenant_id", sa.String(128), nullable=False),
        sa.Column("raw_text", sa.Text, nullable=False),
        sa.Column("source_type", sa.String(32), nullable=False, server_default="manual"),
        sa.Column("char_count", sa.Integer, nullable=False, server_default="0"),
        sa.Column("passed_guard", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("guard_reject_reason", sa.Text, nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
    )
    op.create_index("ix_user_research_inputs_tenant_id", "user_research_inputs", ["tenant_id"])

    # ── strategy_campaigns (aggregate root) ────────────────────────────────
    op.create_table(
        "strategy_campaigns",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("tenant_id", sa.String(128), nullable=False),
        sa.Column(
            "research_input_id",
            sa.String(36),
            sa.ForeignKey("user_research_inputs.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("status", sa.String(32), nullable=False, server_default="DRAFT_GENERATING"),
        sa.Column("seo_mode", sa.String(32), nullable=False, server_default="full_seo_geo"),
        sa.Column("seo_mode_reason", sa.Text, nullable=True),
        sa.Column("cluster_primary_keyword", sa.String(256), nullable=True),
        sa.Column("estimated_search_volume", sa.Integer, nullable=True),
        sa.Column("cannibalization_checked", sa.Boolean, server_default="false"),
        sa.Column("model_used", sa.String(64), nullable=False, server_default="gpt-4o"),
        sa.Column("approved_by", sa.String(256), nullable=True),
        sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True),
        # Cross-system integration fields (Phase 2)
        sa.Column("correlation_id", sa.String(128), nullable=True, unique=True),
        sa.Column("idempotency_key", sa.String(256), nullable=True, unique=True),
        sa.Column("production_job_id", sa.String(256), nullable=True),
        sa.Column("dispatch_attempts", sa.Integer, nullable=False, server_default="0"),
        sa.Column("dispatch_error", sa.Text, nullable=True),
        # Timestamps
        sa.Column("dispatched_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
    )
    op.create_index("ix_strategy_campaigns_tenant_id", "strategy_campaigns", ["tenant_id"])
    op.create_index("ix_strategy_campaigns_status", "strategy_campaigns", ["status"])
    op.create_index("ix_strategy_campaigns_research_input_id", "strategy_campaigns", ["research_input_id"])
    op.create_index("ix_strategy_campaigns_correlation_id", "strategy_campaigns", ["correlation_id"])

    # ── extracted_intents ──────────────────────────────────────────────────
    op.create_table(
        "extracted_intents",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "campaign_id",
            sa.String(36),
            sa.ForeignKey("strategy_campaigns.id", ondelete="CASCADE"),
            nullable=False,
            unique=True,
        ),
        sa.Column(
            "research_input_id",
            sa.String(36),
            sa.ForeignKey("user_research_inputs.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("target_persona", sa.Text, nullable=False),
        sa.Column("core_pain_points", postgresql.JSONB, nullable=False, server_default="[]"),
        sa.Column("underlying_emotions", postgresql.JSONB, nullable=False, server_default="[]"),
        sa.Column("raw_input_snippet", sa.Text, nullable=True),
        sa.Column("model_used", sa.String(64), nullable=False, server_default="gpt-4o"),
        sa.Column("extraction_confidence", sa.Float, nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
    )
    op.create_index("ix_extracted_intents_campaign_id", "extracted_intents", ["campaign_id"])

    # ── topic_clusters ─────────────────────────────────────────────────────
    op.create_table(
        "topic_clusters",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "campaign_id",
            sa.String(36),
            sa.ForeignKey("strategy_campaigns.id", ondelete="CASCADE"),
            nullable=False,
            unique=True,
        ),
        sa.Column("cluster_name", sa.String(512), nullable=True),
        sa.Column("cluster_slug", sa.String(512), nullable=True),
        sa.Column("primary_keyword", sa.String(256), nullable=True),
        sa.Column("total_search_volume", sa.Integer, nullable=True),
        sa.Column("node_count", sa.Integer, nullable=False, server_default="0"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
    )
    op.create_index("ix_topic_clusters_campaign_id", "topic_clusters", ["campaign_id"])

    # ── content_nodes ──────────────────────────────────────────────────────
    op.create_table(
        "content_nodes",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "cluster_id",
            sa.String(36),
            sa.ForeignKey("topic_clusters.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "campaign_id",
            sa.String(36),
            sa.ForeignKey("strategy_campaigns.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("topic_id", sa.String(128), nullable=False),
        sa.Column("role", sa.String(16), nullable=False),
        sa.Column("content_type", sa.String(16), nullable=False),
        sa.Column("title", sa.String(512), nullable=False),
        sa.Column("slug", sa.String(512), nullable=False),
        sa.Column("hook", sa.Text, nullable=True),
        sa.Column("key_points", postgresql.JSONB, nullable=False, server_default="[]"),
        sa.Column("target_duration_s", sa.Integer, nullable=True),
        sa.Column("tone", sa.String(32), nullable=True),
        sa.Column("cta", sa.String(512), nullable=True),
        # SEO
        sa.Column("primary_keyword", sa.String(256), nullable=True),
        sa.Column("secondary_keywords", postgresql.JSONB, nullable=False, server_default="[]"),
        sa.Column("long_tail_keywords", postgresql.JSONB, nullable=False, server_default="[]"),
        sa.Column("search_volume", sa.Integer, nullable=True),
        sa.Column("search_volume_verified", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("keyword_difficulty", sa.Float, nullable=True),
        sa.Column("search_intent", sa.String(32), nullable=True),
        sa.Column("seo_mode", sa.String(32), nullable=True),
        sa.Column("geo_queries", postgresql.JSONB, nullable=False, server_default="[]"),
        # Production tracking (populated after Webhook callback)
        sa.Column("production_url", sa.String(2048), nullable=True),
        sa.Column("production_status", sa.String(32), nullable=True),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
        sa.UniqueConstraint("campaign_id", "slug", name="uq_node_campaign_slug"),
    )
    op.create_index("ix_content_nodes_cluster_id", "content_nodes", ["cluster_id"])
    op.create_index("ix_content_nodes_campaign_id", "content_nodes", ["campaign_id"])
    op.create_index("ix_content_nodes_slug", "content_nodes", ["slug"])

    # ── internal_links ─────────────────────────────────────────────────────
    op.create_table(
        "internal_links",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "campaign_id",
            sa.String(36),
            sa.ForeignKey("strategy_campaigns.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "from_node_id",
            sa.String(36),
            sa.ForeignKey("content_nodes.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "to_node_id",
            sa.String(36),
            sa.ForeignKey("content_nodes.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("anchor_text", sa.String(512), nullable=True),
        sa.Column("link_type", sa.String(32), nullable=False, server_default="contextual"),
        sa.Column("existing_url", sa.String(2048), nullable=True),
    )
    op.create_index("ix_internal_links_campaign_id", "internal_links", ["campaign_id"])
    op.create_index("ix_internal_links_from_node_id", "internal_links", ["from_node_id"])
    op.create_index("ix_internal_links_to_node_id", "internal_links", ["to_node_id"])

    # ── updated_at trigger (auto-update on row change) ─────────────────────
    op.execute("""
        CREATE OR REPLACE FUNCTION update_updated_at_column()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = NOW();
            RETURN NEW;
        END;
        $$ language 'plpgsql';
    """)
    for tbl in ("strategy_campaigns", "content_nodes"):
        op.execute(f"""
            CREATE TRIGGER trg_{tbl}_updated_at
            BEFORE UPDATE ON {tbl}
            FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
        """)


def downgrade() -> None:
    for tbl in ("strategy_campaigns", "content_nodes"):
        op.execute(f"DROP TRIGGER IF EXISTS trg_{tbl}_updated_at ON {tbl};")
    op.execute("DROP FUNCTION IF EXISTS update_updated_at_column;")

    op.drop_table("internal_links")
    op.drop_table("content_nodes")
    op.drop_table("topic_clusters")
    op.drop_table("extracted_intents")
    op.drop_table("strategy_campaigns")
    op.drop_table("user_research_inputs")
