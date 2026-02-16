"""
Unit Tests for Script Generator
VDO Content V2 Test Suite

Uses mocking to avoid actual API calls
"""

import pytest
from unittest.mock import Mock, patch, MagicMock

from core.script_generator import ScriptGenerator, generate_script
from core.llm_router import LLMResponse


class TestScriptGeneratorInit:
    """Test ScriptGenerator initialization"""
    
    def test_default_initialization(self):
        """Test default values"""
        generator = ScriptGenerator()
        assert generator.provider == "deepseek"
        assert generator.model is None
    
    def test_custom_provider(self):
        """Test custom provider"""
        generator = ScriptGenerator(provider="openai")
        assert generator.provider == "openai"
    
    def test_custom_model(self):
        """Test custom model"""
        generator = ScriptGenerator(model="gpt-4o-mini")
        assert generator.model == "gpt-4o-mini"
    
    @patch.dict('os.environ', {'DEEPSEEK_API_KEY': 'test-key'})
    def test_legacy_api_key_support(self):
        """Test legacy API key sets env var"""
        generator = ScriptGenerator(api_key="legacy-key", provider="deepseek")
        import os
        assert os.environ.get("DEEPSEEK_API_KEY") == "legacy-key"


class TestScriptGeneratorIsAvailable:
    """Test is_available method"""
    
    @patch('core.script_generator.get_available_providers')
    def test_available_when_providers_exist(self, mock_get):
        """Test returns True when providers exist"""
        mock_get.return_value = [Mock()]
        generator = ScriptGenerator()
        assert generator.is_available() is True
    
    @patch('core.script_generator.get_available_providers')
    def test_unavailable_when_no_providers(self, mock_get):
        """Test returns False when no providers"""
        mock_get.return_value = []
        generator = ScriptGenerator()
        assert generator.is_available() is False


class TestScriptGeneratorSetProvider:
    """Test set_provider method"""
    
    def test_set_provider_updates_provider(self):
        """Test provider is updated"""
        generator = ScriptGenerator(provider="deepseek")
        generator.set_provider("openai")
        assert generator.provider == "openai"
    
    def test_set_provider_with_model(self):
        """Test provider and model are updated"""
        generator = ScriptGenerator()
        generator.set_provider("openai", model="gpt-4o")
        assert generator.provider == "openai"
        assert generator.model == "gpt-4o"


class TestScriptGeneratorGenerateScript:
    """Test generate_script method"""
    
    @patch('core.script_generator.get_available_providers')
    def test_raises_when_unavailable(self, mock_get):
        """Test raises error when no provider available"""
        mock_get.return_value = []
        generator = ScriptGenerator()
        
        with pytest.raises(RuntimeError, match="No LLM provider configured"):
            generator.generate_script("Test topic")
    
    @patch('core.script_generator.get_available_providers')
    @patch('core.script_generator.get_router')
    def test_generates_thai_script(self, mock_get_router, mock_providers):
        """Test Thai script generation"""
        mock_providers.return_value = [Mock()]
        
        mock_router = Mock()
        mock_router.chat.return_value = LLMResponse(
            content="นี่คือบทพากย์ทดสอบ",
            provider="deepseek",
            model="deepseek-chat"
        )
        mock_get_router.return_value = mock_router
        
        generator = ScriptGenerator()
        result = generator.generate_script("หัวข้อทดสอบ", language="th")
        
        assert result == "นี่คือบทพากย์ทดสอบ"
        mock_router.chat.assert_called_once()
    
    @patch('core.script_generator.get_available_providers')
    @patch('core.script_generator.get_router')
    def test_generates_english_script(self, mock_get_router, mock_providers):
        """Test English script generation"""
        mock_providers.return_value = [Mock()]
        
        mock_router = Mock()
        mock_router.chat.return_value = LLMResponse(
            content="This is a test narration script.",
            provider="deepseek",
            model="deepseek-chat"
        )
        mock_get_router.return_value = mock_router
        
        generator = ScriptGenerator()
        result = generator.generate_script("Test topic", language="en")
        
        assert result == "This is a test narration script."
    
    @patch('core.script_generator.get_available_providers')
    @patch('core.script_generator.get_router')
    def test_uses_style_prompt(self, mock_get_router, mock_providers):
        """Test style is included in prompt"""
        mock_providers.return_value = [Mock()]
        
        mock_router = Mock()
        mock_router.chat.return_value = LLMResponse(
            content="Script content",
            provider="deepseek",
            model="deepseek-chat"
        )
        mock_get_router.return_value = mock_router
        
        generator = ScriptGenerator()
        generator.generate_script("Topic", style="storytelling")
        
        # Verify system prompt contains style hint
        call_kwargs = mock_router.chat.call_args[1]
        assert "system_prompt" in call_kwargs
    
    @patch('core.script_generator.get_available_providers')
    @patch('core.script_generator.get_router')
    def test_uses_provider_override(self, mock_get_router, mock_providers):
        """Test provider override is used"""
        mock_providers.return_value = [Mock()]
        
        mock_router = Mock()
        mock_router.chat.return_value = LLMResponse(
            content="Response",
            provider="openai",
            model="gpt-4"
        )
        mock_get_router.return_value = mock_router
        
        generator = ScriptGenerator(provider="deepseek")
        generator.generate_script("Topic", provider="openai")
        
        call_kwargs = mock_router.chat.call_args[1]
        assert call_kwargs["provider"] == "openai"
    
    @patch('core.script_generator.get_available_providers')
    @patch('core.script_generator.get_router')
    def test_respects_target_duration(self, mock_get_router, mock_providers):
        """Test target duration affects prompt"""
        mock_providers.return_value = [Mock()]
        
        mock_router = Mock()
        mock_router.chat.return_value = LLMResponse(
            content="Content",
            provider="deepseek",
            model="deepseek-chat"
        )
        mock_get_router.return_value = mock_router
        
        generator = ScriptGenerator()
        generator.generate_script("Topic", target_duration=120)
        
        # Should include length hint in system prompt
        call_kwargs = mock_router.chat.call_args[1]
        assert "system_prompt" in call_kwargs


