"""
Database Reference Data Operations
CRUD for visual tags, style profiles, video profiles, content categories,
target audiences, and content goals.
"""

import uuid
import logging
from typing import Optional

from .db_engine import get_db
from .db_models import (
    VisualTagDB, StyleProfileDB, VideoProfileDB,
    ContentCategoryDB, TargetAudienceDB, ContentGoalDB
)

logger = logging.getLogger("vdo_content.database")


# ============ Visual Tag Functions ============

def get_visual_tags() -> dict:
    """Get all visual tags organized by category"""
    with get_db() as db:
        tags = db.query(VisualTagDB).filter(VisualTagDB.is_active.is_(True)).order_by(VisualTagDB.category, VisualTagDB.order_num).all()
        
        result = {}
        for tag in tags:
            if tag.category not in result:
                result[tag.category] = []
            result[tag.category].append({"label": tag.label, "value": tag.value})
        return result


def add_visual_tag(category: str, label: str, value: str) -> bool:
    """Add a new visual tag option"""
    with get_db() as db:
        try:
            max_order = db.query(VisualTagDB).filter(VisualTagDB.category == category).count()
            tag = VisualTagDB(
                category=category,
                label=label,
                value=value,
                order_num=max_order
            )
            db.add(tag)
            return True
        except Exception as e:
            logger.error(f"Error adding tag: {e}")
            return False


def delete_visual_tag(category: str, label: str) -> bool:
    """Delete a visual tag option"""
    with get_db() as db:
        tag = db.query(VisualTagDB).filter(
            VisualTagDB.category == category,
            VisualTagDB.label == label
        ).first()
        if tag:
            db.delete(tag)
            return True
        return False


def update_visual_tag(tag_id: str, label: str, value: str) -> bool:
    """Update an existing tag"""
    with get_db() as db:
        tag = db.query(VisualTagDB).filter(VisualTagDB.id == uuid.UUID(tag_id)).first()
        if tag:
            tag.label = label
            tag.value = value
            return True
        return False


def get_all_tags_raw() -> list[dict]:
    """Get all tags as a flat list of dicts (for data editor)"""
    with get_db() as db:
        tags = db.query(VisualTagDB).order_by(VisualTagDB.category, VisualTagDB.order_num).all()
        return [
            {
                "id": str(t.id),
                "category": t.category,
                "label": t.label,
                "value": t.value,
                "active": t.is_active
            }
            for t in tags
        ]


def delete_tag(tag_id: str) -> bool:
    """Delete a tag by ID (alias for database_tags page)"""
    with get_db() as db:
        tag = db.query(VisualTagDB).filter(VisualTagDB.id == uuid.UUID(tag_id)).first()
        if tag:
            db.delete(tag)
            return True
        return False


# ============ Style Profile Functions ============

def save_style_profile(name: str, config: dict, description: str = "") -> bool:
    """Save a new visual style profile"""
    with get_db() as db:
        try:
            existing = db.query(StyleProfileDB).filter(StyleProfileDB.name == name).first()
            if existing:
                existing.config = config
                existing.description = description
            else:
                profile = StyleProfileDB(name=name, config=config, description=description)
                db.add(profile)
            return True
        except Exception as e:
            logger.error(f"Error saving profile: {e}")
            return False


def list_style_profiles() -> list[dict]:
    """List all saved profiles"""
    with get_db() as db:
        profiles = db.query(StyleProfileDB).order_by(StyleProfileDB.name).all()
        return [
            {
                "id": str(p.id),
                "name": p.name,
                "description": p.description,
                "config": p.config
            }
            for p in profiles
        ]


def delete_style_profile(profile_id: str) -> bool:
    """Delete a profile"""
    with get_db() as db:
        profile = db.query(StyleProfileDB).filter(StyleProfileDB.id == uuid.UUID(profile_id)).first()
        if profile:
            db.delete(profile)
            return True
        return False


# ============ Video Profile Functions ============

