"""
Shared Database Module
Moved from core/database.py with improved organization
"""
# Re-export everything from the original location for backward compatibility
from ..core.database import *

__all__ = [
    "init_db",
    "db_save_project",
    "db_load_project",
    "db_list_projects",
    "db_delete_project",
    "db_save_draft",
    "db_load_draft",
    "db_delete_draft",
    "db_list_drafts",
    "get_visual_tags",
    "save_style_profile",
    "list_style_profiles",
    "delete_style_profile",
    "add_visual_tag",
    "delete_visual_tag",
    "update_visual_tag",
    "get_all_tags_raw",
    "log_api_usage",
    "save_media_asset",
    "list_video_profiles",
    "get_video_profile"
]
