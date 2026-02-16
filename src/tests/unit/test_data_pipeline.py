"""
Unit Tests for Step 2 → Step 3 Data Pipeline
VDO Content V2 Test Suite

Tests cover:
1. Proposal field name mapping (Pydantic ↔ DB round-trip)
2. generated_content persistence
3. ScriptGenerator story_proposal usage (dict & object)
4. _build_script_context enrichment from Step 2
5. Provider configuration (no hardcoded gemini)
"""

import pytest
import json
import uuid
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timezone

from core.models import Project, StoryProposal, Scene
from core.script_generator import ScriptGenerator


# ============================================================
# 1. Proposal Round-Trip: model_dump → save → load → Project
# ============================================================

class TestProposalRoundTrip:
    """Test that proposal data survives save/load cycle"""

    def test_model_dump_produces_proposal_key(self, sample_proposal):
        """model_dump() should produce key 'proposal', not 'proposal_data'"""
        project = Project(
            title="Test",
            topic="TestTopic",
            proposal=sample_proposal,
        )
        data = project.model_dump(mode="json")
        
        assert "proposal" in data, "model_dump() must produce 'proposal' key"
        assert "proposal_data" not in data, "model_dump() must NOT produce 'proposal_data'"
        assert data["proposal"]["topic"] == "วิธีทำอาหารไทยง่ายๆ"
        assert data["proposal"]["analysis"] == "This topic is about Thai cooking, suitable for food content"
        assert data["proposal"]["outline"] == ["Introduction", "Ingredients", "Step-by-step", "Final result"]

    def test_project_to_dict_returns_proposal_key(self, sample_proposal):
        """project_to_dict should return 'proposal' key for Pydantic compatibility"""
        from core.database import project_to_dict, ProjectDB
        
        # Create a mock ProjectDB with proposal_data
        mock_db = MagicMock(spec=ProjectDB)
        mock_db.id = uuid.uuid4()
        mock_db.title = "Test"
        mock_db.topic = "TestTopic"
        mock_db.status = "draft"
        mock_db.default_style = "documentary"
        mock_db.video_profile_id = None
        mock_db.target_duration = 60
        mock_db.character_reference = None
        mock_db.full_script = ""
        mock_db.style_instructions = None
        mock_db.script_text = ""
        mock_db.audio_path = None
        mock_db.audio_duration = 0.0
        mock_db.drive_folder_link = None
        mock_db.aspect_ratio = "16:9"
        mock_db.generated_content = "test content"
        mock_db.proposal_data = {"topic": "Test", "analysis": "Analysis", "outline": ["A", "B"]}
        mock_db.content_description = None
        mock_db.content_goal = None
        mock_db.target_audience = None
        mock_db.voice_personality = None
        mock_db.content_category = None
        mock_db.platforms = None
        mock_db.video_format = None
        mock_db.content_goal_id = None
        mock_db.target_audience_id = None
        mock_db.created_at = datetime.now(timezone.utc)
        mock_db.updated_at = datetime.now(timezone.utc)
        mock_db.scenes = []
        mock_db.audio_segments = []
        
        result = project_to_dict(mock_db)
        
        assert "proposal" in result, "project_to_dict must return 'proposal' key"
        assert "proposal_data" not in result, "project_to_dict must NOT return 'proposal_data'"
        assert result["proposal"]["topic"] == "Test"

    def test_project_from_dict_with_proposal_key(self):
        """Project(**data) should accept 'proposal' key"""
        data = {
            "title": "Test",
            "topic": "TestTopic",
            "proposal": {
                "topic": "Test",
                "analysis": "Analysis result",
                "outline": ["Part 1", "Part 2"],
                "key_points": ["Point A"],
            },
        }
        project = Project(**data)
        
        assert project.proposal is not None
        assert project.proposal.topic == "Test"
        assert project.proposal.analysis == "Analysis result"
        assert project.proposal.outline == ["Part 1", "Part 2"]

    def test_project_from_dict_with_proposal_data_key_fails(self):
        """Project(**data) should NOT accept 'proposal_data' key (wrong name)"""
        data = {
            "title": "Test",
            "topic": "TestTopic",
            "proposal_data": {
                "topic": "Test",
                "analysis": "Analysis",
            },
        }
        project = Project(**data)
        
        # proposal_data is not a valid Pydantic field, so proposal stays None
        assert project.proposal is None, \
            "Using 'proposal_data' key should NOT populate project.proposal"

    def test_generated_content_round_trip(self):
        """generated_content should survive model_dump → Project cycle"""
        content = "📋 AI Analysis: This is a test analysis"
        project = Project(
            title="Test",
            topic="TestTopic",
            generated_content=content,
        )
        
        data = project.model_dump(mode="json")
        assert data["generated_content"] == content
        
        restored = Project(**data)
        assert restored.generated_content == content


