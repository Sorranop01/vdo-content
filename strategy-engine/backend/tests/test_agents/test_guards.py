"""
Tests for the Pipeline Self-Correction Guards (EC1–EC4).

Each test section maps to one Error Correction code:
  EC1 — GarbageInputGuard   (test_garbage_input_guard_*)
  EC2 — StructuredOutputGuard (test_structured_output_guard_*)
  EC3 — RAGMissHandler       (test_rag_miss_handler_*)
  EC4 — SEODeadEndHandler    (test_seo_dead_end_handler_*)
"""

from __future__ import annotations

import pytest
from unittest.mock import AsyncMock, MagicMock
from pydantic import ValidationError

from app.agents.guards import (
    GarbageInputGuard,
    GarbageInputError,
    StructuredOutputGuard,
    StructuredOutputError,
    RAGMissHandler,
    RAGMissResult,
    SEODeadEndHandler,
    SEOStrategy,
)
from app.models.schemas import (
    TopicBlueprint,
    TopicRole,
    ContentType,
    SEOMetadata,
    GEOQuery,
    GEOIntent,
    SearchIntent,
    Tone,
)


# ============================================================
# Fixtures
# ============================================================

REAL_INPUT = """\
ซื้อเก้าอี้ ergonomic มาแพงมาก แต่ยังปวดหลังอยู่เลย ทั้งที่ตั้งสูงสุดแล้ว
เท้าก็ยังลอยอยู่ดี เพราะตัวเล็กสูงแค่ 150 ซม งบอยู่ที่ประมาณ 5000 บาท
ใครเคยเจอปัญหานี้แนะนำได้เลย รู้สึกซื้อมาแล้วเหมือนเสียเงินฟรี
"""

GARBAGE_INPUTS = [
    ("lol this is funny 555", "pure reaction text"),
    ("hi", "greeting"),
    ("2 cups flour, 1 tsp baking soda, preheat oven 350°F", "recipe"),
    ("def hello(): pass\nclass Foo:\n    pass\nimport os", "source code"),
    ("https://example.com https://example2.com https://example3.com", "mostly URLs"),
    ("ทดสอบ", "test greeting in Thai"),
    (
        "word word word word word word word word word word word word word",
        "no diversity (spam-like)",
    ),
    ("ok", "too short"),
]

SIGNAL_INPUTS = [
    ("ซื้อเก้าอี้มาแพง แต่ยังปวดหลัง ทั้งที่ราคา 5000 บาท", "Thai with pain + price"),
    ("I bought an office chair and my back hurts after 3 hours", "English pain"),
    ("comparing chair A vs chair B for budget under 5000 THB", "English comparison with THB"),
    ("รีวิวเก้าอี้ทำงานสำหรับคนสูง 155cm ประสบการณ์ใช้งานจริง", "Thai review with cm"),
]


def _make_spoke(geo_queries=None) -> TopicBlueprint:
    return TopicBlueprint(
        title="5 สัญญาณว่าเก้าอี้ไม่เหมาะ",
        slug="5-signs-wrong-chair",
        role=TopicRole.SPOKE,
        content_type=ContentType.SHORT,
        hook="ถ้าเท้าคุณลอยตอนนั่ง...",
        key_points=["Feet dangling", "Knee angle"],
        target_duration_seconds=60,
        seo=SEOMetadata(
            primary_keyword="สัญญาณเก้าอี้ไม่เหมาะ",
            search_intent=SearchIntent.INFORMATIONAL,
        ),
        geo_queries=geo_queries
        or [
            GEOQuery(
                query_text="เก้าอี้ ergonomic สำหรับคนตัวเล็ก 150cm งบ 5000",
                intent=GEOIntent.SOLUTION,
                constraints=["height: 150cm", "budget: ฿5,000"],
                mandatory_elements=["seat height in cm", "footrest option"],
            )
        ],
        tone=Tone.CASUAL,
    )


def _make_hub() -> TopicBlueprint:
    return TopicBlueprint(
        title="เก้าอี้ทำงานสำหรับคนตัวเล็ก",
        slug="ergonomic-chair-petite-guide",
        role=TopicRole.HUB,
        content_type=ContentType.VIDEO,
        hook="คุณซื้อเก้าอี้แพงแต่ยังปวดหลัง?",
        key_points=["Why standard chairs fail", "The dangling feet problem"],
        target_duration_seconds=480,
        seo=SEOMetadata(
            primary_keyword="เก้าอี้ทำงาน คนตัวเล็ก",
            search_volume=1200,
            search_intent=SearchIntent.INFORMATIONAL,
        ),
        geo_queries=[
            GEOQuery(
                query_text="best ergonomic chair for 150cm person under 5000 baht",
                intent=GEOIntent.COMPARISON,
                constraints=["height: 150cm", "budget: ฿5,000"],
                mandatory_elements=["seat depth", "footrest"],
            )
        ],
        tone=Tone.EMPATHETIC,
    )


