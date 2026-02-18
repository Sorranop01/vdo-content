"""
Firestore CRUD Operations
Project and Draft CRUD operations using Google Cloud Firestore.
Replaces the SQL-based db_crud.py.
"""

import logging
import uuid
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any

from google.cloud import firestore
from .firestore_client import get_firestore_client, get_db

logger = logging.getLogger("vdo_content.database")

# Collection names
COL_PROJECTS = "projects"
COL_DRAFTS = "drafts"
COL_ASSETS = "media_assets"
COL_USAGE = "usage_logs"

def _get_current_utc():
    return datetime.now(timezone.utc)

def _safe_uuid(value: str) -> str:
    """Ensure value is a valid UUID string"""
    if not value:
        return str(uuid.uuid4())
    try:
        uuid.UUID(str(value))
        return str(value)
    except ValueError:
        return str(uuid.uuid4())

# ============ Project Conversion ============

def _snapshot_to_dict(doc: firestore.DocumentSnapshot) -> dict:
    """Convert Firestore document to dict (Pydantic compatible)"""
    if not doc.exists:
        return {}
    
    data = doc.to_dict()
    data["project_id"] = doc.id
    
    # Handle timestamps - Firestore returns datetime objects, which is what we want
    # But Pydantic might expect compatible types. 
    # If using Pydantic V2, it handles datetime objects fine.
    
    return data

# ============ Project CRUD ============

def db_save_project(project_data: dict) -> str:
    """Save or update project in Firestore"""
    db = get_firestore_client()
    
    project_id = project_data.get("project_id")
    if not project_id:
        project_id = str(uuid.uuid4())
    
    # Ensure ID is valid UUID string
    try:
        uuid.UUID(str(project_id))
    except ValueError:
        project_id = str(uuid.uuid4())
        
    # Prepare data for Firestore
    # We flatten some structures or keep them as JSON/Map depending on use case.
    # The SQL version had `scenes` and `audio_segments` as separate tables.
    # In Firestore, we will embed them as arrays/maps within the project document 
    # for simpler atomic reads/writes, as they are part of the project aggregate.
    
    # Clean project_date
    project_date = project_data.get("project_date")
    if isinstance(project_date, str):
        try:
            project_date = datetime.fromisoformat(project_date.replace("Z", "+00:00"))
        except ValueError:
            project_date = None
            
    doc_data = {
        "title": project_data.get("title", "Untitled"),
        "topic": project_data.get("topic"),
        "status": project_data.get("status", "draft"),
        "default_style": project_data.get("default_style"),
        "video_profile_id": project_data.get("video_profile_id"),
        "target_duration": project_data.get("target_duration", 60),
        "character_reference": project_data.get("character_reference"),
        "full_script": project_data.get("full_script"),
        "style_instructions": project_data.get("style_instructions"),
        "script_text": project_data.get("script_text"),
        "audio_path": project_data.get("audio_path"),
        "audio_duration": project_data.get("audio_duration", 0.0),
        "drive_folder_link": project_data.get("drive_folder_link"),
        "aspect_ratio": project_data.get("aspect_ratio", "16:9"),
        
        # Step 2
        "content_goal": project_data.get("content_goal"),
        "content_category": project_data.get("content_category"),
        "target_audience": project_data.get("target_audience"),
        "content_description": project_data.get("content_description"),
        "platforms": project_data.get("platforms", []),
        "video_format": project_data.get("video_format"),
        
        # Step 3
        "voice_personality": project_data.get("voice_personality"),
        "workflow_step": project_data.get("workflow_step", 0),
        
        # Metadata
        "description": project_data.get("description"),
        "project_date": project_date,
        
        # Step 4
        "video_type": project_data.get("video_type"),
        "visual_theme": project_data.get("visual_theme"),
        "directors_note": project_data.get("directors_note"),
        "direction_style": project_data.get("direction_style"),
        "direction_custom_notes": project_data.get("direction_custom_notes"),
        
        # Step 5
        "upload_folder": project_data.get("upload_folder"),
        "uploaded_files": project_data.get("uploaded_files", []),
        "final_video_path": project_data.get("final_video_path"),
        
        # Misc
        "prompt_style_config": project_data.get("prompt_style_config"),
        "generated_content": project_data.get("generated_content"),
        "proposal": project_data.get("proposal"), # Matches Pydantic 'proposal' field name
        
        # Refs
        "content_category_id": project_data.get("content_category_id"),
        "content_goal_id": project_data.get("content_goal_id"),
        "target_audience_id": project_data.get("target_audience_id"),
        
        # Embedded Collections
        "scenes": project_data.get("scenes", []),
        "audio_segments": project_data.get("audio_segments", []),
        
        "updated_at": _get_current_utc()
    }
    
    # Handle creation timestamp
    doc_ref = db.collection(COL_PROJECTS).document(project_id)
    snapshot = doc_ref.get()
    
    if not snapshot.exists:
        doc_data["created_at"] = _get_current_utc()
        doc_ref.set(doc_data)
    else:
        # Merge update
        doc_ref.set(doc_data, merge=True)
        
    return project_id

