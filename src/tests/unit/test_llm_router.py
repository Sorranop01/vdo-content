"""
Unit Tests for LLM Router
VDO Content V2 Test Suite

Uses mocking to avoid actual API calls
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from dataclasses import dataclass

from core.llm_router import (
    LLMRouter, 
    LLMResponse, 
    LLMRequest, 
    get_router, 
    quick_chat
)
from core.llm_config import (
    LLMProvider, 
    LLMModel, 
    get_provider, 
    get_available_providers,
    ProviderName
)


class TestLLMResponse:
    """Test LLMResponse dataclass"""
    
    def test_response_creation(self):
        """Test basic response creation"""
        response = LLMResponse(
            content="Hello world",
            provider="test",
            model="test-model"
        )
        assert response.content == "Hello world"
        assert response.provider == "test"
        assert response.model == "test-model"
    
    def test_response_defaults(self):
        """Test default values"""
        response = LLMResponse(
            content="Test",
            provider="test",
            model="test-model"
        )
        assert response.tokens_used == 0
        assert response.finish_reason == "stop"
    
    def test_response_with_all_fields(self):
        """Test response with all fields specified"""
        response = LLMResponse(
            content="Full response",
            provider="openai",
            model="gpt-4o",
            tokens_used=150,
            finish_reason="length"
        )
        assert response.tokens_used == 150
        assert response.finish_reason == "length"


class TestLLMRequest:
    """Test LLMRequest dataclass"""
    
    def test_request_creation(self):
        """Test basic request creation"""
        request = LLMRequest(
            messages=[{"role": "user", "content": "Hello"}]
        )
        assert len(request.messages) == 1
        assert request.messages[0]["content"] == "Hello"
    
    def test_request_defaults(self):
        """Test default values"""
        request = LLMRequest(messages=[])
        assert request.temperature == 0.7
        assert request.max_tokens == 2048
        assert request.system_prompt is None
    
    def test_request_with_system_prompt(self):
        """Test request with system prompt"""
        request = LLMRequest(
            messages=[{"role": "user", "content": "Hi"}],
            system_prompt="You are helpful"
        )
        assert request.system_prompt == "You are helpful"


class TestLLMProvider:
    """Test LLMProvider configuration"""
    
    def test_provider_api_key_from_env(self):
        """Test api_key property reads from environment"""
        provider = LLMProvider(
            name="Test",
            api_url="https://test.com",
            models=[],
            default_model="test",
            env_key="TEST_API_KEY",
            strengths=[]
        )
        # Without env var set
        assert provider.api_key is None
        assert provider.is_available is False
    
    @patch.dict('os.environ', {'TEST_API_KEY_2': 'sk-test-123'})
    def test_provider_is_available_with_key(self):
        """Test is_available returns True when key exists"""
        provider = LLMProvider(
            name="Test",
            api_url="https://test.com",
            models=[],
            default_model="test",
            env_key="TEST_API_KEY_2",
            strengths=[]
        )
        assert provider.api_key == "sk-test-123"
        assert provider.is_available is True


class TestLLMRouterInit:
    """Test LLMRouter initialization"""
    
    def test_default_initialization(self):
        """Test default router creation"""
        router = LLMRouter()
        assert router.default_provider == "deepseek"
        router.close()
    
    def test_custom_default_provider(self):
        """Test router with custom default provider"""
        router = LLMRouter(default_provider="openai")
        assert router.default_provider == "openai"
        router.close()
    
    def test_context_manager(self):
        """Test router as context manager"""
        with LLMRouter() as router:
            assert router is not None


class TestLLMRouterChat:
    """Test LLMRouter chat method with mocking"""
    
    @patch('core.llm_router.get_provider')
    @patch.object(LLMRouter, '_call_openai_compatible')
    def test_chat_routes_to_deepseek(self, mock_call, mock_get_provider):
        """Test chat routes to DeepSeek"""
        mock_provider = Mock()
        mock_provider.is_available = True
        mock_provider.default_model = "deepseek-chat"
        mock_provider.name = "deepseek"
        mock_get_provider.return_value = mock_provider
        
        mock_call.return_value = LLMResponse(
            content="Test response",
            provider="deepseek",
            model="deepseek-chat"
        )
        
        router = LLMRouter()
        response = router.chat(
            messages=[{"role": "user", "content": "Hello"}],
            provider="deepseek"
        )
        
        assert response.content == "Test response"
        mock_call.assert_called_once()
        router.close()
    
    @patch('core.llm_router.get_provider')
    def test_chat_raises_for_unavailable_provider(self, mock_get_provider):
        """Test chat raises error for unavailable provider"""
        mock_provider = Mock()
        mock_provider.is_available = False
        mock_get_provider.return_value = mock_provider
        
        router = LLMRouter()
        with pytest.raises(ValueError, match="not available"):
            router.chat(
                messages=[{"role": "user", "content": "Hello"}],
                provider="deepseek"
            )
        router.close()
    
    @patch('core.llm_router.get_provider')
    @patch.object(LLMRouter, '_call_openai_compatible')
    def test_chat_adds_system_prompt(self, mock_call, mock_get_provider):
        """Test system prompt is prepended to messages"""
        mock_provider = Mock()
        mock_provider.is_available = True
        mock_provider.default_model = "test-model"
        mock_provider.name = "deepseek"
        mock_get_provider.return_value = mock_provider
        
        mock_call.return_value = LLMResponse(
            content="Response",
            provider="deepseek",
            model="test-model"
        )
        
        router = LLMRouter()
        router.chat(
            messages=[{"role": "user", "content": "Hello"}],
            provider="deepseek",
            system_prompt="Be helpful"
        )
        
        # Verify system prompt was prepended
        call_args = mock_call.call_args
        messages = call_args[0][2]  # Third positional arg is messages
        assert messages[0]["role"] == "system"
        assert messages[0]["content"] == "Be helpful"
        router.close()


class TestLLMRouterProviderRouting:
    """Test routing to different providers"""
    
    @patch('core.llm_router.get_provider')
    @patch.object(LLMRouter, '_call_gemini')
    def test_routes_to_gemini(self, mock_call, mock_get_provider):
        """Test routing to Gemini provider"""
        mock_provider = Mock()
        mock_provider.is_available = True
        mock_provider.default_model = "gemini-2.0-flash"
        mock_provider.name = "gemini"
        mock_get_provider.return_value = mock_provider
        
        mock_call.return_value = LLMResponse(
            content="Gemini response",
            provider="gemini",
            model="gemini-2.0-flash"
        )
        
        router = LLMRouter()
        response = router.chat(
            messages=[{"role": "user", "content": "Hello"}],
            provider="gemini"
        )
        
        assert response.provider == "gemini"
        mock_call.assert_called_once()
        router.close()
    
    @patch('core.llm_router.get_provider')
    @patch.object(LLMRouter, '_call_claude')
    def test_routes_to_claude(self, mock_call, mock_get_provider):
        """Test routing to Claude provider"""
        mock_provider = Mock()
        mock_provider.is_available = True
        mock_provider.default_model = "claude-3-5-sonnet"
        mock_provider.name = "claude"
        mock_get_provider.return_value = mock_provider
        
        mock_call.return_value = LLMResponse(
            content="Claude response",
            provider="claude",
            model="claude-3-5-sonnet"
        )
        
        router = LLMRouter()
        response = router.chat(
            messages=[{"role": "user", "content": "Hello"}],
            provider="claude"
        )
        
        assert response.provider == "claude"
        mock_call.assert_called_once()
        router.close()
    
    @patch('core.llm_router.get_provider')
    def test_raises_for_unknown_provider(self, mock_get_provider):
        """Test error for unknown provider"""
        mock_provider = Mock()
        mock_provider.is_available = True
        mock_provider.default_model = "test"
        mock_get_provider.return_value = mock_provider
        
        router = LLMRouter()
        with pytest.raises(ValueError, match="Unknown provider"):
            router.chat(
                messages=[{"role": "user", "content": "Hello"}],
                provider="unknown"
            )
        router.close()


class TestLLMRouterFallback:
    """Test fallback mechanism"""
    
    @patch('core.llm_router.get_provider')
    @patch.object(LLMRouter, 'chat')
    def test_fallback_tries_next_provider(self, mock_chat, mock_get_provider):
        """Test fallback tries next provider on failure"""
        # First provider fails, second succeeds
        mock_provider = Mock()
        mock_provider.is_available = True
        mock_get_provider.return_value = mock_provider
        
        mock_chat.side_effect = [
            Exception("First failed"),
            LLMResponse(content="Success", provider="openai", model="gpt-4")
        ]
        
        router = LLMRouter()
        
        # Reset mock to track actual calls
        mock_chat.side_effect = None
        mock_chat.return_value = LLMResponse(
            content="Success",
            provider="fallback",
            model="test"
        )
        
        # Test with actual implementation using multiple providers
        with patch.object(router, 'chat') as inner_mock:
            inner_mock.side_effect = [
                Exception("First failed"),
                LLMResponse(content="Second success", provider="openai", model="gpt")
            ]
            
            # This should try deepseek first, then openai
            response = router.chat_with_fallback(
                messages=[{"role": "user", "content": "Test"}],
                preferred_providers=["deepseek", "openai"]
            )
            assert response.content == "Second success"
        
        router.close()
    
    @patch('core.llm_router.get_provider')
    def test_fallback_raises_when_all_fail(self, mock_get_provider):
        """Test fallback raises error when all providers fail"""
        mock_provider = Mock()
        mock_provider.is_available = False
        mock_get_provider.return_value = mock_provider
        
        router = LLMRouter()
        
        with pytest.raises(RuntimeError, match="All providers failed"):
            router.chat_with_fallback(
                messages=[{"role": "user", "content": "Test"}],
                preferred_providers=["deepseek", "openai"]
            )
        
        router.close()


class TestConvenienceFunctions:
    """Test module-level convenience functions"""
    
    def test_get_router_returns_router(self):
        """Test get_router returns LLMRouter instance"""
        router = get_router()
        assert isinstance(router, LLMRouter)
    
    def test_get_router_returns_same_instance(self):
        """Test get_router returns singleton"""
        router1 = get_router()
        router2 = get_router()
        assert router1 is router2
    
    @patch('core.llm_router.get_router')
    def test_quick_chat_uses_router(self, mock_get_router):
        """Test quick_chat uses default router"""
        mock_router = Mock()
        mock_router.chat.return_value = LLMResponse(
            content="Quick response",
            provider="deepseek",
            model="deepseek-chat"
        )
        mock_get_router.return_value = mock_router
        
        result = quick_chat("Hello")
        
        assert result == "Quick response"
        mock_router.chat.assert_called_once()


class TestLLMConfig:
    """Test llm_config module functions"""
    
    def test_get_provider_valid(self):
        """Test get_provider with valid name"""
        provider = get_provider("deepseek")
        assert provider.name == "DeepSeek"
    
    def test_get_provider_invalid(self):
        """Test get_provider with invalid name"""
        with pytest.raises(ValueError, match="Unknown provider"):
            get_provider("invalid")
    
    def test_get_available_providers_returns_list(self):
        """Test get_available_providers returns list"""
        providers = get_available_providers()
        assert isinstance(providers, list)
