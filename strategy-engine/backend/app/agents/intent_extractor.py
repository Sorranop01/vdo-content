"""
Agent 1: Intent Extractor

Takes raw research text and extracts structured variables:
- Target Persona
- Core Pain Points
- Underlying Emotions

Uses instructor + Pydantic for guaranteed structured LLM output.

EC1: GarbageInputGuard runs BEFORE the LLM call to abort on irrelevant input.
"""

from __future__ import annotations

import logging

from app.models.schemas import IntentExtractionOutput
from app.services.llm_provider import structured_completion, resolve_provider
from app.agents.guards import get_garbage_guard, GarbageInputError  # noqa: F401 (re-exported)

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """\
You are an expert consumer research analyst specializing in the Thai market.

Given raw text from user comments, reviews, forum posts, or research notes, \
extract the following in a structured format:

1. **target_persona**: A concise description of WHO this person is.
   Include demographics, role/occupation, physical characteristics, \
   situation, and any other relevant context. Be specific, not vague.
   Example: "Female office worker, 150cm tall, 25-35 years old, \
   works 8+ hours at a desk, budget-conscious but willing to invest \
   in health-related products"

2. **core_pain_points**: Specific, actionable problems they face. \
   Not vague complaints — concrete issues that content can address.
   Include 2-5 items. Look for IMPLICIT pain points too.
   Example: ["Feet dangle from standard office chairs causing poor posture", \
   "Lower back pain develops after 3-4 hours of sitting"]

3. **underlying_emotions**: The emotional drivers BEHIND the pain points. \
   These are what make the content resonate on a human level.
   Include 1-4 items.
   Example: ["frustration — spent money but problem not solved", \
   "buyer's remorse — feels cheated by marketing claims"]

4. **raw_input_snippet**: Copy the first 500 characters of the input \
   for audit trail purposes.

IMPORTANT RULES:
- For Thai-language input, analyze in Thai context but keep field names in English.
- Pain points should be written in a way that suggests content topics.
- Emotions should be labeled with their type (frustration, fear, hope, etc.)
- Be thorough — a single raw text may contain multiple personas; \
  focus on the PRIMARY one.
- If you CANNOT identify a clear consumer pain point or persona in the text, \
  set core_pain_points to an empty list. Do NOT hallucinate pain points."""


async def extract_intent(
    raw_text: str,
    model: str = "deepseek-chat",
) -> IntentExtractionOutput:
    """
    Extract persona, pain points, and emotions from raw text.

    EC1: GarbageInputGuard runs before the LLM call and raises
    GarbageInputError if the input contains no researchable content.
    This error is caught by the LangGraph node and maps to REJECTED status.

    Args:
        raw_text: Raw research text from user input.
        model: LLM model to use.

    Returns:
        IntentExtractionOutput with structured fields.

    Raises:
        GarbageInputError: If input is irrelevant/non-researchable.
    """
    # ── EC1: Garbage Input Guard ───────────────────────────────────────────
    guard = get_garbage_guard()
    guard.check(raw_text)  # Raises GarbageInputError if invalid
    # ──────────────────────────────────────────────────────────────────────

    logger.info(f"[Agent 1] Extracting intent from {len(raw_text)} chars of text...")

    provider = resolve_provider(model)

    result = await structured_completion(
        response_model=IntentExtractionOutput,
        system_prompt=SYSTEM_PROMPT,
        user_prompt=raw_text,
        model=model,
        provider=provider,
        temperature=0.5,  # Lower temp for factual extraction
        max_retries=2,
    )

    # Ensure raw_input_snippet is set
    if not result.raw_input_snippet:
        result.raw_input_snippet = raw_text[:500]

    # ── EC1: Post-LLM check — did the model actually find pain points? ─────
    if len(result.core_pain_points) == 0:
        from app.agents.guards import GarbageInputError
        raise GarbageInputError(
            reason=(
                "LLM could not identify any consumer pain points in the input. "
                "Please provide user research text with clear problems, experiences, or needs."
            ),
            confidence=0.7,
        )
    # ──────────────────────────────────────────────────────────────────────

    logger.info(
        f"[Agent 1] ✅ Extracted: persona='{result.target_persona[:50]}...', "
        f"pain_points={len(result.core_pain_points)}, "
        f"emotions={len(result.underlying_emotions)}"
    )

    return result

