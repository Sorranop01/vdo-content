"""
Tests for the Pydantic schemas — validates the API contract.
"""

from datetime import datetime

from app.models.schemas import (
    ContentBlueprintPayload,
    TopicBlueprint,
    SEOMetadata,
    GEOQuery,
    InternalLink,
    ContentType,
    SearchIntent,
    GEOIntent,
    TopicRole,
    LinkType,
    Tone,
    PipelineState,
    PipelineStatus,
    IntentExtractionOutput,
)


def test_content_blueprint_payload_creation():
    """Test that the master API contract can be instantiated and serialized."""
    hub = TopicBlueprint(
        title="เก้าอี้ทำงานสำหรับคนตัวเล็ก",
        slug="ergonomic-chair-petite-guide",
        role=TopicRole.HUB,
        content_type=ContentType.VIDEO,
        hook="คุณซื้อเก้าอี้ ergonomic แพงๆ แต่ยังปวดหลัง?",
        key_points=["Why standard chairs fail petite users", "The feet dangling problem"],
        target_duration_seconds=480,
        seo=SEOMetadata(
            primary_keyword="เก้าอี้ทำงาน คนตัวเล็ก",
            secondary_keywords=["ergonomic chair petite"],
            long_tail_keywords=["เก้าอี้ทำงานสำหรับคนสูง 150 ซม"],
            search_volume=1200,
            keyword_difficulty=34.5,
            search_intent=SearchIntent.INFORMATIONAL,
        ),
        geo_queries=[
            GEOQuery(
                query_text="I'm 150cm tall and my office chair gives me back pain",
                intent=GEOIntent.SOLUTION,
                constraints=["budget under 5000 THB", "height 150cm"],
                mandatory_elements=["seat depth adjustment", "footrest recommendation"],
            )
        ],
        tone=Tone.EMPATHETIC,
        cta="ดูรีวิวเก้าอี้ที่เราแนะนำ",
    )

    spoke = TopicBlueprint(
        title="5 สัญญาณว่าเก้าอี้ไม่เหมาะกับตัวคุณ",
        slug="5-signs-wrong-chair",
        role=TopicRole.SPOKE,
        content_type=ContentType.SHORT,
        hook="ถ้าเท้าคุณลอยตอนนั่ง...",
        key_points=["Feet dangling test", "Knee angle check"],
        target_duration_seconds=60,
        seo=SEOMetadata(
            primary_keyword="สัญญาณเก้าอี้ไม่เหมาะ",
            search_intent=SearchIntent.INFORMATIONAL,
        ),
        # REQUIRED: spokes must have ≥1 GEO query (architecture rule)
        geo_queries=[
            GEOQuery(
                query_text="ทำไมนั่งเก้าอี้ ergonomic แล้วยังปวดหลัง ทั้งที่ซื้อแพงมาก",
                intent=GEOIntent.SOLUTION,
                constraints=["height: 150cm", "budget: ฿5,000"],
                mandatory_elements=["seat height in cm", "footrest as fix"],
            )
        ],
        tone=Tone.CASUAL,
    )

    links = [
        InternalLink(
            from_topic_id=hub.topic_id,
            to_topic_id=spoke.topic_id,
            anchor_text="5 สัญญาณว่าเก้าอี้ของคุณไม่เหมาะ",
            link_type=LinkType.CONTEXTUAL,
        ),
        InternalLink(
            from_topic_id=spoke.topic_id,
            to_topic_id=hub.topic_id,
            anchor_text="อ่านไกด์ฉบับเต็ม",
            link_type=LinkType.CTA,
        ),
    ]

    payload = ContentBlueprintPayload(
        target_persona="Office worker, female, 150cm, back pain from expensive chair",
        core_pain_points=["Feet dangle", "Back pain", "Chair not sized for petite frame"],
        underlying_emotions=["frustration", "buyer's remorse"],
        hub=hub,
        spokes=[spoke],
        internal_links=links,
        cluster_primary_keyword="เก้าอี้ทำงาน คนตัวเล็ก",
        estimated_total_search_volume=2800,
        agent_model_used="gpt-4o",
        cannibalization_checked=True,
    )

    # Verify serialization
    json_str = payload.model_dump_json()
    assert json_str is not None
    assert len(json_str) > 100

    # Verify deserialization round-trip
    restored = ContentBlueprintPayload.model_validate_json(json_str)
    assert restored.blueprint_id == payload.blueprint_id
    assert restored.hub.title == "เก้าอี้ทำงานสำหรับคนตัวเล็ก"
    assert restored.hub.role == TopicRole.HUB
    assert len(restored.spokes) == 1
    assert len(restored.internal_links) == 2
    assert restored.cluster_primary_keyword == "เก้าอี้ทำงาน คนตัวเล็ก"
    # Verify the spoke's GEO constraint survived the round-trip
    assert "150cm" in restored.spokes[0].geo_queries[0].constraints[0]



def test_seo_metadata_optional_fields():
    """Verify that search_volume and keyword_difficulty are nullable (unverified)."""
    seo = SEOMetadata(
        primary_keyword="test keyword",
        search_intent=SearchIntent.COMMERCIAL,
    )
    assert seo.search_volume is None
    assert seo.keyword_difficulty is None
    assert seo.secondary_keywords == []


def test_pipeline_state_creation():
    """Test pipeline state initialization."""
    state = PipelineState(raw_input="test input text")
    assert state.status == PipelineStatus.PENDING
    assert state.intent is None
    assert state.blueprint is None
    assert state.run_id is not None


def test_intent_extraction_output():
    """Test Agent 1 output model."""
    output = IntentExtractionOutput(
        target_persona="Thai office worker, petite build",
        core_pain_points=["back pain", "chair too high"],
        underlying_emotions=["frustration"],
        raw_input_snippet="ซื้อเก้าอี้ 5000 แต่ยังปวดหลัง",
    )
    assert len(output.core_pain_points) == 2
    assert output.raw_input_snippet.startswith("ซื้อ")


def test_geo_query_model():
    """Test GEO query with constraints."""
    query = GEOQuery(
        query_text="best office chair for short people under 5000 baht",
        intent=GEOIntent.COMPARISON,
        constraints=["budget under 5000 THB", "height under 155cm"],
        mandatory_elements=["seat depth", "footrest", "lumbar height"],
    )
    assert query.intent == GEOIntent.COMPARISON
    assert len(query.constraints) == 2
    assert len(query.mandatory_elements) == 3
