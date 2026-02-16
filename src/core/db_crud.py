"""
Database CRUD Operations
Project and Draft CRUD operations.
"""

import os
import uuid
import logging
from datetime import datetime, timezone
from typing import Optional

from .db_engine import get_db
from .db_models import (
    ProjectDB, SceneDB, AudioSegmentDB, DraftDB,
    UsageLogDB, MediaAssetDB
)

logger = logging.getLogger("vdo_content.database")


def _safe_uuid(value: str) -> uuid.UUID:
    """Parse a string to UUID, raise ValueError with clear message on failure"""
    if not value or not str(value).strip():
        raise ValueError(f"Empty or None project_id")
    try:
        return uuid.UUID(str(value).strip())
    except (ValueError, AttributeError) as e:
        raise ValueError(f"Invalid UUID: {value!r}") from e


# ============ Project Conversion ============

def project_to_dict(project: ProjectDB) -> dict:
    """Convert ProjectDB to dict for Pydantic model"""
    return {
        "project_id": str(project.id),
        "title": project.title,
        "topic": project.topic,
        "status": project.status,
        "default_style": project.default_style,
        "video_profile_id": project.video_profile_id,
        "target_duration": project.target_duration,
        "character_reference": project.character_reference,
        "full_script": project.full_script or "",
        "style_instructions": project.style_instructions or "",
        "script_text": project.script_text or "",
        "audio_path": project.audio_path or "",
        "audio_duration": project.audio_duration or 0.0,
        "drive_folder_link": project.drive_folder_link or "",
        "aspect_ratio": project.aspect_ratio or "16:9",
        # Step 2 fields
        "content_goal": project.content_goal or "",
        "content_category": project.content_category or "",
        "target_audience": project.target_audience or "",
        "content_description": project.content_description or "",
        "platforms": project.platforms or [],
        "video_format": project.video_format or "",
        # Step 3 fields
        "voice_personality": project.voice_personality or "",
        "workflow_step": project.workflow_step or 0,
        # Step 1 metadata
        "description": project.description or "",
        "project_date": project.project_date,
        # Step 4 fields
        "video_type": project.video_type or "",
        "visual_theme": project.visual_theme or "",
        "directors_note": project.directors_note or "",
        "direction_style": project.direction_style,
        "direction_custom_notes": project.direction_custom_notes or "",
        # Step 5 fields
        "upload_folder": project.upload_folder or "",
        "uploaded_files": project.uploaded_files or [],
        "final_video_path": project.final_video_path,
        # Prompt style config
        "prompt_style_config": project.prompt_style_config,
        # FK references
        "content_category_id": str(project.content_category_id) if project.content_category_id else None,
        "target_audience_id": str(project.target_audience_id) if project.target_audience_id else None,
        "content_goal_id": str(project.content_goal_id) if project.content_goal_id else None,
        "generated_content": project.generated_content or "",
        "proposal": project.proposal_data,  # DB column is proposal_data, Pydantic field is proposal
        "created_at": project.created_at,
        "updated_at": project.updated_at,
        "scenes": [
            {
                "scene_id": str(s.id),
                "order": s.order_num,
                "narration_text": s.narration_text or "",
                "veo_prompt": s.veo_prompt or "",
                "emotion": s.emotion or "neutral",
                "visual_style": s.visual_style or "",
                "subject_description": s.subject_description or "",
                "start_time": s.start_time or 0.0,
                "end_time": s.end_time or 0.0,
                "estimated_duration": s.estimated_duration or 0.0,
                "video_generated": s.video_generated,
                "audio_synced": s.audio_synced,
                "stock_video_url": s.stock_video_url or ""
            }
            for s in project.scenes
        ],
        "audio_segments": [
            {
                "order": a.order_num,
                "start_time": a.start_time,
                "end_time": a.end_time,
                "duration": a.duration,
                "text_content": a.text_content or "",
                "is_edited": a.is_edited
            }
            for a in project.audio_segments
        ]
    }


# ============ Project CRUD ============