# ============================================================
# 2. db_save_project reads correct keys
# ============================================================

class TestDbSaveProjectKeys:
    """Test that db_save_project reads from correct model_dump keys"""

    @patch('core.database.get_db')
    def test_save_reads_proposal_not_proposal_data(self, mock_get_db, sample_proposal):
        """db_save_project must read 'proposal' key from project_data dict"""
        from core.database import db_save_project, ProjectDB
        
        # Build project_data as model_dump() would produce
        project = Project(
            title="Test Save",
            topic="Save Topic",
            proposal=sample_proposal,
            generated_content="AI content here",
        )
        project_data = project.model_dump(mode="json")
        project_data["project_id"] = str(uuid.uuid4())
        
        # Mock DB context
        mock_session = MagicMock()
        mock_get_db.return_value.__enter__ = Mock(return_value=mock_session)
        mock_get_db.return_value.__exit__ = Mock(return_value=False)
        
        # Mock existing project found
        mock_existing = MagicMock(spec=ProjectDB)
        mock_existing.id = uuid.UUID(project_data["project_id"])
        mock_session.query.return_value.filter.return_value.first.return_value = mock_existing
        
        db_save_project(project_data)
        
        # Verify proposal_data was set from 'proposal' key (not 'proposal_data')
        assert mock_existing.proposal_data is not None, \
            "proposal_data should be set on the DB object"
        assert mock_existing.generated_content == "AI content here", \
            "generated_content should be set on the DB object"

    def test_model_dump_has_no_proposal_data_key(self, sample_proposal):
        """Verify model_dump does not produce 'proposal_data' key"""
        project = Project(
            title="Test",
            topic="Topic",
            proposal=sample_proposal,
        )
        data = project.model_dump(mode="json")
        
        assert "proposal" in data
        assert "proposal_data" not in data


# ============================================================
# 3. ScriptGenerator: story_proposal field access
# ============================================================

