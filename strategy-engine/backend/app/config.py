"""
Strategy Engine — Application Configuration

Uses Pydantic BaseSettings for environment-variable-driven config.
"""

from __future__ import annotations

from functools import lru_cache
from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # --- App ---
    app_name: str = "Strategy Engine"
    app_version: str = "0.1.0"
    debug: bool = False

    # --- Server ---
    host: str = "0.0.0.0"
    port: int = 8000

    # --- LLM ---
    openai_api_key: Optional[str] = Field(default=None, alias="OPENAI_API_KEY")
    openai_model: str = "gpt-4o"  # Used only when OPENAI_API_KEY is set
    deepseek_api_key: Optional[str] = Field(default=None, alias="DEEPSEEK_API_KEY")
    deepseek_model: str = "deepseek-chat"  # Primary model (default provider)

    @property
    def default_model(self) -> str:
        """Return the best available model based on configured API keys."""
        if self.deepseek_api_key:
            return self.deepseek_model
        if self.openai_api_key:
            return self.openai_model
        return self.deepseek_model  # Will fail with clear error at call time

    # --- Firestore (replaces PostgreSQL — uses same Firebase project as vdo-content) ---
    firebase_project_id: str = Field(
        default="vdo-content-4e158",
        alias="FIREBASE_PROJECT_ID",
    )
    firestore_runs_collection: str = "strategy_engine_runs"


    # --- Vector DB (Qdrant — self-hosted on Cloud Run) ---
    qdrant_url: str = Field(default="http://localhost:6333", alias="QDRANT_URL")
    qdrant_collection: str = "published_content"
    qdrant_api_key: Optional[str] = Field(default=None, alias="QDRANT_API_KEY")

    # --- Embedding (fastembed — local, no API key needed) ---
    # Model: BAAI/bge-small-en-v1.5, 384 dimensions
    # Downloads ~100MB on first run, then cached

    # --- SEO External API ---
    dataforseo_login: Optional[str] = Field(default=None, alias="DATAFORSEO_LOGIN")
    dataforseo_password: Optional[str] = Field(default=None, alias="DATAFORSEO_PASSWORD")

    # --- Production System Webhook ---
    production_webhook_url: Optional[str] = Field(
        default=None,
        alias="PRODUCTION_WEBHOOK_URL",
        description="URL of the existing vdo-content system's ingest endpoint",
    )
    production_webhook_token: Optional[str] = Field(
        default=None,
        alias="PRODUCTION_WEBHOOK_TOKEN",
        description="Bearer token for authenticating with the production webhook",
    )
    webhook_timeout_seconds: int = 30
    webhook_max_retries: int = 3

    # --- CORS ---
    cors_origins: list[str] = ["http://localhost:3000", "http://localhost:3001"]

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": False,
    }


@lru_cache()
def get_settings() -> Settings:
    """Singleton settings instance (cached)."""
    return Settings()
