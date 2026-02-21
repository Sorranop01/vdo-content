"""
Strategy Engine — Pipeline Self-Correction Guards

This module contains all chaos engineering / fallback mechanisms:

  EC1: GarbageInputGuard    — rejects irrelevant input before Agent 1 runs
  EC2: StructuredOutputGuard — validates inter-agent handoffs, retries on bad LLM output
  EC3: RAGMissHandler       — graceful empty-vector-DB handling for Agent 3
  EC4: SEODeadEndHandler    — pivots to GEO-only when no SEO keywords found

Each guard raises a specific, typed exception that the LangGraph pipeline
catches and maps to a clean pipeline error state. Nothing malformed ever
reaches the webhook or Agent 3.
"""

from __future__ import annotations

import logging
import re
from typing import Any, Callable, Coroutine, Optional, Type, TypeVar

from pydantic import BaseModel, ValidationError

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)


# ============================================================
# Exception Hierarchy
# ============================================================


class PipelineGuardError(Exception):
    """Base class for all self-correction guard errors."""

    def __init__(self, message: str, code: str, stage: str):
        super().__init__(message)
        self.code = code
        self.stage = stage
        self.message = message


class GarbageInputError(PipelineGuardError):
    """EC1: Input does not contain researchable consumer content."""

    def __init__(self, reason: str, confidence: float):
        super().__init__(
            message=f"Input rejected: {reason} (confidence={confidence:.2f})",
            code="GARBAGE_INPUT",
            stage="stage_1_intent",
        )
        self.reason = reason
        self.confidence = confidence


class StructuredOutputError(PipelineGuardError):
    """EC2: Agent returned malformed output after max retries."""

    def __init__(self, stage: str, attempts: int, last_error: str):
        super().__init__(
            message=f"Structured output failed after {attempts} attempts: {last_error}",
            code="STRUCTURED_OUTPUT_FAILURE",
            stage=stage,
        )
        self.attempts = attempts
        self.last_error = last_error


class SEODeadEndError(PipelineGuardError):
    """EC4: No viable SEO keywords found — strategy is GEO-only."""

    def __init__(self, keyword: str):
        super().__init__(
            message=f"No SEO volume found for '{keyword}' — pivoting to GEO-only strategy",
            code="SEO_DEAD_END",
            stage="stage_2_seo",
        )
        self.keyword = keyword


# ============================================================
# EC1: Garbage Input Guard
# ============================================================

# Minimum meaningful content signals
_MIN_CHAR_LENGTH = 30
_MIN_MEANINGFUL_WORDS = 5

# Patterns that strongly indicate irrelevant content
_GARBAGE_PATTERNS = [
    r"^\s*(?:lol|555|haha|XD|xD|😂|🤣|wtf|omg)\s*$",  # Pure reaction text
    r"^(?:test|hello|hi|สวัสดี|ทดสอบ)\s*$",             # Greetings / test messages
    r"(?:flour|butter|sugar|bake|tbsp|cup of|preheat)",  # Recipes
    r"(?:def |import |class |function |var |const |let )",  # Source code
    r"(?:http[s]?://\S+\s*){3,}",                          # Mostly URLs
]

# Required: at least ONE of these experience markers
_EXPERIENCE_SIGNALS = [
    r"(?:ซื้อ|bought|ordered|purchase|spend|เสีย|paid|จ่าย)",          # Purchase intent
    r"(?:ปวด|pain|hurt|ache|discomfort|เจ็บ|ไม่สบาย)",                # Physical symptoms
    r"(?:ปัญหา|problem|issue|struggle|frustrat|เบื่อ|กังวล|กลัว)",    # Problems/emotions
    r"(?:รีวิว|review|recommend|แนะนำ|ประสบการณ์|experience|ใช้งาน)", # Reviews/experience
    r"(?:อยากได้|want|need|looking for|หา|ต้องการ)",                  # Desire/need
    r"(?:เปรียบ|compare|vs\.|versus|ดีกว่า|better|worse)",            # Comparisons
    r"(?:cm|ซม|กิโล|kg|บาท|thb|฿|\$|usd|baht)",                      # Concrete measurements
]


