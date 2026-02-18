"""
Frontend Data Caching Layer
Wraps core database functions with Streamlit caching to improve performance.
"""
import streamlit as st
import logging

# Initialize logger
logger = logging.getLogger("vdo_content.cache")

# Try to import database functions
try:
    from src.core.db_reference import (
        get_video_profiles as _get_video_profiles,
        get_content_goals as _get_content_goals,
        get_target_audiences as _get_target_audiences,
        get_visual_tags as _get_visual_tags,
        get_content_categories as _get_content_categories
    )
    DB_AVAILABLE = True
except ImportError:
    logger.warning("Database module not found. Caching disabled.")
    DB_AVAILABLE = False
    _get_video_profiles = lambda: []
    _get_content_goals = lambda: []
    _get_target_audiences = lambda: []
    _get_visual_tags = lambda: {}
    _get_content_categories = lambda: []

# Cache TTL (Time To Live) in seconds
# 5 minutes is a good balance for reference data that doesn't change often
CACHE_TTL = 300

@st.cache_data(ttl=CACHE_TTL, show_spinner=False)
def get_cached_video_profiles():
    """Cached version of get_video_profiles"""
    if not DB_AVAILABLE: return []
    return _get_video_profiles()

@st.cache_data(ttl=CACHE_TTL, show_spinner=False)
def get_cached_content_goals():
    """Cached version of get_content_goals"""
    if not DB_AVAILABLE: return []
    return _get_content_goals()

@st.cache_data(ttl=CACHE_TTL, show_spinner=False)
def get_cached_target_audiences():
    """Cached version of get_target_audiences"""
    if not DB_AVAILABLE: return []
    return _get_target_audiences()

@st.cache_data(ttl=CACHE_TTL, show_spinner=False)
def get_cached_visual_tags():
    """Cached version of get_visual_tags"""
    if not DB_AVAILABLE: return {}
    return _get_visual_tags()

@st.cache_data(ttl=CACHE_TTL, show_spinner=False)
def get_cached_content_categories():
    """Cached version of get_content_categories"""
    if not DB_AVAILABLE: return []
    return _get_content_categories()

def clear_all_cache():
    """Helper to clear all data caches"""
    get_cached_video_profiles.clear()
    get_cached_content_goals.clear()
    get_cached_target_audiences.clear()
    get_cached_visual_tags.clear()
    get_cached_content_categories.clear()
