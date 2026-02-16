"""
Database Module - Facade
========================
Thin re-export layer for backward compatibility.
All logic lives in the split modules:
  - db_engine.py    → Engine, session, Base, PortableUUID
  - db_models.py    → SQLAlchemy ORM models
  - db_seed.py      → Migrations and seed data
  - db_crud.py      → Project / Draft CRUD
  - db_reference.py → Tags, profiles, categories CRUD
"""

import logging

# ── Engine & Infrastructure ────────────────────────────────────
from .db_engine import (  # noqa: F401
    engine,
    SessionLocal,
    Base,
    PortableUUID,
    get_db,
    DATABASE_URL,
)

# ── ORM Models ─────────────────────────────────────────────────
from .db_models import (  # noqa: F401
    ProjectDB,
    SceneDB,
    AudioSegmentDB,
    DraftDB,
    VisualTagDB,
    StyleProfileDB,
    VideoProfileDB,
    MediaAssetDB,
    UsageLogDB,
    ContentCategoryDB,
    TargetAudienceDB,
    ContentGoalDB,
)

# ── Seed / Migrations ─────────────────────────────────────────
from .db_seed import (  # noqa: F401
    migrate_add_video_profile_id,
    migrate_add_direction_style,
    migrate_add_prompt_style_config,
    migrate_add_category_audience,
    migrate_add_content_goal_id,
    migrate_add_generated_content,
    init_style_profiles,
    init_visual_tags,
    init_video_profiles,
    init_content_categories,
    init_content_goals,
    init_target_audiences,
)

# ── Project & Draft CRUD ──────────────────────────────────────
from .db_crud import (  # noqa: F401
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
from .db_reference import (  # noqa: F401
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


# ── init_db (orchestrates migrations + seeding) ────────────────
def init_db():
    """Create all tables, run migrations, seed initial data"""
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables created")

    # Run migrations for new columns
    migrate_add_video_profile_id()
    migrate_add_direction_style()
    migrate_add_prompt_style_config()
    migrate_add_category_audience()
    migrate_add_content_goal_id()
    migrate_add_generated_content()

    # Seed initial data
    with get_db() as db:
        if db.query(VisualTagDB).count() == 0:
            init_visual_tags(db)

        if db.query(VideoProfileDB).count() == 0:
            init_video_profiles(db)

        if db.query(StyleProfileDB).count() == 0:
            init_style_profiles(db)

        if db.query(ContentCategoryDB).count() == 0:
            init_content_categories(db)

        if db.query(TargetAudienceDB).count() == 0:
            init_target_audiences(db)

        if db.query(ContentGoalDB).count() == 0:
            init_content_goals(db)


# ── Module-level flag ──────────────────────────────────────────
DATABASE_AVAILABLE = True

if __name__ == "__main__":
    init_db()