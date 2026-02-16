"""
Project Management Utilities
Handles project CRUD operations with database and JSON fallback
"""
import streamlit as st
import json
import logging
from pathlib import Path
from typing import Optional

# Import from core
from src.core.models import Project
from src.core.database import (
    db_save_project,
    db_load_project,
    db_list_projects,
    db_delete_project
)
from src.config.settings import settings

logger = logging.getLogger("vdo_content.project_manager")

# Lazy database availability check — do NOT call init_db() at import time
_database_checked = False
DATABASE_AVAILABLE = False


def _check_database():
    """Check database availability (lazy, called on first use)"""
    global _database_checked, DATABASE_AVAILABLE
    if not _database_checked:
        try:
            from src.core.database import init_db
            init_db()
            DATABASE_AVAILABLE = True
        except Exception as e:
            logger.warning(f"Database not available: {e}")
            DATABASE_AVAILABLE = False
        _database_checked = True
    return DATABASE_AVAILABLE



import re
import uuid
import shutil

# ... imports ...

def _sanitize_id(val: str) -> str:
    """Ensure val is a valid UUID string, generate new if invalid"""
    val = str(val).strip()
    try:
        # Check if it's a valid UUID
        uuid.UUID(val)
        return val
    except (ValueError, AttributeError):
        pass
    
    # If it's a path, try to extract basename if it looks like uuid
    if "/" in val or "\\" in val:
        base = Path(val).name
        try:
            uuid.UUID(base)
            return base
        except ValueError:
            pass
            
    # Completely invalid/empty -> generate new
    new_id = str(uuid.uuid4())
    logger.warning(f"Sanitizing invalid ID '{val[:50]}...' -> generated {new_id}")
    return new_id


def save_project(project: Project) -> str:
    """Save project to database (or JSON fallback)"""
    # CRITICAL FIX: Sanitize project_id to prevent "badly formed hexadecimal UUID string"
    # and "File exists" errors if ID became a file path
    original_id = project.project_id
    safe_id = _sanitize_id(original_id)
    
    if safe_id != original_id:
        logger.warning(f"Correcting corrupted project_id: {original_id!r} -> {safe_id}")
        project.project_id = safe_id
        # Update session state reference if accessible (Streamlit hack)
        if st and "current_project" in st.session_state:
             if st.session_state.current_project.project_id == original_id:
                 st.session_state.current_project.project_id = safe_id

    project_data = project.model_dump(mode="json")
    # Ensure dict has correct ID
    project_data["project_id"] = safe_id
    project_data["id"] = safe_id
    
    # 1. Try DB Save
    if _check_database():
        try:
            # db_save_project returns the (possibly new) UUID string
            saved_id = db_save_project(project_data)
            if saved_id and saved_id != safe_id:
                project.project_id = saved_id
                safe_id = saved_id
            # Invalidate cache so load_project returns fresh data
            _invalidate_project_cache()
            return safe_id
        except Exception as e:
            if st:
                # Show error but continue to JSON fallback
                # Make error message less scary if it's just a DB glich
                logger.error(f"DB save failed: {e}")
                st.warning(f"บันทึกลงฐานข้อมูลไม่สำเร็จ ({e}) - กำลังบันทึกเป็นไฟล์สำรอง...")
    
    # 2. JSON Fallback
    try:
        DATA_DIR = settings.data_dir
        project_dir = DATA_DIR / safe_id
        
        # FIX: If 'project_dir' exists as a FILE (due to previous bug), delete it
        if project_dir.is_file():
            logger.warning(f"Removing file conflict at {project_dir}")
            project_dir.unlink()
            
        project_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"JSON fallback saving project {safe_id} to {project_dir}")
        project_file = project_dir / "project.json"
        
        with open(project_file, "w", encoding="utf-8") as f:
            json.dump(project_data, f, ensure_ascii=False, indent=2, default=str)
            
    except Exception as e:
        logger.error(f"JSON fallback save failed: {e}")
        if st:
            st.error(f"❌ บันทึกไฟล์ไม่สำเร็จ: {e}")
    
    # Invalidate cache so load_project returns fresh data
    _invalidate_project_cache()
    return safe_id


