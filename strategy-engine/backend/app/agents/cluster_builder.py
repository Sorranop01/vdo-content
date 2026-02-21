"""
Agent 3: Topic Cluster Builder (The Orchestrator)

Takes the SEO/GEO strategy and builds the Hub & Spoke topic cluster
with internal linking map. Includes RAG lookup placeholder for
keyword cannibalization checking.
"""

from __future__ import annotations

import logging
from typing import Optional

from pydantic import BaseModel, Field

from app.models.schemas import (
    SEOStrategyOutput,
    IntentExtractionOutput,
    ClusterOutput,
    TopicBlueprint,
    InternalLink,
    LinkType,
    TopicRole,
)
from app.services.llm_provider import structured_completion, resolve_provider

logger = logging.getLogger(__name__)


# ============================================================
# LLM Response Model for Cluster Building
# ============================================================


class InternalLinkSpec(BaseModel):
    """Specification for a single internal link."""

    from_topic_id: str = Field(description="Source topic ID")
    to_topic_id: str = Field(description="Target topic ID")
    anchor_text: str = Field(
        description="The clickable text for the hyperlink — should be natural Thai"
    )
    link_type: str = Field(
        description="'contextual' (in-content mention), 'cta' (call-to-action), or 'related' (sidebar/footer)"
    )


class ClusterBuildResponse(BaseModel):
    """Full LLM response for cluster building with linking."""

    hub: TopicBlueprint = Field(
        description="The refined Hub content piece with final title, hook, and key points"
    )
    spokes: list[TopicBlueprint] = Field(
        description="2-3 refined Spoke content pieces"
    )
    internal_links: list[InternalLinkSpec] = Field(
        description="All internal links between hub and spokes, including anchor text"
    )
    cannibalization_notes: list[str] = Field(
        default_factory=list,
        description="Any notes about potential content overlap or cannibalization risks"
    )


SYSTEM_PROMPT = """\
You are an expert content strategist specializing in the Hub & Spoke (Topic Cluster) model \
for the Thai content market.

You will receive a proposed SEO/GEO strategy with topic outlines from a previous agent. \
Your job is to REFINE and FINALIZE the cluster:

## YOUR TASKS:

### 1. REFINE THE TOPICS
- Improve titles to be more click-worthy and SEO-optimized (Thai)
- Sharpen the hooks to be more compelling
- Ensure key_points are actionable and content-ready
- Ensure each spoke has a DISTINCT angle (no overlap between spokes)

### 2. BUILD THE INTERNAL LINKING MAP
Create explicit links between ALL content pieces:

**Rules for internal links:**
- Hub MUST link to EVERY spoke (contextual links)
- EVERY spoke MUST link back to the hub (CTA link)
- Adjacent spokes SHOULD cross-link where natural (related links)
- Use natural Thai anchor text that a reader would expect
- Each link needs: from_topic_id, to_topic_id, anchor_text, link_type

**Link types:**
- "contextual": A natural mention within the content body
- "cta": A call-to-action (e.g., "อ่านเพิ่มเติม", "ดูไกด์ฉบับเต็ม")
- "related": A 'related content' suggestion (sidebar/end of article)

### 3. CHECK FOR CANNIBALIZATION
If any existing published content URLs are provided, note potential overlaps.
Also flag if any two topics in the cluster are too similar.

## IMPORTANT RULES:
- Keep topic_ids from the input — do NOT generate new IDs
- All titles MUST be in Thai
- Slugs MUST be in English
- anchor_text MUST be in Thai (it's user-facing)
- Aim for 4-8 internal links total across the cluster
- Each piece should have at least 2 links (one in, one out)
"""


