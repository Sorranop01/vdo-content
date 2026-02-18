"""
LLM Provider Configuration
VDO Content V2 - Multiple LLM Support

Supported providers:
- DeepSeek (default) - Best for Thai, cost-effective
- OpenAI (GPT-4o) - Creative, reliable
- Gemini - Fast, multimodal
- Claude - Analysis, safety
"""

import os
from typing import TypedDict, Literal
from dataclasses import dataclass


# Provider types
ProviderName = Literal["deepseek", "openai", "gemini", "claude", "kimi", "groq"]


@dataclass
class LLMModel:
    """LLM model configuration"""
    id: str
    name: str
    context_length: int = 8192
    supports_system: bool = True
    cost_per_1k: float = 0.0  # USD per 1k tokens


@dataclass
class LLMProvider:
    """LLM provider configuration"""
    name: str
    api_url: str
    models: list[LLMModel]
    default_model: str
    env_key: str
    strengths: list[str]
    
    @property
    def api_key(self) -> str | None:
        return os.getenv(self.env_key)
    
    @property
    def is_available(self) -> bool:
        return bool(self.api_key)


# ============ Provider Definitions ============

DEEPSEEK = LLMProvider(
    name="DeepSeek",
    api_url="https://api.deepseek.com/v1",
    models=[
        LLMModel("deepseek-chat", "DeepSeek Chat", context_length=64000, cost_per_1k=0.001),
        LLMModel("deepseek-coder", "DeepSeek Coder", context_length=64000, cost_per_1k=0.001),
    ],
    default_model="deepseek-chat",
    env_key="DEEPSEEK_API_KEY",
    strengths=["Thai language", "Cost-effective", "Large context"]
)

OPENAI = LLMProvider(
    name="OpenAI",
    api_url="https://api.openai.com/v1",
    models=[
        LLMModel("gpt-4o", "GPT-4o", context_length=128000, cost_per_1k=0.005),
        LLMModel("gpt-4o-mini", "GPT-4o Mini", context_length=128000, cost_per_1k=0.00015),
        LLMModel("gpt-4-turbo", "GPT-4 Turbo", context_length=128000, cost_per_1k=0.01),
    ],
    default_model="gpt-4o-mini",
    env_key="OPENAI_API_KEY",
    strengths=["Creative", "Reliable", "Wide adoption"]
)

GEMINI = LLMProvider(
    name="Google Gemini",
    api_url="https://generativelanguage.googleapis.com/v1beta",
    models=[
        LLMModel("gemini-2.0-flash", "Gemini 2.0 Flash", context_length=1000000, cost_per_1k=0.0001),
        LLMModel("gemini-1.5-pro", "Gemini 1.5 Pro", context_length=2000000, cost_per_1k=0.00125),
    ],
    default_model="gemini-2.0-flash",
    env_key="GOOGLE_API_KEY",
    strengths=["Fast", "Multimodal", "Huge context"]
)

CLAUDE = LLMProvider(
    name="Anthropic Claude",
    api_url="https://api.anthropic.com/v1",
    models=[
        LLMModel("claude-3-5-sonnet-20241022", "Claude 3.5 Sonnet", context_length=200000, cost_per_1k=0.003),
        LLMModel("claude-3-haiku-20240307", "Claude 3 Haiku", context_length=200000, cost_per_1k=0.00025),
    ],
    default_model="claude-3-5-sonnet-20241022",
    env_key="ANTHROPIC_API_KEY",
    strengths=["Analysis", "Safety", "Long outputs"]
)

KIMI = LLMProvider(
    name="Kimi (Moonshot)",
    api_url="https://api.moonshot.ai/v1",
    models=[
        LLMModel("kimi-k2.5", "Kimi K2.5", context_length=131072, cost_per_1k=0.002),
    ],
    default_model="kimi-k2.5",
    env_key="KIMI_API_KEY",
    strengths=["Thai language", "Long context", "Creative"]
)

GROQ = LLMProvider(
    name="Groq (Free, Ultra-fast)",
    api_url="https://api.groq.com/openai/v1",
    models=[
        LLMModel("llama-3.3-70b-versatile", "LLaMA 3.3 70B", context_length=128000, cost_per_1k=0.0),
        LLMModel("llama-3.1-8b-instant", "LLaMA 3.1 8B", context_length=128000, cost_per_1k=0.0),
        LLMModel("gemma2-9b-it", "Gemma 2 9B", context_length=8192, cost_per_1k=0.0),
    ],
    default_model="llama-3.3-70b-versatile",
    env_key="GROQ_API_KEY",
    strengths=["Free", "Ultra-fast", "Good multilingual"]
)


# ============ Provider Registry ============

LLM_PROVIDERS: dict[ProviderName, LLMProvider] = {
    "deepseek": DEEPSEEK,
    "openai": OPENAI,
    "gemini": GEMINI,
    "claude": CLAUDE,
    "kimi": KIMI,
    "groq": GROQ,
}

DEFAULT_PROVIDER: ProviderName = "deepseek"


def get_provider(name: ProviderName) -> LLMProvider:
    """Get provider by name"""
    if name not in LLM_PROVIDERS:
        raise ValueError(f"Unknown provider: {name}")
    return LLM_PROVIDERS[name]


def get_available_providers() -> list[LLMProvider]:
    """Get list of providers with valid API keys"""
    return [p for p in LLM_PROVIDERS.values() if p.is_available]


def get_provider_choices() -> list[tuple[str, str]]:
    """Get (id, display_name) tuples for UI dropdowns"""
    choices = []
    for key, provider in LLM_PROVIDERS.items():
        status = "✅" if provider.is_available else "🔒"
        name = f"{status} {provider.name}"
        choices.append((key, name))
    return choices


def get_model_choices(provider_name: ProviderName) -> list[tuple[str, str]]:
    """Get available models for a provider"""
    provider = get_provider(provider_name)
    return [(m.id, m.name) for m in provider.models]