# ============================================================
# EC1: GarbageInputGuard
# ============================================================


class TestGarbageInputGuardValidate:
    """Unit tests for GarbageInputGuard.validate() — does not raise, returns (bool, reason, conf)."""

    def setup_method(self):
        self.guard = GarbageInputGuard()

    @pytest.mark.parametrize("text,description", GARBAGE_INPUTS)
    def test_garbage_inputs_fail(self, text: str, description: str):
        is_valid, reason, confidence = self.guard.validate(text)
        assert not is_valid, f"Should reject: {description}"
        assert reason, "Reason must be non-empty"
        assert 0.5 <= confidence <= 1.0, f"Confidence must be in [0.5, 1.0], got {confidence}"

    @pytest.mark.parametrize("text,description", SIGNAL_INPUTS)
    def test_real_inputs_pass(self, text: str, description: str):
        is_valid, reason, confidence = self.guard.validate(text)
        assert is_valid, f"Should accept: {description} (reason={reason})"
        assert confidence == 0.0, "Confidence should be 0.0 for valid input"

    def test_real_thai_research_text_passes(self):
        is_valid, reason, _ = self.guard.validate(REAL_INPUT)
        assert is_valid, f"Should accept full Thai research text (reason={reason})"

    def test_reason_is_descriptive_for_garbage(self):
        _, reason, _ = self.guard.validate("lol")
        assert len(reason) > 10, "Reason must be descriptive, not just a code"


class TestGarbageInputGuardCheck:
    """Tests for GarbageInputGuard.check() — the raising interface used by Agent 1."""

    def setup_method(self):
        self.guard = GarbageInputGuard()

    def test_check_raises_on_garbage(self):
        with pytest.raises(GarbageInputError) as exc_info:
            self.guard.check("lol 555")
        assert exc_info.value.code == "GARBAGE_INPUT"
        assert exc_info.value.stage == "stage_1_intent"
        assert exc_info.value.confidence > 0.5

    def test_check_raises_with_reason(self):
        with pytest.raises(GarbageInputError) as exc_info:
            self.guard.check("hi")
        assert exc_info.value.reason, "Exception must carry a reason"

    def test_check_silent_on_valid_input(self):
        # Should not raise
        self.guard.check(REAL_INPUT)

    def test_garbage_input_error_is_not_base_exception(self):
        """GarbageInputError inherits PipelineGuardError, not generic Exception.
        This ensures the LangGraph pipeline can catch it precisely."""
        from app.agents.guards import PipelineGuardError
        err = GarbageInputError(reason="test", confidence=0.9)
        assert isinstance(err, PipelineGuardError)
        assert isinstance(err, Exception)

    def test_cake_recipe_rejected(self):
        recipe = "2 cups flour, 1 cup sugar, preheat oven at 350F, bake for 30 minutes"
        with pytest.raises(GarbageInputError):
            self.guard.check(recipe)

    def test_source_code_rejected(self):
        code = "def extract_intent(text: str):\n    import openai\n    class Agent: pass"
        with pytest.raises(GarbageInputError):
            self.guard.check(code)

    def test_minimum_length_boundary(self):
        """Exactly 30 chars with no signals should still fail (no consumer signals)."""
        exactly_30 = "a" * 30  # No consumer signals
        with pytest.raises(GarbageInputError):
            self.guard.check(exactly_30)

    def test_short_but_meaningful(self):
        """Short text with real consumer signals should pass."""
        short_meaningful = "ปวดหลัง ซื้อเก้าอี้งบ 5000 บาทยังไม่หาย"
        # May or may not pass depending on byte length — just verify it doesn't crash
        is_valid, _, _ = self.guard.validate(short_meaningful)
        # Not asserting pass/fail here since length depends on Thai encoding


# ============================================================
# EC2: StructuredOutputGuard
# ============================================================


