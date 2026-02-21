"""
VDO Content V2 - FastAPI Backend
RESTful API for project management, generation, and export

Run with: uvicorn src.backend.api.main:app --reload --port 8000
"""

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
import io
import os
import logging

logger = logging.getLogger("vdo_content.api")

# Core imports
from src.core.models import Project, Scene, StoryProposal
from src.core.exporter import ProjectExporter

# Database imports
try:
    from src.core.database import (
        init_db, db_save_project, db_load_project, 
        db_list_projects, db_delete_project
    )
    DATABASE_AVAILABLE = True
except ImportError as e:
    logger.warning(f"Database module not available: {e}")
    DATABASE_AVAILABLE = False

# Initialize FastAPI app
app = FastAPI(
    title="VDO Content API",
    description="API for VDO Content V2 - AI Content Pipeline for Video Creation",
    version="2.2.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware for Streamlit and other clients
# In production, set CORS_ORIGINS env var to restrict allowed origins
cors_origins = os.getenv("CORS_ORIGINS", "http://localhost:8501,http://localhost:3000,http://localhost:8000")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in cors_origins.split(",")],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API Key authentication middleware
try:
    from src.backend.api.auth_middleware import APIKeyMiddleware
    app.add_middleware(APIKeyMiddleware)
except ImportError as e:
    logger.warning(f"Auth middleware not loaded: {e}")

# Mount Phase 2 routers
try:
    from src.backend.api.routers.voice import router as voice_router
    from src.backend.api.routers.templates import router as templates_router
    app.include_router(voice_router)
    app.include_router(templates_router)
except ImportError as e:
    logger.info(f"Phase 2 routers not loaded: {e}")

# Mount Strategy Engine integration router
try:
    from src.backend.api.routers.strategy import router as strategy_router
    app.include_router(strategy_router)
    logger.info("Strategy Engine ingest router loaded")
except ImportError as e:
    logger.info(f"Strategy Engine router not loaded: {e}")



# ============ Schemas ============

class ProjectCreate(BaseModel):
    """Schema for creating a new project — synced with Pydantic Project model"""
    # Step 1: Project metadata
    title: str
    topic: str
    description: str = ""
    target_duration: int = 60
    character_reference: str = ""
    aspect_ratio: str = "16:9"
    default_style: str = "documentary"
    video_profile_id: Optional[str] = None
    
    # Step 2: Content planning
    content_goal: Optional[str] = None
    content_category: Optional[str] = None
    target_audience: Optional[str] = None
    content_description: Optional[str] = None
    platforms: Optional[List[str]] = None
    video_format: Optional[str] = None
    voice_personality: Optional[str] = None
    
    # Step 4: Video prompt
    video_type: Optional[str] = None
    visual_theme: Optional[str] = None


class ProjectUpdate(BaseModel):
    """Schema for updating a project — all fields optional"""
    # Step 1
    title: Optional[str] = None
    topic: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    target_duration: Optional[int] = None
    character_reference: Optional[str] = None
    aspect_ratio: Optional[str] = None
    default_style: Optional[str] = None
    video_profile_id: Optional[str] = None
    
    # Step 2: Content
    content_goal: Optional[str] = None
    content_category: Optional[str] = None
    target_audience: Optional[str] = None
    content_description: Optional[str] = None
    platforms: Optional[List[str]] = None
    video_format: Optional[str] = None
    voice_personality: Optional[str] = None
    
    # Step 3: Script
    full_script: Optional[str] = None
    script_text: Optional[str] = None
    style_instructions: Optional[str] = None
    
    # Step 4: Video prompt
    video_type: Optional[str] = None
    visual_theme: Optional[str] = None
    directors_note: Optional[str] = None
    direction_style: Optional[str] = None
    direction_custom_notes: Optional[str] = None
    
    # Step 5: Upload
    drive_folder_link: Optional[str] = None
    upload_folder: Optional[str] = None
    
    # Workflow tracking
    workflow_step: Optional[int] = None


class ProjectResponse(BaseModel):
    """Schema for project response"""
    project_id: str
    title: str
    topic: str
    status: str
    description: str = ""
    default_style: str = "documentary"
    target_duration: int = 60
    workflow_step: int = 0
    scene_count: int = 0
    total_duration: float = 0.0
    video_type: Optional[str] = None
    content_goal: Optional[str] = None
    drive_folder_link: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None


class SceneCreate(BaseModel):
    """Schema for creating a scene"""
    order: int
    narration_text: str
    start_time: float = 0.0
    end_time: float = 0.0
    veo_prompt: str = ""
    visual_style: str = "documentary"
    emotion: str = "neutral"


class GeneratePromptsRequest(BaseModel):
    """Schema for generating prompts"""
    project_id: str
    style_preset: str = "documentary"
    character_reference: str = ""


class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    version: str
    database: bool
    timestamp: datetime


# ============ Health Check ============

@app.get("/health", response_model=HealthResponse, tags=["System"])
async def health_check():
    """Check API health and dependencies"""
    return HealthResponse(
        status="healthy",
        version="2.2.0",
        database=DATABASE_AVAILABLE,
        timestamp=datetime.now()
    )


@app.get("/", tags=["System"])
async def root():
    """Welcome message"""
    return {
        "message": "VDO Content API v2.2.0",
        "docs": "/docs",
        "redoc": "/redoc"
    }


# ============ Projects Router ============

@app.get("/api/projects", tags=["Projects"])
async def list_projects():
    """List all projects"""
    if not DATABASE_AVAILABLE:
        raise HTTPException(status_code=503, detail="Database not available")
    
    try:
        projects = db_list_projects()
        return {"success": True, "data": projects}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/projects/{project_id}", tags=["Projects"])
