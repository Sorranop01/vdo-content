"""
Database Module - Facade (Firestore Version)
============================================
Thin re-export layer for backward compatibility.
Integrates the new Firestore implementation.

Modules:
  - firestore_client.py -> Client & initialization
  - db_crud.py          -> Project / Draft CRUD
  - db_reference.py     -> Tags, profiles, categories CRUD
"""

import logging
from .firestore_client import get_db

# ── Firestore Client & Infrastructure ──────────────────────────
# NO models needed for Firestore (schemaless), but we keep structure

# ── Project & Draft CRUD ──────────────────────────────────────
from .db_crud import (
    project_to_dict,
    db_save_project,
    db_load_project,
    db_list_projects,
    db_delete_project,
    db_update_project_metadata,
    db_save_draft,
    db_load_draft,
    db_delete_draft,
    db_list_drafts,
    log_api_usage,
    save_media_asset,
    get_project_assets,
    # Aliases
    db_get_all_projects,
    db_get_project,
)

# ── Reference Data CRUD ──────────────────────────────────────
from .db_reference import (
    get_visual_tags,
    add_visual_tag,
    delete_visual_tag,
    update_visual_tag,
    get_all_tags_raw,
    delete_tag,
    save_style_profile,
    list_style_profiles,
    delete_style_profile,
    get_video_profiles,
    list_video_profiles,
    get_video_profile,
    update_video_profile,
    get_content_categories,
    get_target_audiences,
    get_content_goals,
    # Aliases
    add_tag,
    get_all_style_presets,
    save_style_preset,
    delete_style_preset,
)

logger = logging.getLogger("vdo_content.database")


# ── init_db (No-op or Seed) ────────────────────────────────────
def init_db():
    """
    Initialize Firestore collections (seeding if empty).
    In SQL this created tables. In Firestore we just ensure seeds exist.
    """
    from .db_seed import seed_all
    try:
        seed_all()
        logger.info("Verification: Database seeded successfully")
    except Exception as e:
        logger.warning(f"Seeding skipped or failed (might be normal if credentials missing locally): {e}")

# ── Module-level flag ──────────────────────────────────────────
DATABASE_AVAILABLE = True

if __name__ == "__main__":
    init_db()