async def build_cluster(
    intent: IntentExtractionOutput,
    seo_strategy: SEOStrategyOutput,
    existing_content: Optional[list[dict]] = None,
    model: str = "gpt-4o",
) -> ClusterOutput:
    """
    Build a Hub & Spoke topic cluster with internal linking.

    Args:
        intent: Structured data from Agent 1.
        seo_strategy: SEO/GEO strategy from Agent 2.
        existing_content: Published content from RAG lookup (Phase 2).
        model: LLM model to use.

    Returns:
        ClusterOutput with hub, spokes, and internal links.
    """
    logger.info("[Agent 3] Building topic cluster with internal links...")

    provider = resolve_provider(model)

    # Find the hub and spokes from Agent 2's output
    hub_topic = None
    spoke_topics = []
    for t in seo_strategy.proposed_topics:
        if t.role == TopicRole.HUB:
            hub_topic = t
        else:
            spoke_topics.append(t)

    if not hub_topic:
        # Fallback: use first topic as hub
        hub_topic = seo_strategy.proposed_topics[0]
        spoke_topics = seo_strategy.proposed_topics[1:]

    # Build context for the LLM
    existing_context = ""
    if existing_content:
        existing_context = "\n## Existing Published Content (check for cannibalization):\n"
        for item in existing_content:
            existing_context += f"- [{item.get('title', 'N/A')}]({item.get('url', 'N/A')}) — keywords: {item.get('keywords', 'N/A')}\n"

    topics_json = []
    for t in [hub_topic] + spoke_topics:
        topics_json.append(
            f"- **{t.role.value}** (id: {t.topic_id}): {t.title}\n"
            f"  slug: {t.slug}, hook: {t.hook}\n"
            f"  SEO keyword: {t.seo.primary_keyword}\n"
            f"  key_points: {', '.join(t.key_points)}"
        )

    user_prompt = f"""## Target Persona
{intent.target_persona}

## Pain Points
{chr(10).join(f"- {p}" for p in intent.core_pain_points)}

## Cluster Primary Keyword
{seo_strategy.cluster_primary_keyword}

## Proposed Topics from SEO Agent
{chr(10).join(topics_json)}
{existing_context}
---
Refine these topics and create the internal linking map."""

    result = await structured_completion(
        response_model=ClusterBuildResponse,
        system_prompt=SYSTEM_PROMPT,
        user_prompt=user_prompt,
        model=model,
        provider=provider,
        temperature=0.6,
        max_retries=2,
    )

    # Ensure roles are correct
    result.hub.role = TopicRole.HUB
    for spoke in result.spokes:
        spoke.role = TopicRole.SPOKE

    # Convert link specs to InternalLink models
    links = [
        InternalLink(
            from_topic_id=link.from_topic_id,
            to_topic_id=link.to_topic_id,
            anchor_text=link.anchor_text,
            link_type=LinkType(link.link_type) if link.link_type in [lt.value for lt in LinkType] else LinkType.CONTEXTUAL,
        )
        for link in result.internal_links
    ]

    logger.info(
        f"[Agent 3] ✅ Cluster: hub='{result.hub.title[:40]}...', "
        f"spokes={len(result.spokes)}, links={len(links)}, "
        f"cannibalization_notes={len(result.cannibalization_notes)}"
    )

    return ClusterOutput(
        hub=result.hub,
        spokes=result.spokes,
        internal_links=links,
        cannibalization_risks=result.cannibalization_notes,
        existing_content_links=[
            item.get("url", "") for item in (existing_content or [])
        ],
    )


async def check_cannibalization(
    keyword: str,
    threshold: float = 0.85,
) -> list[dict]:
    """
    Check for keyword cannibalization against published content in Vector DB.

    TODO (Phase 2): Implement with Qdrant vector search.

    Args:
        keyword: The keyword to check.
        threshold: Cosine similarity threshold for flagging.

    Returns:
        List of similar existing content items above threshold.
    """
    logger.info(
        f"[RAG] Checking cannibalization for: '{keyword}' (threshold: {threshold})"
    )
    return []  # No results until RAG is implemented in Phase 2
