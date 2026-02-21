"""
Agent 2: SEO/GEO Strategist

Takes extracted intent data and generates:
- SEO Keywords (primary, secondary, long-tail) with verification placeholders
- GEO Queries (conversational queries for AI search engines)
- Proposed topic outlines for Hub + Spokes

Uses instructor for structured output.
Includes a placeholder for DataForSEO API integration.
"""

from __future__ import annotations

import logging
from typing import Optional

from pydantic import BaseModel, Field

from app.models.schemas import (
    IntentExtractionOutput,
    SEOStrategyOutput,
    TopicBlueprint,
    SEOMetadata,
    GEOQuery,
    TopicRole,
    ContentType,
)
from app.services.llm_provider import structured_completion, resolve_provider
from app.services.seo_api_service import get_seo_service
from app.agents.guards import (
    get_seo_dead_end_handler,
    SEODeadEndError,
)


logger = logging.getLogger(__name__)


# ============================================================
# Intermediate LLM Response Model (richer than final output)
# ============================================================


class SEOGEOResponse(BaseModel):
    """Full LLM response for SEO/GEO strategy generation."""

    cluster_primary_keyword: str = Field(
        description="The overarching keyword theme for the entire content cluster"
    )

    estimated_total_search_volume: Optional[int] = Field(
        default=None,
        description="AI-estimated combined monthly search volume across all topics (best guess, unverified)",
    )

    hub_topic: TopicBlueprint = Field(
        description="The main Hub (pillar) content piece"
    )

    spoke_topics: list[TopicBlueprint] = Field(
        description="2-3 supporting Spoke content pieces following Before/During/After journey"
    )


SYSTEM_PROMPT = """\
You are an expert SEO/GEO strategist for the Thai content market (YouTube, blogs, social media).

Given a target persona and their pain points, generate a COMPLETE content strategy:

## SEO STRATEGY (for each topic):
1. **primary_keyword**: Thai-language keyword with highest search potential.
   Use natural Thai phrases people actually search for.
2. **secondary_keywords**: 2-3 related terms (can mix Thai and English).
3. **long_tail_keywords**: 1-2 highly specific, low-competition queries in Thai.
4. **search_intent**: Classify as informational/commercial/transactional/navigational.

## GEO STRATEGY (Generative Engine Optimization):
For EACH topic, generate 1-2 conversational queries:
1. **query_text**: What this persona would ask ChatGPT/Perplexity/Google Gemini.
   Include specific constraints (budget, physical specs, comparisons).
2. **constraints**: Budget limits, physical limitations, situational constraints.
3. **mandatory_elements**: Things the content MUST include to satisfy AI search engines.
   These are the structured data points that AI models look for.

## TOPIC STRUCTURE:
Generate one **Hub** (comprehensive pillar content) and 2-3 **Spokes** (supporting content):

**Hub (role="hub"):**
- Comprehensive guide covering the entire topic
- content_type: "video" (default) — 5-8 minute video
- Hook should be attention-grabbing and address the core pain

**Spokes (role="spoke"):**
- Follow the user journey: Before → During → After
  - "Before": Awareness, signs, early research
  - "During": Evaluation, comparison, decision-making
  - "After": Implementation, review, optimization
- content_type: "short" for before/after (60s), "video" for during (3-5 min)
- Each spoke should have a clear, distinct angle

IMPORTANT RULES:
- Titles MUST be in Thai (they're for Thai audience)
- Slugs MUST be in English (URL-safe)
- Hooks should be conversational, curiosity-driven Thai
- key_points can be in English (internal reference)
- All topic_ids should be descriptive: "hub-main", "spoke-before", "spoke-during", "spoke-after"
- Set tone appropriately: empathetic for pain, casual for tips, authoritative for guides

CRITICAL — GEO CONSTRAINT RULES:
- Every GEO query `constraints` list MUST include any physical spec from the input (e.g. "height: 150cm").
- Every GEO query `constraints` list MUST include any budget from the input (e.g. "budget: ฿5,000").
- EVERY spoke MUST have at least 1 GEO query — no spoke may have an empty geo_queries list.
- The Hub MUST have 1-2 GEO queries covering broad purchase intent.
- `mandatory_elements` must include exact numeric thresholds (cm, THB) whenever they exist in the input.

SEARCH VOLUME:
- Provide `estimated_total_search_volume` as your best AI estimate of combined monthly Thai searches.
  Mark this as an AI estimate — it will be overridden by real SEO API data later.
"""