def db_load_project(project_id: str) -> Optional[dict]:
    """Load project from Firestore"""
    if not project_id:
        return None
        
    db = get_firestore_client()
    doc_ref = db.collection(COL_PROJECTS).document(project_id)
    doc = doc_ref.get()
    
    if doc.exists:
        return _snapshot_to_dict(doc)
    return None

def db_list_projects() -> List[dict]:
    """List all projects ordered by created_at desc"""
    db = get_firestore_client()
    docs = db.collection(COL_PROJECTS)\
             .order_by("created_at", direction=firestore.Query.DESCENDING)\
             .stream()
    
    projects = []
    for doc in docs:
        data = doc.to_dict()
        projects.append({
            "id": doc.id,
            "title": data.get("title", "Untitled"),
            "status": data.get("status", "draft"),
            "scenes": len(data.get("scenes", [])),
            "created": str(data.get("created_at", "")),
            "topic": (data.get("topic") or "")[:50]
        })
    return projects

def db_delete_project(project_id: str) -> bool:
    """Delete a project"""
    if not project_id:
        return False
        
    db = get_firestore_client()
    db.collection(COL_PROJECTS).document(project_id).delete()
    return True

def db_update_project_metadata(project_id: str, metadata: dict) -> bool:
    """Partial update of project metadata"""
    if not project_id:
        return False
        
    db = get_firestore_client()
    doc_ref = db.collection(COL_PROJECTS).document(project_id)
    
    metadata["updated_at"] = _get_current_utc()
    doc_ref.update(metadata)
    return True

# ============ Draft CRUD ============

def db_save_draft(session_id: str, draft_type: str, content: dict) -> str:
    """Save draft"""
    db = get_firestore_client()
    
    # Composite key for uniqueness
    draft_id = f"{session_id}_{draft_type}"
    
    data = {
        "session_id": session_id,
        "draft_type": draft_type,
        "content": content,
        "updated_at": _get_current_utc()
    }
    
    db.collection(COL_DRAFTS).document(draft_id).set(data, merge=True)
    return draft_id

def db_load_draft(session_id: str, draft_type: str) -> Optional[dict]:
    """Load draft content"""
    db = get_firestore_client()
    draft_id = f"{session_id}_{draft_type}"
    doc = db.collection(COL_DRAFTS).document(draft_id).get()
    
    if doc.exists:
        return doc.get("content")
    return None

def db_delete_draft(session_id: str, draft_type: str) -> bool:
    """Delete draft"""
    db = get_firestore_client()
    draft_id = f"{session_id}_{draft_type}"
    db.collection(COL_DRAFTS).document(draft_id).delete()
    return True

def db_list_drafts(session_id: str) -> List[dict]:
    """List drafts for session"""
    db = get_firestore_client()
    docs = db.collection(COL_DRAFTS)\
             .where("session_id", "==", session_id)\
             .order_by("updated_at", direction=firestore.Query.DESCENDING)\
             .stream()
             
    drafts = []
    for doc in docs:
        d = doc.to_dict()
        drafts.append({
            "id": doc.id,
            "draft_type": d.get("draft_type"),
            "content": d.get("content"),
            "updated_at": str(d.get("updated_at"))
        })
    return drafts

# ============ Utils ============

def log_api_usage(service: str, operation: str, status: str, project_id: str = None, tokens: int = 0, duration: float = 0.0, meta: dict = None):
    """Log usage to Firestore (fire & forget)"""
    try:
        db = get_firestore_client()
        db.collection(COL_USAGE).add({
            "service_name": service,
            "operation": operation,
            "status": status,
            "project_id": project_id,
            "tokens_used": tokens,
            "duration_seconds": duration,
            "metadata": meta or {},
            "timestamp": _get_current_utc()
        })
    except Exception as e:
        logger.warning(f"Failed to log usage: {e}")

def save_media_asset(file_path: str, file_type: str, asset_type: str, project_id: str = None) -> str:
    """Log media asset"""
    try:
        db = get_firestore_client()
        
        size = 0
        if os.path.exists(file_path):
            size = os.path.getsize(file_path)
            
        _, doc_ref = db.collection(COL_ASSETS).add({
            "file_path": file_path,
            "file_type": file_type,
            "asset_type": asset_type,
            "file_size_bytes": size,
            "project_id": project_id,
            "created_at": _get_current_utc()
        })
        return doc_ref.id
    except Exception as e:
        logger.warning(f"Failed to save asset log: {e}")
        return ""

def get_project_assets(project_id: str) -> List[dict]:
    """Get assets for project"""
    if not project_id:
        return []
        
    db = get_firestore_client()
    docs = db.collection(COL_ASSETS)\
             .where("project_id", "==", project_id)\
             .order_by("created_at", direction=firestore.Query.DESCENDING)\
             .stream()
             
    assets = []
    for doc in docs:
        a = doc.to_dict()
        assets.append({
            "id": doc.id,
            "path": a.get("file_path"),
            "type": a.get("asset_type"),
            "size_kb": round(a.get("file_size_bytes", 0) / 1024, 1),
            "created": str(a.get("created_at"))
        })
    return assets

# Aliases
db_get_all_projects = db_list_projects
db_get_project = db_load_project
