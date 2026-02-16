"""
VDO Content Configuration
Centralized settings management using Pydantic
"""
from pathlib import Path
from typing import Optional
import os
import logging

logger = logging.getLogger("vdo_content.config")

# Try pydantic-settings first, fall back to pydantic v1 style
try:
    from pydantic_settings import BaseSettings
except ImportError:
    try:
        from pydantic import BaseSettings  # pydantic v1
    except ImportError:
        # Ultimate fallback - simple class without validation
        class BaseSettings:
            def __init__(self, **kwargs):
                for k, v in kwargs.items():
                    setattr(self, k, v)
            class Config:
                env_file = ".env"


class Settings(BaseSettings):
    """Application settings with environment variable support"""
    
    # Application
    app_name: str = "VDO Content"
    version: str = "2.2.0"
    debug: bool = False
    
    # API Keys — Pydantic BaseSettings reads from env vars automatically
    deepseek_api_key: str = ""
    kimi_api_key: Optional[str] = None
    google_api_key: Optional[str] = None
    google_tts_api_key: Optional[str] = None
    openai_api_key: Optional[str] = None
    
    # Paths
    data_dir: Path = Path(__file__).parent.parent.parent / "data"
    export_dir: Path = Path(__file__).parent.parent.parent / "exports"
    
    # Limits
    max_revisions: int = 3
    max_scene_duration: float = 8.0  # seconds
    default_video_duration: int = 60  # seconds
    
    # Defaults
    default_style: str = "documentary"
    default_language: str = "th"
    
    # Database
    database_url: Optional[str] = None
    
    # Server
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    streamlit_port: int = 8510
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


# Global settings instance - catch errors gracefully
try:
    settings = Settings()
except Exception as e:
    logger.warning(f"Settings validation failed, using defaults: {e}")
    # Fallback settings if validation fails
    settings = type('Settings', (), {
        'app_name': 'VDO Content',
        'version': '2.2.0',
        'debug': False,
        'deepseek_api_key': os.getenv("DEEPSEEK_API_KEY", ""),
        'data_dir': Path(__file__).parent.parent.parent / "data",
        'export_dir': Path(__file__).parent.parent.parent / "exports",
        'default_style': 'documentary',
        'default_language': 'th',
    })()