async def formulate_strategy(
    intent: IntentExtractionOutput,
    model: str = "deepseek-chat",
) -> SEOStrategyOutput:
    """
    Generate SEO/GEO strategy from extracted intent.

    Args:
        intent: Structured output from Agent 1.
        model: LLM model to use.

    Returns:
        SEOStrategyOutput with proposed topics and keyword strategy.
    """
    logger.info("[Agent 2] Formulating SEO/GEO strategy...")

    provider = resolve_provider(model)

    # Build context from Agent 1's output
    user_prompt = f"""## Target Persona
{intent.target_persona}

## Core Pain Points
{chr(10).join(f"- {p}" for p in intent.core_pain_points)}

## Underlying Emotions
{chr(10).join(f"- {e}" for e in intent.underlying_emotions)}

## Original Research Snippet
{intent.raw_input_snippet or "N/A"}

---
Generate the full SEO/GEO strategy with Hub + Spokes for this persona."""

    result = await structured_completion(
        response_model=SEOGEOResponse,
        system_prompt=SYSTEM_PROMPT,
        user_prompt=user_prompt,
        model=model,
        provider=provider,
        temperature=0.7,  # Slightly creative for keyword ideas
        max_retries=2,
    )

    # Ensure role fields are set correctly
    result.hub_topic.role = TopicRole.HUB
    for spoke in result.spoke_topics:
        spoke.role = TopicRole.SPOKE

    all_topics = [result.hub_topic] + result.spoke_topics

    # ── EC2: Business validation — ensure we have ≥1 hub + ≥1 spoke ────────
    if len(result.spoke_topics) == 0:
        logger.error("[Agent 2] EC2 violation: no spoke topics returned by LLM")
        raise ValueError(
            "Agent 2 returned 0 spoke topics. At least 1 spoke is required for a content cluster."
        )
    # ──────────────────────────────────────────────────────────────────────

    # ── EC4: SEO Dead-End Evaluation ──────────────────────────────────────
    ec4 = get_seo_dead_end_handler()
    seo_strategy_mode = ec4.evaluate(
        proposed_topics=all_topics,
        estimated_total_volume=result.estimated_total_search_volume,
    )

    if seo_strategy_mode.requires_human_review:
        # Level 2 dead-end: flag for HITL, do not abort — pass the warning forward
        logger.warning(
            f"[Agent 2] EC4 Level 2: {seo_strategy_mode.reason}"
        )
        # Attach the dead-end reason to the strategy note (carried in cluster_primary_keyword)
        # The graph node will read this and set status to AWAITING_REVIEW with a warning
    elif seo_strategy_mode.geo_queries_only:
        # Level 1 auto-pivot: GEO-only — strip search_volume expectations, continue
        logger.warning(
            f"[Agent 2] EC4 Level 1: {seo_strategy_mode.reason}"
        )
    # ──────────────────────────────────────────────────────────────────────

    # ── Phase 4.4: DataForSEO — verify keyword volumes & KD ────────────────
    all_primary_keywords = [t.seo.primary_keyword for t in all_topics]
    try:
        seo_svc = get_seo_service()
        batch = await seo_svc.get_batch_metrics(all_primary_keywords)
        if batch.api_available:
            verified_total = 0
            for topic in all_topics:
                kw = topic.seo.primary_keyword
                metrics = batch.results.get(kw)
                if metrics and metrics.is_verified:
                    topic.seo.search_volume = metrics.search_volume
                    topic.seo.keyword_difficulty = metrics.keyword_difficulty
                    if metrics.search_volume:
                        verified_total += metrics.search_volume
            if verified_total > 0:
                # Override AI-estimated volume with verified sum
                result.estimated_total_search_volume = verified_total
                logger.info(f"[Agent 2] DataForSEO: verified total volume = {verified_total}")
        else:
            logger.info(f"[Agent 2] DataForSEO unavailable ({batch.error}) — using AI estimates")
    except Exception as e:
        logger.warning(f"[Agent 2] DataForSEO enrichment failed (non-fatal): {e}")
    # ────────────────────────────────────────────────────────────────────────

    logger.info(
        f"[Agent 2] ✅ Strategy: cluster='{result.cluster_primary_keyword}', "
        f"hub='{result.hub_topic.title[:40]}...', "
        f"spokes={len(result.spoke_topics)}, "
        f"seo_mode={seo_strategy_mode.mode}"
    )

    return SEOStrategyOutput(
        proposed_topics=all_topics,
        cluster_primary_keyword=result.cluster_primary_keyword,
        estimated_total_search_volume=result.estimated_total_search_volume,
        seo_mode=seo_strategy_mode.mode,
        seo_mode_reason=seo_strategy_mode.reason,
    )


async def verify_keyword_volume(
    keyword: str,
    language: str = "th",
) -> dict:
    """
    Verify keyword search volume via DataForSEO API (Phase 4.4).

    Args:
        keyword: The keyword to verify.
        language: Language code (default: 'th' = Thai).

    Returns:
        Dict with search_volume, keyword_difficulty, is_verified, and source.
        search_volume / keyword_difficulty may be None if API is unavailable.
    """
    logger.info(f"[SEO API] Verifying keyword: '{keyword}' (language: {language})")
    svc = get_seo_service()
    lang_map = {"th": "th", "en": "en"}
    metrics = await svc.get_keyword_metrics(
        keyword=keyword,
        language_code=lang_map.get(language, "th"),
    )
    return {
        "keyword": metrics.keyword,
        "search_volume": metrics.search_volume,
        "keyword_difficulty": metrics.keyword_difficulty,
        "cpc": metrics.cpc,
        "is_verified": metrics.is_verified,
        "source": metrics.source,
    }
