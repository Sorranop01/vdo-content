"""
Templates API Router
VDO Content V2 - FastAPI

Endpoints for template management.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, Literal

router = APIRouter(prefix="/api/templates", tags=["Templates"])


class TemplateInfo(BaseModel):
    """Template summary"""
    id: str
    name: str
    description: str
    category: str
    target_duration: int
    scene_count: int
    is_builtin: bool


class TemplateDetail(TemplateInfo):
    """Full template details"""
    default_style: str
    system_prompt: str
    scene_templates: list[dict]
    visual_theme: str
    aspect_ratio: str


class CreateTemplateRequest(BaseModel):
    """Request to save project as template"""
    project_id: str
    name: str
    description: str
    category: str = "custom"


@router.get("", response_model=list[TemplateInfo])
async def list_templates(category: Optional[str] = None):
    """List all available templates"""
    from core.templates import TemplateManager
    
    manager = TemplateManager()
    templates = manager.list_templates(category)
    
    return [
        TemplateInfo(
            id=t.id,
            name=t.name,
            description=t.description,
            category=t.category,
            target_duration=t.target_duration,
            scene_count=t.scene_count,
            is_builtin=t.is_builtin
        )
        for t in templates
    ]


@router.get("/{template_id}", response_model=TemplateDetail)
async def get_template(template_id: str):
    """Get template details"""
    from core.templates import TemplateManager
    
    manager = TemplateManager()
    template = manager.get_template(template_id)
    
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    
    return TemplateDetail(
        id=template.id,
        name=template.name,
        description=template.description,
        category=template.category,
        target_duration=template.target_duration,
        scene_count=template.scene_count,
        is_builtin=template.is_builtin,
        default_style=template.default_style,
        system_prompt=template.system_prompt,
        scene_templates=template.scene_templates,
        visual_theme=template.visual_theme,
        aspect_ratio=template.aspect_ratio
    )


@router.post("/{template_id}/apply")
async def apply_template(template_id: str, topic: str, title: Optional[str] = None):
    """Create a new project from template"""
    from core.templates import TemplateManager
    from core.database import db_save_project, DATABASE_AVAILABLE
    
    manager = TemplateManager()
    
    try:
        project = manager.apply_template(template_id, topic, title)
        
        # Save to database if available
        if DATABASE_AVAILABLE:
            db_save_project(project)
        
        return {
            "success": True,
            "project_id": project.project_id,
            "title": project.title,
            "scene_count": len(project.scenes)
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.delete("/{template_id}")
async def delete_template(template_id: str):
    """Delete a custom template"""
    from core.templates import TemplateManager
    
    manager = TemplateManager()
    
    try:
        deleted = manager.delete_template(template_id)
        if deleted:
            return {"success": True, "message": "Template deleted"}
        raise HTTPException(status_code=404, detail="Template not found")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/categories/list")
async def list_categories():
    """Get template categories"""
    from core.templates import TemplateManager
    
    manager = TemplateManager()
    categories = manager.get_categories()
    
    return [{"id": c[0], "name": c[1]} for c in categories]
