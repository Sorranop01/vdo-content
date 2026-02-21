"""
Strategy Engine — Blueprints Router

CRUD endpoints for managing generated Content Blueprints.
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.models.schemas import ContentBlueprintPayload

router = APIRouter()


# ============================================================
# In-Memory Store (will be replaced with PostgreSQL in Phase 2)
# ============================================================

_blueprints: dict[str, ContentBlueprintPayload] = {}


# ============================================================
# Endpoints
# ============================================================


@router.get("/")
async def list_blueprints():
    """List all stored blueprints (most recent first)."""
    sorted_bps = sorted(
        _blueprints.values(),
        key=lambda b: b.created_at,
        reverse=True,
    )
    return [
        {
            "blueprint_id": bp.blueprint_id,
            "cluster_primary_keyword": bp.cluster_primary_keyword,
            "hub_title": bp.hub.title,
            "spokes_count": len(bp.spokes),
            "approved_by": bp.approved_by,
            "created_at": bp.created_at,
        }
        for bp in sorted_bps
    ]


@router.get("/{blueprint_id}")
async def get_blueprint(blueprint_id: str):
    """Get a specific blueprint by ID."""
    bp = _blueprints.get(blueprint_id)
    if not bp:
        raise HTTPException(status_code=404, detail=f"Blueprint '{blueprint_id}' not found")
    return bp


@router.put("/{blueprint_id}")
async def update_blueprint(blueprint_id: str, payload: ContentBlueprintPayload):
    """
    Update (replace) a blueprint.

    Used by the HITL dashboard when the operator edits the blueprint.
    """
    if blueprint_id not in _blueprints:
        raise HTTPException(status_code=404, detail=f"Blueprint '{blueprint_id}' not found")

    payload.blueprint_id = blueprint_id
    _blueprints[blueprint_id] = payload
    return {"message": "Blueprint updated", "blueprint_id": blueprint_id}


@router.delete("/{blueprint_id}")
async def delete_blueprint(blueprint_id: str):
    """Delete a blueprint."""
    if blueprint_id not in _blueprints:
        raise HTTPException(status_code=404, detail=f"Blueprint '{blueprint_id}' not found")
    del _blueprints[blueprint_id]
    return {"message": "Blueprint deleted", "blueprint_id": blueprint_id}