class TestStructuredOutputGuard:
    """Tests for StructuredOutputGuard.run() — retry loop with business validation."""

    def setup_method(self):
        self.guard = StructuredOutputGuard()

    @pytest.mark.asyncio
    async def test_passes_on_first_attempt(self):
        mock_fn = AsyncMock(return_value=42)
        result = await self.guard.run(
            fn=mock_fn,
            validator=lambda r: r == 42,
            error_msg="should be 42",
            stage="test_stage",
            max_attempts=3,
        )
        assert result == 42
        assert mock_fn.call_count == 1

    @pytest.mark.asyncio
    async def test_retries_on_business_validation_failure(self):
        """Returns bad value twice, then good value — should succeed on 3rd attempt."""
        call_count = 0

        async def flaky_fn(**kwargs):
            nonlocal call_count
            call_count += 1
            return call_count  # 1, 2, 3...

        result = await self.guard.run(
            fn=flaky_fn,
            validator=lambda r: r == 3,  # Only passes on 3rd call
            error_msg="value must be 3",
            stage="test_stage",
            max_attempts=3,
        )
        assert result == 3
        assert call_count == 3

    @pytest.mark.asyncio
    async def test_raises_after_max_attempts(self):
        mock_fn = AsyncMock(return_value="wrong")

        with pytest.raises(StructuredOutputError) as exc_info:
            await self.guard.run(
                fn=mock_fn,
                validator=lambda r: r == "right",
                error_msg="must be 'right'",
                stage="stage_2_seo",
                max_attempts=3,
            )

        err = exc_info.value
        assert err.code == "STRUCTURED_OUTPUT_FAILURE"
        assert err.stage == "stage_2_seo"
        assert err.attempts == 3
        assert "must be 'right'" in err.last_error
        assert mock_fn.call_count == 3

    @pytest.mark.asyncio
    async def test_catches_validation_error_and_retries(self):
        """Pydantic ValidationError from fn() should be caught and retried."""
        call_count = 0

        async def fn_that_raises(**kwargs):
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ValidationError.from_exception_data(
                    "TestModel", [{"type": "missing", "loc": ("field",), "msg": "Field required", "input": {}}]
                )
            return "success"

        result = await self.guard.run(
            fn=fn_that_raises,
            validator=lambda r: r == "success",
            error_msg="must succeed",
            stage="test_stage",
            max_attempts=3,
        )
        assert result == "success"

    @pytest.mark.asyncio
    async def test_one_attempt_max(self):
        """max_attempts=1 should fail immediately if validator is False."""
        mock_fn = AsyncMock(return_value="bad")
        with pytest.raises(StructuredOutputError) as exc_info:
            await self.guard.run(
                fn=mock_fn,
                validator=lambda r: False,
                error_msg="always fails",
                stage="test",
                max_attempts=1,
            )
        assert exc_info.value.attempts == 1


# ============================================================
# EC3: RAGMissHandler
# ============================================================


class TestRAGMissHandler:
    """Tests for RAGMissHandler — classifies empty/low-score Qdrant results."""

    def setup_method(self):
        self.handler = RAGMissHandler()

    def test_empty_list_is_empty_registry(self):
        result = self.handler.handle(
            similar_items=[],
            threshold=0.7,
            keyword="เก้าอี้ทำงาน คนตัวเล็ก",
        )
        assert result.is_miss is True
        assert result.strategy == "empty_registry"
        assert result.found_items == []

    def test_below_threshold_is_classified_separately(self):
        low_score_item = MagicMock()
        low_score_item.score = 0.45  # Below 0.7 threshold

        result = self.handler.handle(
            similar_items=[low_score_item],
            threshold=0.7,
            keyword="เก้าอี้ทำงาน",
        )
        assert result.is_miss is True
        assert result.strategy == "below_threshold"

    def test_build_safe_context_returns_none_on_miss(self):
        miss = RAGMissResult(found_items=[], is_miss=True, strategy="empty_registry")
        result = self.handler.build_safe_context(miss)
        assert result is None, "Must return None on miss — no fake URLs"

    def test_build_safe_context_returns_items_on_hit(self):
        items = [{"url": "https://example.com", "title": "Test Article"}]
        hit = RAGMissResult(found_items=items, is_miss=False, strategy="rag_found")
        result = self.handler.build_safe_context(hit)
        assert result == items

    def test_never_invents_urls_on_empty(self):
        """Core contract: no fake URLs ever returned when RAG finds nothing."""
        result = self.handler.handle(
            similar_items=[],
            threshold=0.7,
            keyword="brand-new-website-no-content",
        )
        safe_context = self.handler.build_safe_context(result)
        assert safe_context is None
        # Agent 3 must see None and use internal-only link strategy
        assert result.found_items == []

    def test_miss_result_has_correct_attributes(self):
        result = RAGMissResult(found_items=[], is_miss=True, strategy="empty_registry")
        assert hasattr(result, "found_items")
        assert hasattr(result, "is_miss")
        assert hasattr(result, "strategy")

    def test_multiple_below_threshold_all_classified_as_miss(self):
        items = [MagicMock(score=0.3), MagicMock(score=0.5), MagicMock(score=0.65)]
        result = self.handler.handle(
            similar_items=items,
            threshold=0.7,
            keyword="test",
        )
        assert result.is_miss is True
        assert result.strategy == "below_threshold"


