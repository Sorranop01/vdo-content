"""
Firestore Reference Data Operations
CRUD for visual tags, style profiles, video profiles, content categories,
target audiences, and content goals using Google Cloud Firestore.
Replaces the SQL-based db_reference.py.
"""

import logging
import uuid
from typing import Optional, List, Dict, Any

from google.cloud import firestore
from .firestore_client import get_firestore_client, get_db

logger = logging.getLogger("vdo_content.database")

# Collection names
COL_TAGS = "visual_tags"
COL_STYLE_PROFILES = "style_profiles"
COL_VIDEO_PROFILES = "video_profiles"
COL_CATEGORIES = "content_categories"
COL_AUDIENCES = "target_audiences"
COL_GOALS = "content_goals"

def _safe_uuid(value: str) -> str:
    if not value: return str(uuid.uuid4())
    try:
        uuid.UUID(str(value))
        return str(value)
    except ValueError:
        return str(uuid.uuid4())

# ============ Visual Tag Functions ============

def get_visual_tags() -> dict:
    """Get all visual tags organized by category"""
    db = get_firestore_client()
    docs = db.collection(COL_TAGS).stream()
    
    # Client-side filter & sort (avoids composite index requirement)
    all_tags = []
    for doc in docs:
        tag = doc.to_dict()
        if tag.get("is_active", True):
            all_tags.append(tag)
    all_tags.sort(key=lambda t: (t.get("category", ""), t.get("order_num", 0)))
    
    result = {}
    for tag in all_tags:
        category = tag.get("category")
        if category not in result:
            result[category] = []
        result[category].append({
            "label": tag.get("label"),
            "value": tag.get("value")
        })
    return result

def add_visual_tag(category: str, label: str, value: str) -> bool:
    """Add a new visual tag option"""
    try:
        db = get_firestore_client()
        
        # Get current max order
        query = db.collection(COL_TAGS).where("category", "==", category)
        count = len(list(query.stream()))
        
        tag_id = str(uuid.uuid4())
        db.collection(COL_TAGS).document(tag_id).set({
            "category": category,
            "label": label,
            "value": value,
            "order_num": count,
            "is_active": True
        })
        return True
    except Exception as e:
        logger.error(f"Error adding tag: {e}")
        return False

def delete_visual_tag(category: str, label: str) -> bool:
    """Delete a visual tag option"""
    try:
        db = get_firestore_client()
        docs = db.collection(COL_TAGS)\
                 .where("category", "==", category)\
                 .where("label", "==", label)\
                 .limit(1)\
                 .stream()
                 
        for doc in docs:
            doc.reference.delete()
            return True
        return False
    except Exception as e:
        logger.error(f"Error deleting tag: {e}")
        return False

def update_visual_tag(tag_id: str, label: str, value: str) -> bool:
    """Update an existing tag"""
    try:
        db = get_firestore_client()
        doc_ref = db.collection(COL_TAGS).document(tag_id)
        if doc_ref.get().exists:
            doc_ref.update({
                "label": label, 
                "value": value
            })
            return True
        return False
    except Exception as e:
        logger.error(f"Error updating tag: {e}")
        return False

def get_all_tags_raw() -> List[dict]:
    """Get all tags as a flat list"""
    db = get_firestore_client()
    docs = list(db.collection(COL_TAGS).stream())
    
    # Client-side sort (avoids composite index requirement)
    items = []
    for doc in docs:
        d = doc.to_dict()
        items.append({
            "id": doc.id,
            "category": d.get("category"),
            "label": d.get("label"),
            "value": d.get("value"),
            "active": d.get("is_active", True)
        })
    items.sort(key=lambda x: (x.get("category", ""), 0))
    return items

def delete_tag(tag_id: str) -> bool:
    """Delete a tag by ID"""
    try:
        db = get_firestore_client()
        db.collection(COL_TAGS).document(tag_id).delete()
        return True
    except Exception as e:
        logger.error(f"Error deleting tag: {e}")
        return False

# ============ Style Profile Functions ============

def save_style_profile(name: str, config: dict, description: str = "") -> bool:
    """Save a new visual style profile"""
    try:
        db = get_firestore_client()
        
        # Check for existing logic is a bit harder in NoSQL if not using name as ID.
        # But we can query.
        docs = db.collection(COL_STYLE_PROFILES).where("name", "==", name).limit(1).stream()
        existing_ref = None
        for doc in docs:
            existing_ref = doc.reference
            
        data = {
            "name": name,
            "config": config,
            "description": description
        }
            
        if existing_ref:
            existing_ref.update(data)
        else:
            profile_id = str(uuid.uuid4())
            db.collection(COL_STYLE_PROFILES).document(profile_id).set(data)
            
        return True
    except Exception as e:
        logger.error(f"Error saving profile: {e}")
        return False