def db_save_project(project_data: dict) -> str:
    """Save or update project in database"""
    with get_db() as db:
        project_id = project_data.get("project_id")
        
        # Try to find existing project
        existing = None
        if project_id:
            try:
                pid = _safe_uuid(project_id)
                existing = db.query(ProjectDB).filter(ProjectDB.id == pid).first()
            except ValueError:
                logger.warning(f"Invalid project_id format: {project_id!r}, treating as new project")
                existing = None
        
        # Sanitize FK UUID fields — empty strings become None
        def _clean_fk(key):
            val = project_data.get(key)
            if val and str(val).strip():
                try:
                    uuid.UUID(str(val))
                    return val
                except (ValueError, AttributeError):
                    return None
            return None
        
        content_category_id = _clean_fk("content_category_id")
        content_goal_id = _clean_fk("content_goal_id")
        target_audience_id = _clean_fk("target_audience_id")
        
        # Parse project_date if string
        project_date = project_data.get("project_date")
        if isinstance(project_date, str):
            try:
                from datetime import datetime as dt
                project_date = dt.fromisoformat(project_date.replace("Z", "+00:00"))
            except (ValueError, TypeError):
                project_date = None
        
        if existing:
            # Update existing
            existing.title = project_data.get("title", existing.title)
            existing.topic = project_data.get("topic")
            existing.status = project_data.get("status", "draft")
            existing.default_style = project_data.get("default_style")
            existing.video_profile_id = project_data.get("video_profile_id")
            existing.target_duration = project_data.get("target_duration", 60)
            existing.character_reference = project_data.get("character_reference")
            existing.full_script = project_data.get("full_script")
            existing.style_instructions = project_data.get("style_instructions")
            existing.script_text = project_data.get("script_text")
            existing.audio_path = project_data.get("audio_path")
            existing.audio_duration = project_data.get("audio_duration", 0.0)
            existing.drive_folder_link = project_data.get("drive_folder_link")
            existing.aspect_ratio = project_data.get("aspect_ratio", "16:9")
            existing.generated_content = project_data.get("generated_content")
            existing.proposal_data = project_data.get("proposal")
            # Step 2 fields
            existing.content_goal = project_data.get("content_goal")
            existing.content_category = project_data.get("content_category")
            existing.target_audience = project_data.get("target_audience")
            existing.content_description = project_data.get("content_description")
            existing.platforms = project_data.get("platforms", [])
            existing.video_format = project_data.get("video_format")
            # Step 3 fields
            existing.voice_personality = project_data.get("voice_personality")
            existing.workflow_step = project_data.get("workflow_step", 0)
            # Step 1 metadata
            existing.description = project_data.get("description")
            existing.project_date = project_date
            # Step 4 fields
            existing.video_type = project_data.get("video_type")
            existing.visual_theme = project_data.get("visual_theme")
            existing.directors_note = project_data.get("directors_note")
            existing.direction_style = project_data.get("direction_style")
            existing.direction_custom_notes = project_data.get("direction_custom_notes")
            # Step 5 fields
            existing.upload_folder = project_data.get("upload_folder")
            existing.uploaded_files = project_data.get("uploaded_files", [])
            existing.final_video_path = project_data.get("final_video_path")
            # Config & FK references
            existing.prompt_style_config = project_data.get("prompt_style_config")
            existing.content_category_id = content_category_id
            existing.content_goal_id = content_goal_id
            existing.target_audience_id = target_audience_id
            existing.updated_at = datetime.now(timezone.utc)
            
            # Update scenes
            db.query(SceneDB).filter(SceneDB.project_id == existing.id).delete()
            for scene_data in project_data.get("scenes", []):
                scene = SceneDB(
                    project_id=existing.id,
                    order_num=scene_data.get("order", 1),
                    narration_text=scene_data.get("narration_text"),
                    veo_prompt=scene_data.get("veo_prompt"),
                    emotion=scene_data.get("emotion"),
                    visual_style=scene_data.get("visual_style"),
                    subject_description=scene_data.get("subject_description"),
                    start_time=scene_data.get("start_time", 0.0),
                    end_time=scene_data.get("end_time", 0.0),
                    estimated_duration=scene_data.get("estimated_duration", 0.0),
                    video_generated=scene_data.get("video_generated", False),
                    audio_synced=scene_data.get("audio_synced", False)
                )
                db.add(scene)
            
            # Update audio segments
            db.query(AudioSegmentDB).filter(AudioSegmentDB.project_id == existing.id).delete()
            for seg_data in project_data.get("audio_segments", []):
                seg = AudioSegmentDB(
                    project_id=existing.id,
                    order_num=seg_data.get("order", 1),
                    start_time=seg_data.get("start_time", 0.0),
                    end_time=seg_data.get("end_time", 0.0),
                    duration=seg_data.get("duration", 0.0),
                    text_content=seg_data.get("text_content"),
                    is_edited=seg_data.get("is_edited", False)
                )
                db.add(seg)
            
            return str(existing.id)
        else:
            # Create new — use project_id if valid UUID, else generate
            new_id = None
            if project_id:
                try:
                    new_id = _safe_uuid(project_id)
                except ValueError:
                    new_id = uuid.uuid4()
            
            new_project = ProjectDB(
                id=new_id,  # None → uses column default (uuid4)
                title=project_data.get("title", "Untitled"),
                topic=project_data.get("topic"),
                status=project_data.get("status", "draft"),
                default_style=project_data.get("default_style"),
                video_profile_id=project_data.get("video_profile_id"),
                target_duration=project_data.get("target_duration", 60),
                character_reference=project_data.get("character_reference"),
                full_script=project_data.get("full_script"),
                style_instructions=project_data.get("style_instructions"),
                script_text=project_data.get("script_text"),
                audio_path=project_data.get("audio_path"),
                audio_duration=project_data.get("audio_duration", 0.0),
                drive_folder_link=project_data.get("drive_folder_link"),
                aspect_ratio=project_data.get("aspect_ratio", "16:9"),
                generated_content=project_data.get("generated_content"),
                proposal_data=project_data.get("proposal"),
                # Step 2 fields
                content_goal=project_data.get("content_goal"),
                content_category=project_data.get("content_category"),
                target_audience=project_data.get("target_audience"),
                content_description=project_data.get("content_description"),
                platforms=project_data.get("platforms", []),
                video_format=project_data.get("video_format"),
                # Step 3 fields
                voice_personality=project_data.get("voice_personality"),
                workflow_step=project_data.get("workflow_step", 0),
                # Step 1 metadata
                description=project_data.get("description"),
                project_date=project_date,
                # Step 4 fields
                video_type=project_data.get("video_type"),
                visual_theme=project_data.get("visual_theme"),
                directors_note=project_data.get("directors_note"),
                direction_style=project_data.get("direction_style"),
                direction_custom_notes=project_data.get("direction_custom_notes"),
                # Step 5 fields
                upload_folder=project_data.get("upload_folder"),
                uploaded_files=project_data.get("uploaded_files", []),
                final_video_path=project_data.get("final_video_path"),
                # Config & FK references
                prompt_style_config=project_data.get("prompt_style_config"),
                content_category_id=content_category_id,
                content_goal_id=content_goal_id,
                target_audience_id=target_audience_id,
            )
            db.add(new_project)
            db.flush()  # Get ID
            
            # Add scenes
            for scene_data in project_data.get("scenes", []):
                scene = SceneDB(
                    project_id=new_project.id,
                    order_num=scene_data.get("order", 1),
                    narration_text=scene_data.get("narration_text"),
                    veo_prompt=scene_data.get("veo_prompt"),
                    emotion=scene_data.get("emotion"),
                    visual_style=scene_data.get("visual_style"),
                    subject_description=scene_data.get("subject_description"),
                    start_time=scene_data.get("start_time", 0.0),
                    end_time=scene_data.get("end_time", 0.0),
                    estimated_duration=scene_data.get("estimated_duration", 0.0),
                    video_generated=scene_data.get("video_generated", False),
                    audio_synced=scene_data.get("audio_synced", False)
                )
                db.add(scene)
            
            # Add audio segments
            for seg_data in project_data.get("audio_segments", []):
                seg = AudioSegmentDB(
                    project_id=new_project.id,
                    order_num=seg_data.get("order", 1),
                    start_time=seg_data.get("start_time", 0.0),
                    end_time=seg_data.get("end_time", 0.0),
                    duration=seg_data.get("duration", 0.0),
                    text_content=seg_data.get("text_content"),
                    is_edited=seg_data.get("is_edited", False)
                )
                db.add(seg)
            
            return str(new_project.id)