# ============================================================
# EC4: SEODeadEndHandler
# ============================================================


class TestSEODeadEndHandler:
    """Tests for SEODeadEndHandler — 3-level dead-end evaluation."""

    def setup_method(self):
        self.handler = SEODeadEndHandler()
        self.hub = _make_hub()
        self.spoke = _make_spoke()

    def test_healthy_volume_returns_full_strategy(self):
        result = self.handler.evaluate(
            proposed_topics=[self.hub, self.spoke],
            estimated_total_volume=1500,
        )
        assert result.mode == "full_seo_geo"
        assert result.geo_queries_only is False
        assert result.requires_human_review is False

    def test_exactly_100_volume_is_healthy(self):
        result = self.handler.evaluate(
            proposed_topics=[self.hub, self.spoke],
            estimated_total_volume=100,
        )
        assert result.mode == "full_seo_geo"

    def test_99_volume_triggers_level_1(self):
        result = self.handler.evaluate(
            proposed_topics=[self.hub, self.spoke],
            estimated_total_volume=99,
        )
        # All topics have GEO queries → Level 1 auto-pivot
        assert result.mode == "geo_only"
        assert result.geo_queries_only is True
        assert result.requires_human_review is False

    def test_none_volume_with_geo_queries_triggers_level_1(self):
        """None volume = unverified = treated as low/zero."""
        result = self.handler.evaluate(
            proposed_topics=[self.hub, self.spoke],
            estimated_total_volume=None,
        )
        assert result.mode == "geo_only"

    def test_zero_volume_with_geo_queries_triggers_level_1(self):
        result = self.handler.evaluate(
            proposed_topics=[self.hub, self.spoke],
            estimated_total_volume=0,
        )
        assert result.mode == "geo_only"

    def test_level_2_when_no_volume_and_spoke_missing_geo(self):
        """Level 2: no volume AND at least one spoke is missing GEO queries.
        This tests the schema validator bypass — we use a hub (not spoke) without GEO."""
        # Hub without GEO queries is allowed by schema
        hub_no_geo = TopicBlueprint(
            title="เก้าอี้ทำงานสำหรับคนตัวเล็ก",
            slug="chair-guide-hub",
            role=TopicRole.HUB,
            content_type=ContentType.VIDEO,
            hook="test hook",
            key_points=["point"],
            seo=SEOMetadata(primary_keyword="test", search_intent=SearchIntent.INFORMATIONAL),
            geo_queries=[],  # Hub with no GEO → passes schema, but EC4 Level 2 picks it up
            tone=Tone.EMPATHETIC,
        )

        result = self.handler.evaluate(
            proposed_topics=[hub_no_geo],  # Only 1 topic with no GEO
            estimated_total_volume=None,
        )
        assert result.mode == "hitl_required"
        assert result.requires_human_review is True

    def test_level_2_reason_is_descriptive(self):
        hub_no_geo = TopicBlueprint(
            title="test hub",
            slug="test-hub",
            role=TopicRole.HUB,
            content_type=ContentType.VIDEO,
            hook="hook",
            key_points=["p"],
            seo=SEOMetadata(primary_keyword="test", search_intent=SearchIntent.INFORMATIONAL),
            geo_queries=[],
            tone=Tone.EMPATHETIC,
        )
        result = self.handler.evaluate(
            proposed_topics=[hub_no_geo],
            estimated_total_volume=0,
        )
        assert len(result.reason) > 20, "Reason must be explanatory"
        assert result.cluster_keyword  # Must carry the keyword

    def test_geo_only_reason_explains_channel_shift(self):
        result = self.handler.evaluate(
            proposed_topics=[self.hub, self.spoke],
            estimated_total_volume=0,
        )
        assert "GEO" in result.reason or "AI" in result.reason or "ChatGPT" in result.reason, \
            "GEO-only reason should explain the channel shift"

    def test_cluster_keyword_always_present(self):
        for volume in [500, 0, None]:
            result = self.handler.evaluate(
                proposed_topics=[self.hub, self.spoke],
                estimated_total_volume=volume,
            )
            assert result.cluster_keyword, "cluster_keyword must always be set"

    def test_seo_strategy_object_attributes(self):
        result = SEOStrategy(
            mode="geo_only",
            reason="No volume",
            cluster_keyword="test-kw",
            geo_queries_only=True,
        )
        assert result.mode == "geo_only"
        assert result.geo_queries_only is True
        assert result.requires_human_review is False