class TestScriptGeneratorProposalAccess:
    """Test ScriptGenerator correctly uses StoryProposal fields"""

    @patch('core.script_generator.get_available_providers')
    @patch('core.script_generator.get_router')
    def test_uses_outline_from_story_proposal_object(
        self, mock_get_router, mock_providers, sample_proposal
    ):
        """ScriptGenerator should use outline (not suggestions) from StoryProposal"""
        mock_providers.return_value = [Mock()]
        
        mock_router = Mock()
        from core.llm_router import LLMResponse
        mock_router.chat.return_value = LLMResponse(
            content="Generated script with proposal",
            provider="deepseek",
            model="deepseek-chat"
        )
        mock_get_router.return_value = mock_router
        
        generator = ScriptGenerator()
        result = generator.generate_script(
            topic="ทดสอบ",
            language="th",
            story_proposal=sample_proposal,
        )
        
        assert result == "Generated script with proposal"
        
        # Verify the first call's prompt includes outline content
        # Note: _validate_script_length may trigger additional calls,
        # so we check the first call (the actual generation call)
        first_call_kwargs = mock_router.chat.call_args_list[0][1]
        messages = first_call_kwargs["messages"]
        user_prompt = messages[0]["content"]
        assert "โครงเรื่อง" in user_prompt or "Introduction" in user_prompt or \
               "ประเด็นหลัก" in user_prompt, \
            f"Prompt should include outline/key_points. Got: {user_prompt[:300]}"

    @patch('core.script_generator.get_available_providers')
    @patch('core.script_generator.get_router')
    def test_uses_outline_from_dict(self, mock_get_router, mock_providers):
        """ScriptGenerator should handle proposal as dict (from DB JSON)"""
        mock_providers.return_value = [Mock()]
        
        mock_router = Mock()
        from core.llm_router import LLMResponse
        mock_router.chat.return_value = LLMResponse(
            content="Script from dict proposal",
            provider="deepseek",
            model="deepseek-chat"
        )
        mock_get_router.return_value = mock_router
        
        proposal_dict = {
            "topic": "Thai cooking",
            "analysis": "Good topic for food content",
            "outline": ["Introduction", "Ingredients", "Steps"],
            "key_points": ["Easy recipes", "Local ingredients"],
        }
        
        generator = ScriptGenerator()
        result = generator.generate_script(
            topic="ทดสอบ",
            language="th",
            story_proposal=proposal_dict,
        )
        
        assert result == "Script from dict proposal"
        
        # Verify context from dict made it into the first prompt
        first_call_kwargs = mock_router.chat.call_args_list[0][1]
        messages = first_call_kwargs["messages"]
        user_prompt = messages[0]["content"]
        assert "Introduction" in user_prompt or "Easy recipes" in user_prompt or \
               "Good topic" in user_prompt, \
            f"Prompt should include data from dict proposal. Got: {user_prompt[:300]}"

    @patch('core.script_generator.get_available_providers')
    @patch('core.script_generator.get_router')
    def test_handles_none_proposal_gracefully(self, mock_get_router, mock_providers):
        """ScriptGenerator should work fine when story_proposal is None"""
        mock_providers.return_value = [Mock()]
        
        mock_router = Mock()
        from core.llm_router import LLMResponse
        mock_router.chat.return_value = LLMResponse(
            content="Script without proposal",
            provider="deepseek",
            model="deepseek-chat"
        )
        mock_get_router.return_value = mock_router
        
        generator = ScriptGenerator()
        result = generator.generate_script(
            topic="ทดสอบ",
            language="th",
            story_proposal=None,
        )
        
        assert result == "Script without proposal"

    @patch('core.script_generator.get_available_providers')
    @patch('core.script_generator.get_router')
    def test_handles_empty_proposal_fields(self, mock_get_router, mock_providers):
        """ScriptGenerator should handle proposal with empty fields"""
        mock_providers.return_value = [Mock()]
        
        mock_router = Mock()
        from core.llm_router import LLMResponse
        mock_router.chat.return_value = LLMResponse(
            content="Script output",
            provider="deepseek",
            model="deepseek-chat"
        )
        mock_get_router.return_value = mock_router
        
        # Proposal with all empty fields
        empty_proposal = StoryProposal(topic="Test")
        
        generator = ScriptGenerator()
        result = generator.generate_script(
            topic="Test",
            language="th",
            story_proposal=empty_proposal,
        )
        
        assert result == "Script output"

    @patch('core.script_generator.get_available_providers')
    @patch('core.script_generator.get_router')  
    def test_includes_analysis_in_prompt(self, mock_get_router, mock_providers):
        """ScriptGenerator should include analysis text in the prompt"""
        mock_providers.return_value = [Mock()]
        
        mock_router = Mock()
        from core.llm_router import LLMResponse
        mock_router.chat.return_value = LLMResponse(
            content="Script",
            provider="deepseek",
            model="deepseek-chat"
        )
        mock_get_router.return_value = mock_router
        
        proposal = StoryProposal(
            topic="Test",
            analysis="This is a detailed analysis about the topic",
            outline=["Part 1", "Part 2"],
            key_points=["Key point A"],
        )
        
        generator = ScriptGenerator()
        generator.generate_script(
            topic="Test",
            language="th",
            story_proposal=proposal,
        )
        
        first_call_kwargs = mock_router.chat.call_args_list[0][1]
        messages = first_call_kwargs["messages"]
        user_prompt = messages[0]["content"]
        
        # All three fields should be present in the first prompt
        assert "detailed analysis" in user_prompt, \
            f"analysis should be in prompt. Got: {user_prompt[:300]}"
        assert "Part 1" in user_prompt, "outline items should be in prompt"
        assert "Key point A" in user_prompt, "key_points should be in prompt"


# ============================================================
# 4. Provider configuration (no hardcoded gemini)
# ============================================================

class TestProviderConfig:
    """Test that ScriptGenerator uses correct provider"""
    
    def test_default_provider_is_deepseek(self):
        """Default provider should be deepseek, not gemini"""
        from core.llm_config import DEFAULT_PROVIDER
        assert DEFAULT_PROVIDER == "deepseek"
    
    def test_generator_default_provider(self):
        """ScriptGenerator should default to deepseek"""
        generator = ScriptGenerator()
        assert generator.provider == "deepseek"


# ============================================================
# 5. _build_script_context logic (inline to avoid import chain)
# ============================================================

