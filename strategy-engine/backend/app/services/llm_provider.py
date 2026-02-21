"""
Strategy Engine — LLM Provider Abstraction

Provides a unified interface for structured LLM output
using the `instructor` library with OpenAI or DeepSeek backends.
"""

from __future__ import annotations

import logging
from typing import TypeVar, Type

import instructor
from openai import AsyncOpenAI
from pydantic import BaseModel

from app.config import get_settings

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)


def _get_client(
    provider: str = "openai",
    api_key: str | None = None,
) -> instructor.AsyncInstructor:
    """
    Create an instructor-patched async OpenAI client.

    Args:
        provider: 'openai' or 'deepseek'
        api_key: Override API key (uses env var if None)

    Returns:
        Instructor-wrapped async client ready for structured output.
    """
    settings = get_settings()

    if provider == "deepseek":
        key = api_key or settings.deepseek_api_key
        base_url = "https://api.deepseek.com"
        if not key:
            raise ValueError("DEEPSEEK_API_KEY is not configured")
    else:
        key = api_key or settings.openai_api_key
        base_url = None  # Use default OpenAI URL
        if not key:
            raise ValueError("OPENAI_API_KEY is not configured")

    raw_client = AsyncOpenAI(
        api_key=key,
        base_url=base_url,
    )

    return instructor.from_openai(raw_client)


async def structured_completion(
    response_model: Type[T],
    system_prompt: str,
    user_prompt: str,
    model: str | None = None,
    provider: str = "openai",
    api_key: str | None = None,
    temperature: float = 0.7,
    max_retries: int = 2,
) -> T:
    """
    Get a structured (Pydantic-validated) response from an LLM.

    This is the core function all agents use. `instructor` guarantees
    the response matches the Pydantic model — no markdown, no conversation,
    just clean structured data.

    Args:
        response_model: Pydantic model class for the output.
        system_prompt: System instructions for the LLM.
        user_prompt: User input text.
        model: Override model name (uses settings default if None).
        provider: 'openai' or 'deepseek'.
        api_key: Override API key.
        temperature: LLM temperature (0-2).
        max_retries: Instructor retry count for validation failures.

    Returns:
        Instance of response_model with validated fields.
    """
    settings = get_settings()

    if model is None:
        model = (
            settings.deepseek_model
            if provider == "deepseek"
            else settings.openai_model
        )

    client = _get_client(provider=provider, api_key=api_key)

    logger.info(
        f"[LLM] Calling {provider}/{model} for {response_model.__name__} "
        f"(temp={temperature}, retries={max_retries})"
    )

    result = await client.chat.completions.create(
        model=model,
        response_model=response_model,
        max_retries=max_retries,
        temperature=temperature,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
    )

    logger.info(f"[LLM] Got valid {response_model.__name__} response")
    return result


def resolve_provider(model: str) -> str:
    """Detect provider from model name."""
    if "deepseek" in model.lower():
        return "deepseek"
    return "openai"