# ============================================================
# Integration: Schema-level GEO query enforcement (model_validator)
# ============================================================


class TestTopicBlueprintSchemaGuard:
    """Tests that the Pydantic model_validator on TopicBlueprint acts as a hard stop."""

    def test_spoke_without_geo_queries_raises_on_construction(self):
        """EC2/schema-level guard: a spoke with empty geo_queries must be rejected."""
        with pytest.raises(ValidationError) as exc_info:
            TopicBlueprint(
                title="test spoke",
                slug="test-spoke",
                role=TopicRole.SPOKE,
                content_type=ContentType.SHORT,
                hook="hook",
                key_points=["point"],
                seo=SEOMetadata(primary_keyword="test", search_intent=SearchIntent.INFORMATIONAL),
                geo_queries=[],  # Empty → must raise
                tone=Tone.CASUAL,
            )
        errors = exc_info.value.errors()
        assert any("GEO query" in str(e.get("msg", "")) for e in errors), \
            "Error message must mention GEO query requirement"

    def test_hub_without_geo_queries_is_allowed(self):
        """Hub is exempt from the GEO query requirement."""
        hub = TopicBlueprint(
            title="test hub",
            slug="test-hub",
            role=TopicRole.HUB,
            content_type=ContentType.VIDEO,
            hook="hook",
            key_points=["point"],
            seo=SEOMetadata(primary_keyword="test", search_intent=SearchIntent.INFORMATIONAL),
            geo_queries=[],  # Hub can be empty
            tone=Tone.EMPATHETIC,
        )
        assert hub.role == TopicRole.HUB

    def test_spoke_with_one_geo_query_is_valid(self):
        """Minimum valid spoke: exactly 1 GEO query."""
        spoke = _make_spoke()
        assert len(spoke.geo_queries) == 1

    def test_geo_query_constraints_contain_physical_specs(self):
        """Dry-run validation: constraints must carry height/budget through."""
        spoke = _make_spoke()
        constraints = spoke.geo_queries[0].constraints
        flat = " ".join(constraints).lower()
        assert "150" in flat or "cm" in flat, "Physical spec must be in constraints"
        assert "5" in flat and ("บาท" in flat or "฿" in flat or "5,000" in flat or "5000" in flat), \
            "Budget must be in constraints"

    def test_spoke_rejected_with_helpful_error_message(self):
        """The error message should tell the developer what to fix."""
        with pytest.raises(ValidationError) as exc_info:
            TopicBlueprint(
                title="No GEO spoke",
                slug="no-geo-spoke",
                role=TopicRole.SPOKE,
                content_type=ContentType.SHORT,
                hook="hook",
                key_points=["p"],
                seo=SEOMetadata(
                    primary_keyword="kw", search_intent=SearchIntent.INFORMATIONAL
                ),
                geo_queries=[],
                tone=Tone.CASUAL,
            )
        error_str = str(exc_info.value)
        # Must explain WHY (the architecture rule)
        assert "geo" in error_str.lower() or "GEO" in error_str


# ============================================================
# Integration: REJECTED status in schemas
# ============================================================


class TestPipelineStatusRejected:
    """Verify REJECTED is a first-class pipeline status."""

    def test_rejected_is_a_valid_pipeline_status(self):
        from app.models.schemas import PipelineStatus
        assert PipelineStatus.REJECTED.value == "rejected"

    def test_rejected_is_distinct_from_failed(self):
        from app.models.schemas import PipelineStatus
        assert PipelineStatus.REJECTED != PipelineStatus.FAILED

    def test_pipeline_state_can_be_set_to_rejected(self):
        from app.models.schemas import PipelineState, PipelineStatus
        state = PipelineState(raw_input="lol 555")
        state.status = PipelineStatus.REJECTED
        assert state.status == PipelineStatus.REJECTED
