"""
Analytics Module -- Project statistics and pipeline quality metrics.
"""

import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Optional

logger = logging.getLogger("vdo_content.analytics")

PROJECTS_DIR = Path("data/projects")


def _load_all_projects() -> list:
    """Load all project JSON files from data/projects/."""
    projects = []
    if not PROJECTS_DIR.exists():
        return projects

    for path in sorted(PROJECTS_DIR.glob("*.json")):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            projects.append(data)
        except Exception as e:
            logger.warning(f"Failed to load project {path}: {e}")

    return projects


def get_project_stats() -> dict:
    """
    High-level project statistics across all saved projects.

    Returns dict with:
        total_projects, total_scenes, total_prompts_generated,
        avg_quality_score, projects_completed, platforms_used
    """
    projects = _load_all_projects()
    if not projects:
        return {
            "total_projects": 0,
            "total_scenes": 0,
            "total_prompts_generated": 0,
            "avg_quality_score": 0.0,
            "projects_completed": 0,
            "platforms_used": [],
        }

    total_scenes = 0
    all_scores = []
    platforms_used = set()
    projects_with_prompts = 0

    for p in projects:
        scenes = p.get("scenes", [])
        total_scenes += len(scenes)

        has_prompts = False
        for s in scenes:
            score = s.get("quality_score", 0)
            if score > 0:
                all_scores.append(score)
                has_prompts = True
        if has_prompts:
            projects_with_prompts += 1

        for platform in p.get("platforms", []):
            platforms_used.add(platform)

    return {
        "total_projects": len(projects),
        "total_scenes": total_scenes,
        "total_prompts_generated": len(all_scores),
        "avg_quality_score": round(sum(all_scores) / len(all_scores), 1) if all_scores else 0.0,
        "projects_completed": projects_with_prompts,
        "platforms_used": sorted(list(platforms_used)),
    }


def get_quality_distribution() -> dict:
    """
    Quality score distribution across all generated prompts.

    Returns dict with:
        excellent (>=90), good (80-89), fair (70-79), poor (<70), scores list
    """
    projects = _load_all_projects()
    scores = []

    for p in projects:
        for s in p.get("scenes", []):
            score = s.get("quality_score", 0)
            if score > 0:
                scores.append(score)

    if not scores:
        return {"excellent": 0, "good": 0, "fair": 0, "poor": 0, "scores": []}

    return {
        "excellent": sum(1 for s in scores if s >= 90),
        "good": sum(1 for s in scores if 80 <= s < 90),
        "fair": sum(1 for s in scores if 70 <= s < 80),
        "poor": sum(1 for s in scores if s < 70),
        "scores": scores,
        "avg": round(sum(scores) / len(scores), 1),
        "min": round(min(scores), 1),
        "max": round(max(scores), 1),
    }


def get_recent_projects(limit: int = 10) -> list:
    """Return the most recently created projects as lightweight summaries."""
    projects = _load_all_projects()

    summaries = []
    for p in projects:
        scenes = p.get("scenes", [])
        scores = [s.get("quality_score", 0) for s in scenes if s.get("quality_score", 0) > 0]
        has_prompts = any(s.get("veo_prompt") for s in scenes)

        summaries.append({
            "project_id": p.get("project_id", ""),
            "title": p.get("title", "Untitled"),
            "topic": p.get("topic", ""),
            "scene_count": len(scenes),
            "prompt_count": sum(1 for s in scenes if s.get("veo_prompt")),
            "avg_score": round(sum(scores) / len(scores), 1) if scores else 0.0,
            "status": p.get("status", "unknown"),
            "created_at": p.get("project_date", ""),
            "platforms": p.get("platforms", []),
        })

    # Sort by creation date (most recent first)
    summaries.sort(key=lambda x: x.get("created_at", ""), reverse=True)
    return summaries[:limit]


def get_video_type_breakdown() -> dict:
    """Count projects by video_type."""
    projects = _load_all_projects()
    breakdown = {}
    for p in projects:
        vtype = p.get("video_type", "unknown")
        breakdown[vtype] = breakdown.get(vtype, 0) + 1
    return breakdown


def get_platform_breakdown() -> dict:
    """Count occurrences of each platform across all projects."""
    projects = _load_all_projects()
    breakdown = {}
    for p in projects:
        for platform in p.get("platforms", []):
            breakdown[platform] = breakdown.get(platform, 0) + 1
    return breakdown