class GarbageInputGuard:
    """
    EC1: Validates that raw input contains researchable consumer content.

    Runs BEFORE Agent 1 to prevent hallucinated content strategies from
    inputs that contain no real consumer intent data.

    Algorithm:
      1. Length check (too short = not enough context)
      2. Pattern blacklist (cake recipes, source code, pure reactions)
      3. Signal whitelist (must contain ≥1 purchase/pain/emotion marker)
      4. Word diversity check (same word repeated = spam)

    On failure: raises GarbageInputError with a user-friendly reason.
    The LangGraph node catches this and sets status=REJECTED (not FAILED).
    """

    def validate(self, text: str) -> tuple[bool, str, float]:
        """
        Validate input text.

        Returns:
            (is_valid, reason, confidence_score)
            confidence_score: 0.0–1.0 where 1.0 = definitely garbage
        """
        stripped = text.strip()

        # --- Check 1: Length ---
        if len(stripped) < _MIN_CHAR_LENGTH:
            return False, f"Input too short ({len(stripped)} chars, min {_MIN_CHAR_LENGTH})", 0.95

        words = re.findall(r'\w+', stripped.lower())
        if len(words) < _MIN_MEANINGFUL_WORDS:
            return False, f"Too few words ({len(words)}, min {_MIN_MEANINGFUL_WORDS})", 0.9

        # --- Check 2: Blacklist patterns ---
        for pattern in _GARBAGE_PATTERNS:
            if re.search(pattern, stripped, re.IGNORECASE):
                return False, f"Input matches non-research pattern: '{pattern}'", 0.88

        # --- Check 3: Whitelist signals (must have ≥1) ---
        found_signals = [
            p for p in _EXPERIENCE_SIGNALS
            if re.search(p, stripped, re.IGNORECASE)
        ]
        if not found_signals:
            return (
                False,
                "No consumer experience signals found (no purchase, pain, emotion, or measurement markers). "
                "Please paste user comments, reviews, or research notes.",
                0.75,
            )

        # --- Check 4: Word diversity (spam detection) ---
        if len(words) >= 10:
            unique_ratio = len(set(words)) / len(words)
            if unique_ratio < 0.3:
                return False, f"Input appears to be spam (word diversity={unique_ratio:.2f})", 0.82

        return True, "ok", 0.0

    def check(self, text: str) -> None:
        """
        Run validation. Raises GarbageInputError if invalid.
        Call this at the start of Agent 1.
        """
        is_valid, reason, confidence = self.validate(text)
        if not is_valid:
            logger.warning(f"[EC1] Garbage input rejected: {reason} (confidence={confidence:.2f})")
            raise GarbageInputError(reason=reason, confidence=confidence)

        logger.info(f"[EC1] Input validated OK (signals found, {len(text)} chars)")


# Singleton
_garbage_guard = GarbageInputGuard()


def get_garbage_guard() -> GarbageInputGuard:
    return _garbage_guard


# ============================================================
# EC2: Structured Output Retry Guard
# ============================================================


class StructuredOutputGuard:
    """
    EC2: Wraps any agent call with a validation + retry loop.

    The `instructor` library handles LLM-level retries for Pydantic parse
    failures. This guard adds a SECOND layer — a programmatic validation
    check AFTER parsing that verifies business-level constraints that
    Pydantic types alone can't express.

    Example: ensuring Agent 2 returned ≥1 spoke, or that spoke GEO
    queries contain constraints.

    Usage:
        guard = StructuredOutputGuard()
        result = await guard.run(
            fn=formulate_strategy,
            validator=lambda r: len(r.proposed_topics) >= 2,
            error_msg="Agent 2 returned fewer than 2 topics",
            max_attempts=3,
            stage="stage_2_seo",
            **kwargs
        )
    """

    async def run(
        self,
        fn: Callable[..., Coroutine[Any, Any, T]],
        validator: Callable[[T], bool],
        error_msg: str,
        stage: str,
        max_attempts: int = 3,
        **kwargs: Any,
    ) -> T:
        """
        Run a coroutine function with post-validation + retry.

        Args:
            fn: Async agent function to call.
            validator: Must return True if the result is acceptable.
            error_msg: Human-readable description of what's wrong on failure.
            stage: Pipeline stage name for error reporting.
            max_attempts: Max total attempts (including first call).
            **kwargs: Arguments passed to fn.

        Returns:
            Validated result of fn(**kwargs).

        Raises:
            StructuredOutputError if all attempts fail.
        """
        last_error = ""

        for attempt in range(1, max_attempts + 1):
            try:
                result = await fn(**kwargs)

                # Business-level validation (beyond Pydantic type checks)
                if not validator(result):
                    last_error = error_msg
                    logger.warning(
                        f"[EC2] {stage} attempt {attempt}/{max_attempts}: "
                        f"business validation failed — {error_msg}"
                    )
                    if attempt < max_attempts:
                        continue
                    raise StructuredOutputError(
                        stage=stage,
                        attempts=attempt,
                        last_error=last_error,
                    )

                logger.info(f"[EC2] {stage} passed validation on attempt {attempt}")
                return result

            except ValidationError as e:
                last_error = str(e)
                logger.warning(
                    f"[EC2] {stage} attempt {attempt}/{max_attempts}: "
                    f"Pydantic ValidationError — {last_error[:200]}"
                )
                if attempt >= max_attempts:
                    raise StructuredOutputError(
                        stage=stage,
                        attempts=attempt,
                        last_error=last_error,
                    )

        # Should not reach here but satisfy type checker
        raise StructuredOutputError(stage=stage, attempts=max_attempts, last_error=last_error)


