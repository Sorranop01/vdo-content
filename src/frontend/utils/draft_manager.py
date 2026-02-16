"""
Draft Management Utilities
Handles draft persistence to database for ideation workflow
"""
import streamlit as st
import logging
from typing import Optional, Dict, Any

logger = logging.getLogger("vdo_content.draft_manager")

# Import from core
from src.core.database import db_save_draft, db_delete_draft, db_load_draft

# Lazy database check (do NOT call init_db() at import time)
_database_checked = False
DATABASE_AVAILABLE = False


def _check_database():
    """Check database availability (lazy, called on first use)"""
    global _database_checked, DATABASE_AVAILABLE
    if not _database_checked:
        try:
            from src.core.database import get_db
            with get_db() as db:
                DATABASE_AVAILABLE = True
        except Exception as e:
            logger.warning(f"Database not available for drafts: {e}")
            DATABASE_AVAILABLE = False
        _database_checked = True
    return DATABASE_AVAILABLE


def save_draft_to_db() -> bool:
    """Save current draft to database"""
    if not _check_database():
        return False
    
    try:
        content = {
            "title": st.session_state.get("draft_title", ""),
            "topic": st.session_state.get("draft_topic", ""),
            "style": st.session_state.get("draft_style", "documentary"),
            "duration": st.session_state.get("draft_duration", 60),
            "character": st.session_state.get("draft_character", "")
        }
        db_save_draft(st.session_state.session_id, "ideation", content)
        return True
    except Exception as e:
        logger.warning(f"Draft save error: {e}")
        return False


def load_draft_from_db() -> Optional[Dict[str, Any]]:
    """Load draft from database"""
    if not _check_database():
        return None
    
    try:
        return db_load_draft(st.session_state.session_id, "ideation")
    except Exception as e:
        logger.warning(f"Draft load error: {e}")
        return None


def clear_draft_from_db() -> bool:
    """Clear draft from database after project is created"""
    if not _check_database():
        return False
    
    try:
        db_delete_draft(st.session_state.session_id, "ideation")
        return True
    except Exception as e:
        logger.warning(f"Draft clear error: {e}")
        return False


def clear_draft_state():
    """Clear all draft-related session state"""
    draft_keys = [
        "draft_title",
        "draft_topic", 
        "draft_style",
        "draft_duration",
        "draft_character",
        "draft_video_profile",
        "draft_content_type",
        "proposal",
        "proposal_version",
        "audio_segments",
        "uploaded_audio_path"
    ]
    
    for key in draft_keys:
        if key in st.session_state:
            if key == "draft_duration":
                st.session_state[key] = 60  # Reset to default
            elif key == "draft_style":
                st.session_state[key] = "documentary"
            elif key == "draft_video_profile":
                st.session_state[key] = "educational"
            else:
                st.session_state[key] = "" if isinstance(st.session_state.get(key), str) else None


def list_drafts():
    """List all drafts (placeholder for future implementation)"""
    # Future: implement draft listing from database
    return []


# API Wrappers for consistent naming
save_draft = save_draft_to_db
load_draft = load_draft_from_db
clear_draft = clear_draft_from_db