def db_load_project(project_id: str) -> Optional[dict]:
    """Load project from database"""
    with get_db() as db:
        project = db.query(ProjectDB).filter(ProjectDB.id == _safe_uuid(project_id)).first()
        if project:
            return project_to_dict(project)
        return None


def db_list_projects() -> list[dict]:
    """List all projects"""
    with get_db() as db:
        projects = db.query(ProjectDB).order_by(ProjectDB.created_at.desc()).all()
        return [
            {
                "id": str(p.id),
                "title": p.title,
                "status": p.status,
                "scenes": len(p.scenes),
                "created": str(p.created_at) if p.created_at else "",
                "topic": (p.topic or "")[:50]
            }
            for p in projects
        ]


def db_delete_project(project_id: str) -> bool:
    """Delete a project"""
    with get_db() as db:
        project = db.query(ProjectDB).filter(ProjectDB.id == _safe_uuid(project_id)).first()
        if project:
            db.delete(project)
            return True
        return False


def db_update_project_metadata(project_id: str, metadata: dict) -> bool:
    """Update project metadata fields"""
    with get_db() as db:
        project = db.query(ProjectDB).filter(ProjectDB.id == _safe_uuid(project_id)).first()
        if project:
            for key, value in metadata.items():
                if hasattr(project, key):
                    setattr(project, key, value)
            project.updated_at = datetime.now(timezone.utc)
            return True
        return False