class TestScriptGeneratorGenerateOutline:
    """Test generate_outline method"""
    
    @patch('core.script_generator.get_available_providers')
    def test_raises_when_unavailable(self, mock_get):
        """Test raises error when no provider available"""
        mock_get.return_value = []
        generator = ScriptGenerator()
        
        with pytest.raises(RuntimeError, match="No LLM provider configured"):
            generator.generate_outline("Test topic")
    
    @patch('core.script_generator.get_available_providers')
    @patch('core.script_generator.get_router')
    def test_generates_outline_points(self, mock_get_router, mock_providers):
        """Test outline generation returns list"""
        mock_providers.return_value = [Mock()]
        
        mock_router = Mock()
        mock_router.chat.return_value = LLMResponse(
            content="Point 1\nPoint 2\nPoint 3\nPoint 4\nPoint 5",
            provider="deepseek",
            model="deepseek-chat"
        )
        mock_get_router.return_value = mock_router
        
        generator = ScriptGenerator()
        result = generator.generate_outline("Test topic", num_points=5)
        
        assert isinstance(result, list)
        assert len(result) == 5
    
    @patch('core.script_generator.get_available_providers')
    @patch('core.script_generator.get_router')
    def test_limits_to_num_points(self, mock_get_router, mock_providers):
        """Test outline is limited to requested points"""
        mock_providers.return_value = [Mock()]
        
        mock_router = Mock()
        mock_router.chat.return_value = LLMResponse(
            content="Point 1\nPoint 2\nPoint 3\nPoint 4\nPoint 5\nPoint 6\nPoint 7",
            provider="deepseek",
            model="deepseek-chat"
        )
        mock_get_router.return_value = mock_router
        
        generator = ScriptGenerator()
        result = generator.generate_outline("Test topic", num_points=3)
        
        assert len(result) <= 3
    
    @patch('core.script_generator.get_available_providers')
    @patch('core.script_generator.get_router')
    def test_filters_empty_lines(self, mock_get_router, mock_providers):
        """Test empty lines are filtered out"""
        mock_providers.return_value = [Mock()]
        
        mock_router = Mock()
        mock_router.chat.return_value = LLMResponse(
            content="Point 1\n\nPoint 2\n\n\nPoint 3",
            provider="deepseek",
            model="deepseek-chat"
        )
        mock_get_router.return_value = mock_router
        
        generator = ScriptGenerator()
        result = generator.generate_outline("Test topic")
        
        assert "" not in result
        assert len(result) == 3


class TestConvenienceFunction:
    """Test module-level generate_script function"""
    
    @patch('core.script_generator.get_available_providers')
    @patch('core.script_generator.get_router')
    def test_generate_script_function(self, mock_get_router, mock_providers):
        """Test convenience function works"""
        mock_providers.return_value = [Mock()]
        
        mock_router = Mock()
        mock_router.chat.return_value = LLMResponse(
            content="Generated script",
            provider="deepseek",
            model="deepseek-chat"
        )
        mock_get_router.return_value = mock_router
        
        result = generate_script("Test topic")
        
        assert result == "Generated script"
    
    @patch('core.script_generator.get_available_providers')
    @patch('core.script_generator.get_router')
    def test_generate_script_with_kwargs(self, mock_get_router, mock_providers):
        """Test convenience function passes kwargs"""
        mock_providers.return_value = [Mock()]
        
        mock_router = Mock()
        mock_router.chat.return_value = LLMResponse(
            content="Script",
            provider="deepseek",
            model="deepseek-chat"
        )
        mock_get_router.return_value = mock_router
        
        result = generate_script(
            "Topic",
            provider="openai",
            style="tutorial",
            target_duration=90
        )
        
        assert result == "Script"