# ============================================================
# EC3: RAG Memory Miss Handler
# ============================================================


class RAGMissResult:
    """Result of a RAG search, handling the empty-vector-DB case."""

    def __init__(
        self,
        found_items: list[dict],
        is_miss: bool,
        strategy: str,
    ):
        self.found_items = found_items    # Empty list if miss
        self.is_miss = is_miss            # True = no relevant content found
        self.strategy = strategy          # "rag_found" | "empty_registry" | "below_threshold"


class RAGMissHandler:
    """
    EC3: Handles the case where Qdrant returns 0 results.

    Scenarios:
      A) Brand-new website — vector DB is completely empty.
      B) Existing content, but nothing similar enough (below threshold).
      C) Qdrant is down (handled separately in graph.py with warning).

    In all cases, the contract is:
      - NEVER invent fake URLs or placeholder links.
      - Return an empty `existing_content_links` list.
      - Set `cannibalization_checked=True` with `cannibalization_risks=[]`
        so the dashboard shows "Checked — no conflicts found" (not "Not checked").
      - Log the miss reason so the operator can seed the registry if needed.

    The Agent 3 prompt is also modified: when `existing_content=None`,
    the "Outbound Links" section is replaced with a placeholder CTA section
    pointing to the Hub itself (safe internal links only).
    """

    def handle(
        self,
        similar_items: list,
        threshold: float,
        keyword: str,
    ) -> RAGMissResult:
        """
        Classify the RAG result and return a structured miss result.

        Args:
            similar_items: List of SimilarContent from Qdrant search.
            threshold: The similarity threshold that was used.
            keyword: The keyword that was searched.

        Returns:
            RAGMissResult describing why nothing was found and what to do.
        """
        if not similar_items:
            # Distinguish: is the collection empty, or just no matches?
            strategy = "empty_registry"
            logger.info(
                f"[EC3] RAG miss for '{keyword}': no results returned. "
                "Either the content registry is empty or no content is indexed yet. "
                "Proceeding without external links — set cannibalization_checked=True, risks=[]."
            )
            return RAGMissResult(
                found_items=[],
                is_miss=True,
                strategy=strategy,
            )

        # Items exist but all below threshold
        best_score = max(i.score for i in similar_items) if similar_items else 0
        logger.info(
            f"[EC3] RAG near-miss for '{keyword}': {len(similar_items)} candidates "
            f"but best score={best_score:.2f} < threshold={threshold:.2f}. "
            "No cannibalization risk flagged."
        )
        return RAGMissResult(
            found_items=[],
            is_miss=True,
            strategy="below_threshold",
        )

    def build_safe_context(self, miss_result: RAGMissResult) -> Optional[list[dict]]:
        """
        Returns None when there's a miss (signals Agent 3 to skip outbound links).
        Returns the real items list when content was found.
        """
        if miss_result.is_miss:
            return None  # Agent 3 will use internal-only link strategy
        return miss_result.found_items


# Singleton
_rag_miss_handler = RAGMissHandler()


def get_rag_miss_handler() -> RAGMissHandler:
    return _rag_miss_handler


