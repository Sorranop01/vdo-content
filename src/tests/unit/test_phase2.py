"""
Unit Tests for Phase 2 Modules
VDO Content V2
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path


# ============ LLM Config Tests ============

class TestLLMConfig:
    """Tests for llm_config module"""
    
    def test_provider_types(self):
        from core.llm_config import LLM_PROVIDERS
        
        assert "deepseek" in LLM_PROVIDERS
        assert "openai" in LLM_PROVIDERS
        assert "gemini" in LLM_PROVIDERS
        assert "claude" in LLM_PROVIDERS
    
    def test_get_provider(self):
        from core.llm_config import get_provider
        
        provider = get_provider("deepseek")
        assert provider.name == "DeepSeek"
        assert len(provider.models) > 0
    
    def test_invalid_provider(self):
        from core.llm_config import get_provider
        
        with pytest.raises(ValueError):
            get_provider("invalid_provider")
    
    def test_provider_choices(self):
        from core.llm_config import get_provider_choices
        
        choices = get_provider_choices()
        assert len(choices) == 4
        assert all(isinstance(c, tuple) for c in choices)


# ============ LLM Router Tests ============

class TestLLMRouter:
    """Tests for llm_router module"""
    
    def test_router_init(self):
        from core.llm_router import LLMRouter
        
        router = LLMRouter()
        assert router.default_provider == "deepseek"
    
    def test_router_context_manager(self):
        from core.llm_router import LLMRouter
        
        with LLMRouter() as router:
            assert router is not None
    
    @patch('httpx.Client.post')
    def test_openai_compatible_call(self, mock_post):
        from core.llm_router import LLMRouter
        
        # Mock response
        mock_post.return_value = Mock(
            json=lambda: {
                "choices": [{"message": {"content": "Hello"}, "finish_reason": "stop"}],
                "usage": {"total_tokens": 10}
            },
            raise_for_status=lambda: None
        )
        
        # Set env var for test
        import os
        os.environ["DEEPSEEK_API_KEY"] = "test_key"
        
        router = LLMRouter()
        response = router.chat(
            messages=[{"role": "user", "content": "Hi"}],
            provider="deepseek"
        )
        
        assert response.content == "Hello"
        assert response.provider == "DeepSeek"


# ============ Prompt Scorer Tests ============

class TestPromptScorer:
    """Tests for prompt_scorer module"""
    
    def test_score_basic_prompt(self):
        from core.prompt_scorer import PromptScorer
        
        scorer = PromptScorer(use_ai=False)
        score = scorer.score("A person walking")
        
        assert 0 <= score.total_score <= 100
        assert score.grade in ["A", "B", "C", "D", "F"]
    
    def test_score_detailed_prompt(self):
        from core.prompt_scorer import PromptScorer
        
        good_prompt = """Cinematic wide shot of a young woman walking through 
        a golden wheat field at sunset. Soft natural lighting, warm amber tones. 
        Camera slowly pans to follow her movement. 4K HDR quality."""
        
        scorer = PromptScorer(use_ai=False)
        score = scorer.score(good_prompt)
        
        # Detailed prompts should score higher
        assert score.total_score > 50
    
    def test_score_vague_prompt(self):
        from core.prompt_scorer import PromptScorer
        
        bad_prompt = "maybe something like a person doing stuff etc"
        
        scorer = PromptScorer(use_ai=False)
        score = scorer.score(bad_prompt)
        
        # Vague prompts should score lower
        assert score.total_score < 50
        assert len(score.suggestions) > 0
    
    def test_get_score_emoji(self):
        from core.prompt_scorer import get_score_emoji
        
        assert get_score_emoji(85) == "🟢"
        assert get_score_emoji(65) == "🟡"
        assert get_score_emoji(45) == "🟠"
        assert get_score_emoji(30) == "🔴"


# ============ Template Manager Tests ============

class TestTemplateManager:
    """Tests for templates module"""
    
    def test_list_templates(self):
        from core.templates import TemplateManager
        
        manager = TemplateManager()
        templates = manager.list_templates()
        
        assert len(templates) >= 5  # At least 5 built-in
    
    def test_get_builtin_template(self):
        from core.templates import TemplateManager
        
        manager = TemplateManager()
        template = manager.get_template("news-short")
        
        assert template is not None
        assert template.name == "ข่าวสั้น (News Short)"
        assert template.is_builtin
    
    def test_filter_by_category(self):
        from core.templates import TemplateManager
        
        manager = TemplateManager()
        tutorials = manager.list_templates(category="tutorial")
        
        assert all(t.category == "tutorial" for t in tutorials)
    
    def test_apply_template(self):
        from core.templates import TemplateManager
        
        manager = TemplateManager()
        project = manager.apply_template("news-short", "Breaking News Test")
        
        assert project.title == "Breaking News Test"
        assert len(project.scenes) == 4  # news-short has 4 scenes
    
    def test_get_categories(self):
        from core.templates import TemplateManager
        
        manager = TemplateManager()
        categories = manager.get_categories()
        
        assert len(categories) >= 7
        assert all(isinstance(c, tuple) for c in categories)


# ============ Voice Preview Tests ============

class TestVoicePreview:
    """Tests for voice_preview module"""
    
    def test_init_creates_cache_dir(self, tmp_path):
        from core.voice_preview import VoicePreview
        
        cache_dir = tmp_path / "voice_cache"
        preview = VoicePreview(cache_dir=str(cache_dir))
        
        assert cache_dir.exists()
    
    def test_list_thai_voices(self):
        from core.voice_preview import VoicePreview, THAI_VOICES
        
        preview = VoicePreview()
        voices = preview.list_voices("th")
        
        assert len(voices) > 0
        assert all(v.language == "th-TH" for v in voices)
    
    def test_cache_key_generation(self):
        from core.voice_preview import VoicePreview
        
        preview = VoicePreview()
        key1 = preview.get_cache_key("Hello", "voice1")
        key2 = preview.get_cache_key("Hello", "voice2")
        key3 = preview.get_cache_key("Hello", "voice1")
        
        assert key1 != key2
        assert key1 == key3