# ============ Draft CRUD ============

def db_save_draft(session_id: str, draft_type: str, content: dict) -> str:
    """Save or update a draft"""
    with get_db() as db:
        draft = db.query(DraftDB).filter(
            DraftDB.session_id == session_id,
            DraftDB.draft_type == draft_type
        ).first()
        
        if draft:
            draft.content = content
            draft.updated_at = datetime.now(timezone.utc)
        else:
            draft = DraftDB(
                session_id=session_id,
                draft_type=draft_type,
                content=content
            )
            db.add(draft)
        
        db.flush()
        return str(draft.id)


def db_load_draft(session_id: str, draft_type: str) -> Optional[dict]:
    """Load a draft by session and type"""
    with get_db() as db:
        draft = db.query(DraftDB).filter(
            DraftDB.session_id == session_id,
            DraftDB.draft_type == draft_type
        ).first()
        
        if draft:
            return draft.content
        return None


def db_delete_draft(session_id: str, draft_type: str) -> bool:
    """Delete a draft after it's saved as project"""
    with get_db() as db:
        draft = db.query(DraftDB).filter(
            DraftDB.session_id == session_id,
            DraftDB.draft_type == draft_type
        ).first()
        
        if draft:
            db.delete(draft)
            return True
        return False


def db_list_drafts(session_id: str) -> list[dict]:
    """List all drafts for a session"""
    with get_db() as db:
        drafts = db.query(DraftDB).filter(
            DraftDB.session_id == session_id
        ).order_by(DraftDB.updated_at.desc()).all()
        
        return [
            {
                "id": str(d.id),
                "draft_type": d.draft_type,
                "content": d.content,
                "updated_at": d.updated_at.isoformat() if d.updated_at else None
            }
            for d in drafts
        ]


# ============ Utility Functions ============

def log_api_usage(service: str, operation: str, status: str, project_id: str = None, tokens: int = 0, duration: float = 0.0, meta: dict = None):
    """Log AI usage safely"""
    with get_db() as db:
        try:
            log = UsageLogDB(
                service_name=service,
                operation=operation,
                status=status,
                project_id=_safe_uuid(project_id) if project_id else None,
                tokens_used=tokens,
                duration_seconds=duration,
                metadata_json=meta or {}
            )
            db.add(log)
        except Exception as e:
            logger.warning(f"Failed to log usage: {e}")

def save_media_asset(file_path: str, file_type: str, asset_type: str, project_id: str = None) -> str:
    """Register a media file in the database"""
    with get_db() as db:
        try:
            size = 0
            if os.path.exists(file_path):
                size = os.path.getsize(file_path)
                
            asset = MediaAssetDB(
                file_path=file_path,
                file_type=file_type,
                asset_type=asset_type,
                file_size_bytes=size,
                project_id=_safe_uuid(project_id) if project_id else None
            )
            db.add(asset)
            db.flush()
            return str(asset.id)
        except Exception as e:
            logger.warning(f"Failed to save asset: {e}")
            return ""

def get_project_assets(project_id: str) -> list[dict]:
    """Get all assets for a project"""
    with get_db() as db:
        assets = db.query(MediaAssetDB).filter(MediaAssetDB.project_id == _safe_uuid(project_id)).all()
        return [
            {
                "id": str(a.id),
                "path": a.file_path,
                "type": a.asset_type,
                "size_kb": round(a.file_size_bytes / 1024, 1),
                "created": a.created_at.isoformat()
            }
            for a in assets
        ]


# ============ Aliases ============

db_get_all_projects = db_list_projects
db_get_project = db_load_project