def list_style_profiles() -> List[dict]:
    """List all saved profiles"""
    db = get_firestore_client()
    docs = db.collection(COL_STYLE_PROFILES).order_by("name").stream()
    
    return [
        {
            "id": doc.id,
            "name": d.get("name"),
            "description": d.get("description"),
            "config": d.get("config")
        }
        for doc in docs for d in [doc.to_dict()]
    ]

def delete_style_profile(profile_id: str) -> bool:
    try:
        db = get_firestore_client()
        db.collection(COL_STYLE_PROFILES).document(profile_id).delete()
        return True
    except Exception:
        return False

# ============ Video Profile Functions ============

def get_video_profiles() -> List[dict]:
    """Get all active video profiles"""
    db = get_firestore_client()
    docs = list(db.collection(COL_VIDEO_PROFILES).stream())
    
    # Client-side filter & sort (avoids composite index requirement)
    items = []
    for doc in docs:
        d = doc.to_dict()
        if d.get("is_active", True):
            items.append({
                "id": doc.id,
                "name_th": d.get("name_th"),
                "name_en": d.get("name_en"),
                "description_th": d.get("description_th"),
                "description_en": d.get("description_en"),
                "icon": d.get("icon"),
                "config": d.get("config")
            })
    items.sort(key=lambda x: x.get("config", {}).get("order_num", 0) if isinstance(x.get("config"), dict) else 0)
    return items

def list_video_profiles() -> List[dict]:
    """List all video profiles (admin)"""
    db = get_firestore_client()
    docs = list(db.collection(COL_VIDEO_PROFILES).stream())
    
    items = []
    for doc in docs:
        d = doc.to_dict()
        items.append({
            "id": doc.id,
            "name_th": d.get("name_th"),
            "name_en": d.get("name_en"),
            "description_th": d.get("description_th"),
            "description_en": d.get("description_en"),
            "icon": d.get("icon"),
            "config": d.get("config"),
            "is_system": d.get("is_system", False)
        })
    items.sort(key=lambda x: d.get("order_num", 0))
    return items

def get_video_profile(profile_id: str) -> Optional[dict]:
    """Get single profile"""
    db = get_firestore_client()
    doc = db.collection(COL_VIDEO_PROFILES).document(profile_id).get()
    
    if doc.exists:
        d = doc.to_dict()
        d["id"] = doc.id
        return d
    return None

def update_video_profile(profile_id: str, config: dict, name_th: str = None, name_en: str = None, description_th: str = None, description_en: str = None) -> bool:
    try:
        db = get_firestore_client()
        doc_ref = db.collection(COL_VIDEO_PROFILES).document(profile_id)
        
        updates = {"config": config}
        if name_th: updates["name_th"] = name_th
        if name_en: updates["name_en"] = name_en
        if description_th: updates["description_th"] = description_th
        if description_en: updates["description_en"] = description_en
        
        doc_ref.update(updates)
        return True
    except Exception:
        return False

# ============ Content Category Functions ============

def get_content_categories() -> List[dict]:
    db = get_firestore_client()
    docs = list(db.collection(COL_CATEGORIES).stream())
    
    # Client-side filter & sort
    items = []
    for doc in docs:
        d = doc.to_dict()
        if d.get("is_active", True):
            items.append({
                "id": doc.id,
                "name_th": d.get("name_th"),
                "name_en": d.get("name_en"),
                "description": d.get("description"),
                "icon": d.get("icon")
            })
    items.sort(key=lambda x: 0)
    return items

# ============ Target Audience Functions ============

def get_target_audiences() -> List[dict]:
    db = get_firestore_client()
    docs = list(db.collection(COL_AUDIENCES).stream())
    
    # Client-side filter & sort
    items = []
    for doc in docs:
        d = doc.to_dict()
        if d.get("is_active", True):
            items.append({
                "id": doc.id,
                "name_th": d.get("name_th"),
                "name_en": d.get("name_en"),
                "age_range": d.get("age_range"),
                "description": d.get("description")
            })
    items.sort(key=lambda x: 0)
    return items

# ============ Content Goal Functions ============

def get_content_goals() -> List[dict]:
    db = get_firestore_client()
    docs = list(db.collection(COL_GOALS).stream())
    
    # Client-side filter & sort
    items = []
    for doc in docs:
        d = doc.to_dict()
        if d.get("is_active", True):
            items.append({
                "id": doc.id,
                "name_th": d.get("name_th"),
                "name_en": d.get("name_en"),
                "description": d.get("description"),
                "icon": d.get("icon"),
                "prompt_hint": d.get("prompt_hint")
            })
    items.sort(key=lambda x: 0)
    return items

# ============ Aliases ============

add_tag = add_visual_tag
get_all_style_presets = list_style_profiles
save_style_preset = save_style_profile
delete_style_preset = delete_style_profile
