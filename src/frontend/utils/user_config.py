"""
User Configuration Management
Handles user preferences and persistence
"""
import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Optional

logger = logging.getLogger("vdo_content.user_config")


class UserConfig:
    """User configuration manager"""
    
    def __init__(self, config_dir: Path):
        self.config_file = config_dir / "user_config.json"
        self.config_file.parent.mkdir(parents=True, exist_ok=True)
    
    def save(self, config: dict):
        """Save user preferences and last state"""
        try:
            current = self.load()
            current.update(config)
            with open(self.config_file, "w") as f:
                json.dump(current, f)
        except Exception as e:
            logger.warning(f"Failed to save user config: {e}")
    
    def load(self) -> dict:
        """Load user preferences"""
        if self.config_file.exists():
            try:
                with open(self.config_file, "r") as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"Failed to load user config: {e}")
        return {}
    
    def update_last_active(self, project_id: str, page_index: int):
        """Update last active state"""
        self.save({
            "last_project_id": project_id,
            "last_page": page_index,
            "last_updated": datetime.now().isoformat()
        })
    
    def get_last_project(self) -> Optional[str]:
        """Get last active project ID"""
        config = self.load()
        return config.get("last_project_id")
    
    def get_last_page(self) -> int:
        """Get last active page"""
        config = self.load()
        return config.get("last_page", 0)


# Global config instance
from src.config.constants import DATA_DIR
_config = UserConfig(DATA_DIR)


def load_user_config() -> dict:
    """Load user configuration (wrapper function)"""
    return _config.load()


def save_user_config(config: dict):
    """Save user configuration (wrapper function)"""
    _config.save(config)

