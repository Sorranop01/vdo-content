"""
LLM Router - Unified Interface for Multiple LLM Providers
VDO Content V2

Provides a unified interface for calling different LLM providers
with automatic fallback and error handling.
"""

import os
import json
import httpx
from typing import Optional, Literal
from dataclasses import dataclass

from .llm_config import (
    LLM_PROVIDERS,
    DEFAULT_PROVIDER,
    ProviderName,
    get_provider,
    get_available_providers,
)


@dataclass
class LLMResponse:
    """Unified LLM response"""
    content: str
    provider: str
    model: str
    tokens_used: int = 0
    finish_reason: str = "stop"


@dataclass
class LLMRequest:
    """Unified LLM request"""
    messages: list[dict]
    temperature: float = 0.7
    max_tokens: int = 2048
    system_prompt: Optional[str] = None


class LLMRouter:
    """
    Unified router for multiple LLM providers.
    
    Usage:
        router = LLMRouter()
        response = router.chat(
            messages=[{"role": "user", "content": "Hello"}],
            provider="deepseek"
        )
    """
    
    def __init__(self, default_provider: ProviderName = DEFAULT_PROVIDER):
        self.default_provider = default_provider
        self._client = httpx.Client(timeout=60.0)
    
    def chat(
        self,
        messages: list[dict],
        provider: Optional[ProviderName] = None,
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2048,
        system_prompt: Optional[str] = None,
    ) -> LLMResponse:
        """
        Send chat completion request to specified provider.
        
        Args:
            messages: List of message dicts with role/content
            provider: LLM provider name (default: deepseek)
            model: Specific model ID (default: provider's default)
            temperature: Creativity (0-1)
            max_tokens: Max response tokens
            system_prompt: Optional system prompt to prepend
        
        Returns:
            LLMResponse with content and metadata
        """
        provider_name = provider or self.default_provider
        provider_config = get_provider(provider_name)
        
        if not provider_config.is_available:
            raise ValueError(f"Provider {provider_name} not available (missing API key)")
        
        model_id = model or provider_config.default_model
        
        # Add system prompt if provided
        if system_prompt:
            messages = [{"role": "system", "content": system_prompt}] + messages
        
        # Route to appropriate provider
        if provider_name in ("deepseek", "openai", "kimi"):
            return self._call_openai_compatible(provider_config, model_id, messages, temperature, max_tokens)
        elif provider_name == "gemini":
            return self._call_gemini(provider_config, model_id, messages, temperature, max_tokens)
        elif provider_name == "claude":
            return self._call_claude(provider_config, model_id, messages, temperature, max_tokens)
        else:
            raise ValueError(f"Unknown provider: {provider_name}")
    
    def _call_openai_compatible(
        self,
        provider,
        model: str,
        messages: list[dict],
        temperature: float,
        max_tokens: int
    ) -> LLMResponse:
        """Call OpenAI-compatible API (OpenAI, DeepSeek)"""
        headers = {
            "Authorization": f"Bearer {provider.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens
        }
        
        response = self._client.post(
            f"{provider.api_url}/chat/completions",
            headers=headers,
            json=payload
        )
        response.raise_for_status()
        
        data = response.json()
        choice = data["choices"][0]
        
        return LLMResponse(
            content=choice["message"]["content"],
            provider=provider.name,
            model=model,
            tokens_used=data.get("usage", {}).get("total_tokens", 0),
            finish_reason=choice.get("finish_reason", "stop")
        )
    
    def _call_gemini(
        self,
        provider,
        model: str,
        messages: list[dict],
        temperature: float,
        max_tokens: int
    ) -> LLMResponse:
        """Call Google Gemini API"""
        # Convert messages to Gemini format
        contents = []
        system_instruction = None
        
        for msg in messages:
            if msg["role"] == "system":
                system_instruction = msg["content"]
            else:
                role = "user" if msg["role"] == "user" else "model"
                contents.append({
                    "role": role,
                    "parts": [{"text": msg["content"]}]
                })
        
        payload = {
            "contents": contents,
            "generationConfig": {
                "temperature": temperature,
                "maxOutputTokens": max_tokens
            }
        }
        
        if system_instruction:
            payload["systemInstruction"] = {"parts": [{"text": system_instruction}]}
        
        url = f"{provider.api_url}/models/{model}:generateContent?key={provider.api_key}"
        response = self._client.post(url, json=payload)
        response.raise_for_status()
        
        data = response.json()
        content = data["candidates"][0]["content"]["parts"][0]["text"]
        
        return LLMResponse(
            content=content,
            provider=provider.name,
            model=model,
            tokens_used=data.get("usageMetadata", {}).get("totalTokenCount", 0),
            finish_reason=data["candidates"][0].get("finishReason", "STOP")
        )
    
    def _call_claude(
        self,
        provider,
        model: str,
        messages: list[dict],
        temperature: float,
        max_tokens: int
    ) -> LLMResponse:
        """Call Anthropic Claude API"""
        headers = {
            "x-api-key": provider.api_key,
            "anthropic-version": "2023-06-01",
            "Content-Type": "application/json"
        }
        
        # Extract system message
        system = None
        claude_messages = []
        for msg in messages:
            if msg["role"] == "system":
                system = msg["content"]
            else:
                claude_messages.append(msg)
        
        payload = {
            "model": model,
            "messages": claude_messages,
            "max_tokens": max_tokens,
            "temperature": temperature
        }
        
        if system:
            payload["system"] = system
        
        response = self._client.post(
            f"{provider.api_url}/messages",
            headers=headers,
            json=payload
        )
        response.raise_for_status()
        
        data = response.json()
        content = data["content"][0]["text"]
        
        return LLMResponse(
            content=content,
            provider=provider.name,
            model=model,
            tokens_used=data.get("usage", {}).get("input_tokens", 0) + 
                       data.get("usage", {}).get("output_tokens", 0),
            finish_reason=data.get("stop_reason", "end_turn")
        )
    
    def chat_with_fallback(
        self,
        messages: list[dict],
        preferred_providers: list[ProviderName] = None,
        **kwargs
    ) -> LLMResponse:
        """
        Try providers in order, falling back on failure.
        
        Args:
            messages: Chat messages
            preferred_providers: Order of providers to try
            **kwargs: Additional chat params
        
        Returns:
            LLMResponse from first successful provider
        """
        providers = preferred_providers or [self.default_provider, "openai", "gemini"]
        
        last_error = None
        for provider_name in providers:
            try:
                provider = get_provider(provider_name)
                if not provider.is_available:
                    continue
                return self.chat(messages, provider=provider_name, **kwargs)
            except Exception as e:
                last_error = e
                continue
        
        raise RuntimeError(f"All providers failed. Last error: {last_error}")
    
    def close(self):
        """Close HTTP client"""
        self._client.close()
    
    def __enter__(self):
        return self
    
    def __exit__(self, *args):
        self.close()


# ============ Convenience Functions ============

_default_router: Optional[LLMRouter] = None


def get_router() -> LLMRouter:
    """Get or create default router instance"""
    global _default_router
    if _default_router is None:
        _default_router = LLMRouter()
    return _default_router


def quick_chat(
    prompt: str,
    provider: ProviderName = DEFAULT_PROVIDER,
    system_prompt: Optional[str] = None,
    **kwargs
) -> str:
    """Quick single-turn chat"""
    router = get_router()
    response = router.chat(
        messages=[{"role": "user", "content": prompt}],
        provider=provider,
        system_prompt=system_prompt,
        **kwargs
    )
    return response.content