# ============================================================
# EC4: SEO Dead-End Handler
# ============================================================


class SEOStrategy:
    """Output of the SEO dead-end analysis."""

    def __init__(
        self,
        mode: str,               # "full_seo_geo" | "geo_only" | "hitl_required"
        reason: str,
        cluster_keyword: str,
        geo_queries_only: bool = False,
        requires_human_review: bool = False,
    ):
        self.mode = mode
        self.reason = reason
        self.cluster_keyword = cluster_keyword
        self.geo_queries_only = geo_queries_only
        self.requires_human_review = requires_human_review


class SEODeadEndHandler:
    """
    EC4: Determines strategy when Agent 2 finds no viable SEO keywords.

    Dead-End Levels:
      Level 0 — Normal: primary_keyword has estimated volume > 0 → full SEO+GEO
      Level 1 — Low volume: volume = 0 or None for primary → pivot to GEO-only
        - Content still publishable; AI search (Perplexity/ChatGPT) is the channel
        - Dashboard shows "GEO-Only Mode" badge
        - No HITL interrupt; pipeline continues automatically
      Level 2 — Zero signals across ALL topics AND cluster is ambiguous:
        - Pause for HITL; operator must confirm or reject the cluster before dispatch
        - Dashboard shows "Human Review Required" status with explanation

    Thresholds:
      - volume >= 100 → viable SEO keyword
      - volume < 100 OR volume is None → low/zero signal
      - ALL topics have low signal → Level 2 (HITL)
    """

    _MIN_VIABLE_VOLUME = 100

    def evaluate(
        self,
        proposed_topics: list,
        estimated_total_volume: Optional[int],
    ) -> SEOStrategy:
        """
        Evaluate SEO health of Agent 2's output.

        Args:
            proposed_topics: List of TopicBlueprint from Agent 2.
            estimated_total_volume: AI-estimated total search volume.

        Returns:
            SEOStrategy describing the fallback mode.
        """
        cluster_keyword = proposed_topics[0].seo.primary_keyword if proposed_topics else "unknown"

        # Check per-topic GEO query presence
        all_have_geo = all(len(t.geo_queries) > 0 for t in proposed_topics)

        # Level 0: Healthy — has volume signal
        if estimated_total_volume and estimated_total_volume >= self._MIN_VIABLE_VOLUME:
            logger.info(
                f"[EC4] SEO healthy: estimated_volume={estimated_total_volume} "
                f"for '{cluster_keyword}'"
            )
            return SEOStrategy(
                mode="full_seo_geo",
                reason="SEO volume found — full strategy applied",
                cluster_keyword=cluster_keyword,
            )

        # Level 1: Low/no SEO volume but GEO queries present → auto-pivot
        if all_have_geo:
            logger.warning(
                f"[EC4] SEO dead-end for '{cluster_keyword}': "
                f"estimated_volume={estimated_total_volume}, all topics have GEO queries. "
                "Auto-pivoting to GEO-only strategy."
            )
            return SEOStrategy(
                mode="geo_only",
                reason=(
                    f"No measurable SEO search volume for '{cluster_keyword}'. "
                    "Strategy pivots to GEO (AI search engine) optimisation only. "
                    "Content is still valuable via ChatGPT/Perplexity/Google Gemini discovery."
                ),
                cluster_keyword=cluster_keyword,
                geo_queries_only=True,
            )

        # Level 2: No SEO AND some topics missing GEO → too risky, need HITL
        missing_geo = [t.topic_id for t in proposed_topics if len(t.geo_queries) == 0]
        logger.warning(
            f"[EC4] SEO dead-end Level 2 for '{cluster_keyword}': "
            f"no volume AND {len(missing_geo)} topics missing GEO queries. "
            "Flagging for HITL review."
        )
        return SEOStrategy(
            mode="hitl_required",
            reason=(
                f"Critical gap: no SEO volume for '{cluster_keyword}' AND topics "
                f"{missing_geo} have no GEO queries. "
                "Human review required before this blueprint can be sent to production."
            ),
            cluster_keyword=cluster_keyword,
            requires_human_review=True,
        )


# Singleton
_seo_dead_end_handler = SEODeadEndHandler()


def get_seo_dead_end_handler() -> SEODeadEndHandler:
    return _seo_dead_end_handler