@st.cache_data(ttl=300)  # Cache for 5 minutes
def _load_project_cached(project_id: str) -> Project:
    """Load project from database (or JSON fallback) — cached version"""
    if _check_database():
        try:
            data = db_load_project(project_id)
            if data:
                return _safe_create_project(data, source="DB")
        except Exception as e:
            if st:
                st.warning(f"DB load failed: {e}. Using JSON fallback.")
    
    # JSON fallback
    DATA_DIR = settings.data_dir
    project_file = DATA_DIR / project_id / "project.json"
    if not project_file.exists():
        return None
    with open(project_file, "r", encoding="utf-8") as f:
        data = json.load(f)
    return _safe_create_project(data, source="JSON")


def load_project(project_id: str) -> Project:
    """Load project — public API that delegates to cached version"""
    return _load_project_cached(project_id)


def _invalidate_project_cache():
    """Clear the load_project and list_projects caches"""
    try:
        _load_project_cached.clear()
        list_projects.clear()
    except Exception:
        pass  # Gracefully handle if cache is not available (e.g., outside Streamlit)


def _safe_create_project(data: dict, source: str = "unknown") -> Project:
    """
    Safely create a Project from dict data with validation error handling.
    If full validation fails, attempts partial load by stripping invalid fields.
    """
    import logging
    logger = logging.getLogger("vdo_content.project_manager")
    
    try:
        return Project(**data)
    except Exception as e:
        logger.warning(f"Project validation failed ({source}): {e}")
        
        # Attempt partial load — keep only fields the model accepts
        try:
            valid_fields = set(Project.model_fields.keys())
            cleaned = {k: v for k, v in data.items() if k in valid_fields}
            project = Project(**cleaned)
            logger.info(f"Partial project loaded from {source} (dropped invalid fields)")
            return project
        except Exception as e2:
            logger.error(f"Partial load also failed: {e2}")
            # Last resort — minimal project
            return Project(
                project_id=data.get("project_id", data.get("id", "")),
                title=data.get("title", "Untitled (Recovery)"),
                topic=data.get("topic", ""),
            )


def delete_project(project_id: str) -> bool:
    """Delete project from database (or JSON fallback)"""
    deleted = False
    if _check_database():
        try:
            deleted = db_delete_project(project_id)
        except Exception as e:
            logger.warning(f"DB delete failed: {e}")
    
    # JSON fallback — also clean up JSON if it exists
    import shutil
    DATA_DIR = settings.data_dir
    project_dir = DATA_DIR / project_id
    if project_dir.exists():
        shutil.rmtree(project_dir)
        deleted = True
    
    # Invalidate cache so deleted project is not returned
    if deleted:
        _invalidate_project_cache()
    
    return deleted


@st.cache_data(ttl=60)  # Cache for 1 minute (shorter for list view)
def list_projects() -> list[dict]:
    """List all projects from database (or JSON fallback)"""
    if _check_database():
        try:
            return db_list_projects()
        except Exception as e:
            if st:
                st.warning(f"DB list failed: {e}. Using JSON fallback.")
    
    # JSON fallback
    DATA_DIR = settings.data_dir
    projects = []
    if DATA_DIR.exists():
        for project_dir in DATA_DIR.iterdir():
            if project_dir.is_dir():
                project_file = project_dir / "project.json"
                if project_file.exists():
                    try:
                        with open(project_file, "r", encoding="utf-8") as f:
                            data = json.load(f)
                            projects.append({
                                "id": data["project_id"],
                                "title": data["title"],
                                "status": data.get("status", "draft"),
                                "scenes": len(data.get("scenes", [])),
                                "created": data.get("created_at", ""),
                                "topic": data.get("topic", "")[:50]
                            })
                    except (json.JSONDecodeError, KeyError, OSError) as e:
                        logger.debug(f"Skipping invalid project file {p}: {e}")
    return sorted(projects, key=lambda x: x["created"], reverse=True)