def get_video_profiles() -> list[dict]:
    """Get all active video profiles"""
    with get_db() as db:
        profiles = db.query(VideoProfileDB).filter(
            VideoProfileDB.is_active.is_(True)
        ).order_by(VideoProfileDB.order_num).all()
        
        return [
            {
                "id": p.id,
                "name_th": p.name_th,
                "name_en": p.name_en,
                "description_th": p.description_th,
                "description_en": p.description_en,
                "icon": p.icon,
                "config": p.config
            }
            for p in profiles
        ]


def list_video_profiles() -> list[dict]:
    """List all active video profiles"""
    with get_db() as db:
        profiles = db.query(VideoProfileDB).filter(
            VideoProfileDB.is_active.is_(True)
        ).order_by(VideoProfileDB.order_num).all()
        
        return [
            {
                "id": p.id,
                "name_th": p.name_th,
                "name_en": p.name_en,
                "description_th": p.description_th,
                "description_en": p.description_en,
                "icon": p.icon,
                "config": p.config,
                "is_system": p.is_system
            }
            for p in profiles
        ]


def get_video_profile(profile_id: str) -> Optional[dict]:
    """Get a single video profile by ID"""
    with get_db() as db:
        profile = db.query(VideoProfileDB).filter(VideoProfileDB.id == profile_id).first()
        if profile:
            return {
                "id": profile.id,
                "name_th": profile.name_th,
                "name_en": profile.name_en,
                "description_th": profile.description_th,
                "description_en": profile.description_en,
                "icon": profile.icon,
                "config": profile.config,
                "is_system": profile.is_system
            }
        return None


def update_video_profile(profile_id: str, config: dict, name_th: str = None, name_en: str = None, description_th: str = None, description_en: str = None) -> bool:
    """Update a video profile's configuration and details"""
    with get_db() as db:
        profile = db.query(VideoProfileDB).filter(VideoProfileDB.id == profile_id).first()
        if profile:
            profile.config = config
            if name_th: profile.name_th = name_th
            if name_en: profile.name_en = name_en
            if description_th: profile.description_th = description_th
            if description_en: profile.description_en = description_en
            return True
        return False


# ============ Content Category Functions ============

def get_content_categories() -> list[dict]:
    """Get all active content categories for dropdown"""
    with get_db() as db:
        categories = db.query(ContentCategoryDB).filter(
            ContentCategoryDB.is_active.is_(True)
        ).order_by(ContentCategoryDB.order_num).all()
        
        return [
            {
                "id": str(cat.id),
                "name_th": cat.name_th,
                "name_en": cat.name_en,
                "description": cat.description,
                "icon": cat.icon
            }
            for cat in categories
        ]


# ============ Target Audience Functions ============

def get_target_audiences() -> list[dict]:
    """Get all active target audiences for dropdown"""
    with get_db() as db:
        audiences = db.query(TargetAudienceDB).filter(
            TargetAudienceDB.is_active.is_(True)
        ).order_by(TargetAudienceDB.order_num).all()
        
        return [
            {
                "id": str(aud.id),
                "name_th": aud.name_th,
                "name_en": aud.name_en,
                "age_range": aud.age_range,
                "description": aud.description
            }
            for aud in audiences
        ]


# ============ Content Goal Functions ============

def get_content_goals() -> list[dict]:
    """Get all active content goals for dropdown"""
    with get_db() as db:
        goals = db.query(ContentGoalDB).filter(
            ContentGoalDB.is_active.is_(True)
        ).order_by(ContentGoalDB.order_num).all()
        
        return [
            {
                "id": str(goal.id),
                "name_th": goal.name_th,
                "name_en": goal.name_en,
                "description": goal.description,
                "icon": goal.icon,
                "prompt_hint": goal.prompt_hint
            }
            for goal in goals
        ]


# ============ Aliases ============

add_tag = add_visual_tag
get_all_style_presets = list_style_profiles
save_style_preset = save_style_profile
delete_style_preset = delete_style_profile