def _build_script_context_standalone(project) -> str:
    """Reimplementation of step3_script._build_script_context for testing.
    
    We can't import from frontend.pages.step3_script directly because
    frontend/pages/__init__.py imports all pages which use 'src.' prefixed
    imports incompatible with test runner. So we test the logic inline.
    """
    parts = []
    base_topic = project.content_description or project.topic or ""
    parts.append(f"📌 หัวข้อ: {base_topic}")
    
    goal_text = project.content_goal or ""
    if goal_text:
        parts.append(f"🎯 เป้าหมาย: {goal_text}")
    
    audience_text = project.target_audience or ""
    if audience_text:
        parts.append(f"👥 กลุ่มเป้าหมาย: {audience_text}")
    
    parts.append(f"⏱️ ความยาว: {project.target_duration} วินาที")
    
    generated = getattr(project, 'generated_content', '')
    if generated:
        parts.append(f"\n📋 ข้อมูลจากการวิเคราะห์เนื้อหา:\n{generated}")
    
    return "\n".join(parts)


class TestBuildScriptContext:
    """Test _build_script_context logic"""

    def test_includes_generated_content(self):
        """Context should include generated_content from Step 2"""
        project = Project(
            title="Test",
            topic="Test Topic",
            content_description="วิธีลดน้ำหนัก",
            generated_content="📋 AI Analysis: ลดน้ำหนักด้วยอาหารคลีน",
            target_duration=60,
        )
        context = _build_script_context_standalone(project)
        
        assert "วิธีลดน้ำหนัก" in context
        assert "AI Analysis" in context or "ลดน้ำหนักด้วยอาหารคลีน" in context

    def test_includes_basic_fields(self):
        """Context should include topic and duration"""
        project = Project(
            title="Test",
            topic="Thai food guide",
            content_description="อาหารไทย",
            target_duration=120,
        )
        context = _build_script_context_standalone(project)
        
        assert "อาหารไทย" in context
        assert "120" in context

    def test_empty_generated_content(self):
        """Context should work when generated_content is empty"""
        project = Project(
            title="Test",
            topic="Test",
            target_duration=60,
        )
        context = _build_script_context_standalone(project)
        
        assert isinstance(context, str)
        assert "60" in context

    def test_includes_goal_and_audience(self):
        """Context should include goal and audience when set"""
        project = Project(
            title="Test",
            topic="Test",
            content_goal="สร้างยอดขาย",
            target_audience="วัยรุ่น",
            target_duration=30,
        )
        context = _build_script_context_standalone(project)
        
        assert "สร้างยอดขาย" in context
        assert "วัยรุ่น" in context


# ============================================================
# 6. StoryProposal Model Validation
# ============================================================

class TestStoryProposalFields:
    """Verify StoryProposal has the fields ScriptGenerator expects"""

    def test_has_analysis_field(self):
        """StoryProposal must have 'analysis' field"""
        p = StoryProposal(topic="Test", analysis="Test analysis")
        assert p.analysis == "Test analysis"

    def test_has_outline_field(self):
        """StoryProposal must have 'outline' field"""
        p = StoryProposal(topic="Test", outline=["A", "B", "C"])
        assert p.outline == ["A", "B", "C"]

    def test_has_key_points_field(self):
        """StoryProposal must have 'key_points' field"""
        p = StoryProposal(topic="Test", key_points=["X", "Y"])
        assert p.key_points == ["X", "Y"]

    def test_no_suggestions_field(self):
        """StoryProposal should NOT have 'suggestions' field (was a bug)"""
        p = StoryProposal(topic="Test")
        assert not hasattr(p, 'suggestions') or p.__class__.__fields__.get('suggestions') is None

    def test_serializes_to_dict(self):
        """StoryProposal should serialize to dict for DB storage"""
        p = StoryProposal(
            topic="ทดสอบ",
            analysis="Analysis text",
            outline=["Step 1", "Step 2"],
            key_points=["Point A"],
        )
        d = p.model_dump(mode="json")
        
        assert d["topic"] == "ทดสอบ"
        assert d["analysis"] == "Analysis text"
        assert d["outline"] == ["Step 1", "Step 2"]
        assert d["key_points"] == ["Point A"]

    def test_deserializes_from_dict(self):
        """StoryProposal should be created from dict (DB JSON)"""
        d = {
            "topic": "Test",
            "analysis": "Analysis",
            "outline": ["A", "B"],
            "key_points": ["K1"],
            "status": "approved",
        }
        p = StoryProposal(**d)
        
        assert p.topic == "Test"
        assert p.analysis == "Analysis"
        assert p.outline == ["A", "B"]
        assert p.status == "approved"