async def get_project(project_id: str):
    """Get a specific project by ID"""
    if not DATABASE_AVAILABLE:
        raise HTTPException(status_code=503, detail="Database not available")
    
    try:
        project_data = db_load_project(project_id)
        if not project_data:
            raise HTTPException(status_code=404, detail="Project not found")
        return {"success": True, "data": project_data}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/projects", tags=["Projects"])
async def create_project(project: ProjectCreate):
    """Create a new project"""
    if not DATABASE_AVAILABLE:
        raise HTTPException(status_code=503, detail="Database not available")
    
    try:
        # Filter out None values: ProjectCreate has Optional[str] fields,
        # but Project model has str="" defaults. Passing None causes ValidationError.
        create_data = {k: v for k, v in project.model_dump().items() if v is not None}
        new_project = Project(**create_data)
        project_data = new_project.model_dump(mode="json")
        project_id = db_save_project(project_data)
        return {"success": True, "data": {"project_id": project_id}}
    except Exception as e:
        import traceback
        logger.error(f"Create project failed: {e}\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))


@app.patch("/api/projects/{project_id}", tags=["Projects"])
async def update_project(project_id: str, updates: ProjectUpdate):
    """Update an existing project"""
    if not DATABASE_AVAILABLE:
        raise HTTPException(status_code=503, detail="Database not available")
    
    try:
        project_data = db_load_project(project_id)
        if not project_data:
            raise HTTPException(status_code=404, detail="Project not found")
        
        # Apply updates
        project = Project(**project_data)
        update_dict = updates.model_dump(exclude_unset=True)
        for key, value in update_dict.items():
            if hasattr(project, key):
                setattr(project, key, value)
        project.updated_at = datetime.now()
        
        # Save back
        project_data = project.model_dump(mode="json")
        db_save_project(project_data)
        return {"success": True, "data": {"project_id": project_id}}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/projects/{project_id}", tags=["Projects"])
async def delete_project(project_id: str):
    """Delete a project"""
    if not DATABASE_AVAILABLE:
        raise HTTPException(status_code=503, detail="Database not available")
    
    try:
        success = db_delete_project(project_id)
        if not success:
            raise HTTPException(status_code=404, detail="Project not found")
        return {"success": True, "message": "Project deleted"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============ Export Router ============

@app.get("/api/export/{project_id}/zip", tags=["Export"])
async def export_project_zip(project_id: str):
    """Export project as ZIP package"""
    if not DATABASE_AVAILABLE:
        raise HTTPException(status_code=503, detail="Database not available")
    
    try:
        project_data = db_load_project(project_id)
        if not project_data:
            raise HTTPException(status_code=404, detail="Project not found")
        
        project = Project(**project_data)
        exporter = ProjectExporter()
        zip_bytes = exporter.export_full_package(project)
        
        # Create safe filename
        safe_title = "".join(c for c in project.title if c.isalnum() or c in (' ', '-', '_')).strip().replace(' ', '_')
        filename = f"{safe_title}_VDO_Content.zip"
        
        return StreamingResponse(
            io.BytesIO(zip_bytes),
            media_type="application/zip",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/export/{project_id}/prompts", tags=["Export"])
async def export_prompts_text(project_id: str):
    """Export all prompts as text file"""
    if not DATABASE_AVAILABLE:
        raise HTTPException(status_code=503, detail="Database not available")
    
    try:
        project_data = db_load_project(project_id)
        if not project_data:
            raise HTTPException(status_code=404, detail="Project not found")
        
        project = Project(**project_data)
        exporter = ProjectExporter()
        prompts_text = exporter.export_all_prompts_text(project)
        
        return StreamingResponse(
            io.BytesIO(prompts_text.encode('utf-8')),
            media_type="text/plain",
            headers={"Content-Disposition": f"attachment; filename={project.title}_prompts.txt"}
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============ Generation Router ============

@app.post("/api/generate/prompts", tags=["Generation"])
async def generate_prompts(request: GeneratePromptsRequest):
    """Generate Veo 3 prompts for all scenes in a project"""
    if not DATABASE_AVAILABLE:
        raise HTTPException(status_code=503, detail="Database not available")
    
    try:
        project_data = db_load_project(request.project_id)
        if not project_data:
            raise HTTPException(status_code=404, detail="Project not found")
        
        project = Project(**project_data)
        
        if not project.scenes:
            raise HTTPException(status_code=400, detail="Project has no scenes")
        
        # Import generator
        from src.core.prompt_generator import VeoPromptGenerator
        generator = VeoPromptGenerator()
        
        # Generate prompts for each scene
        results = []
        for scene in project.scenes:
            if not scene.veo_prompt:
                scene.veo_prompt = generator.generate_prompt(
                    scene=scene,
                    character_override=request.character_reference,
                )
                results.append({
                    "scene_id": scene.scene_id,
                    "order": scene.order,
                    "prompt": scene.veo_prompt,
                    "generated": True
                })
            else:
                results.append({
                    "scene_id": scene.scene_id,
                    "order": scene.order,
                    "prompt": scene.veo_prompt,
                    "generated": False
                })
        
        # Save updated project
        project.updated_at = datetime.now()
        project_data = project.model_dump(mode="json")
        db_save_project(project_data)
        
        return {
            "success": True,
            "data": {
                "project_id": request.project_id,
                "scenes_processed": len(results),
                "results": results
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Initialize database on startup
@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    if DATABASE_AVAILABLE:
        init_db()
        logger.info("Database initialized")
    else:
        logger.warning("Database not available")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
