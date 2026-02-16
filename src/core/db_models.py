"""
Database Models
All SQLAlchemy ORM model classes for VDO Content.
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, String, Text, Integer, Float, Boolean, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship

from .db_engine import Base, PortableUUID


# ============ Core Models ============

class ProjectDB(Base):
    """Project table"""
    __tablename__ = "projects"
    
    id = Column(PortableUUID(), primary_key=True, default=uuid.uuid4)
    title = Column(String(255), nullable=False)
    topic = Column(Text)
    status = Column(String(50), default="draft")
    default_style = Column(String(50))
    video_profile_id = Column(String(50))  # Master video profile ID (e.g., "vlog-lifestyle")
    target_duration = Column(Integer, default=60)
    character_reference = Column(Text)
    full_script = Column(Text)
    style_instructions = Column(Text)
    script_text = Column(Text)
    audio_path = Column(String(255))
    audio_duration = Column(Float, default=0.0)
    drive_folder_link = Column(String(500))
    aspect_ratio = Column(String(20), default="16:9")
    
    # Step 2: Content Planning fields
    content_goal = Column(String(255))           # เป้าหมายเนื้อหา (display text)
    content_category = Column(String(100))       # หมวดหมู่เนื้อหา
    target_audience = Column(String(255))        # กลุ่มเป้าหมาย (display text)
    content_description = Column(Text)           # รายละเอียดเนื้อหา
    platforms = Column(JSON, default=list)        # ช่องทางแพลตฟอร์ม ["youtube", "tiktok"]
    video_format = Column(String(50))            # รูปแบบวีดีโอ (shorts, standard, longform)
    
    # Step 3: Script fields
    voice_personality = Column(String(100))      # บุคลิกน้ำเสียง
    workflow_step = Column(Integer, default=0)   # Current step (0-4)
    
    # Step 1: Project metadata
    description = Column(Text)                   # รายละเอียดโปรเจค
    project_date = Column(DateTime)              # วันที่โปรเจค
    
    # Step 4: Video Prompt fields
    video_type = Column(String(50))              # ประเภทวีดีโอ (with_person, no_person, mixed)
    visual_theme = Column(String(255))           # ธีมภาพ
    directors_note = Column(Text)                # โน้ตผู้กำกับ
    direction_style = Column(String(100))        # สไตล์การกำกับ
    direction_custom_notes = Column(Text)        # โน้ตเพิ่มเติม
    
    # Step 5: Upload fields
    upload_folder = Column(String(255))          # โฟลเดอร์อัพโหลด
    uploaded_files = Column(JSON, default=list)  # รายการไฟล์ที่อัพโหลด
    final_video_path = Column(String(500))       # path ไฟล์วีดีโอสุดท้าย
    
    # AI-generated content from Step 2
    generated_content = Column(Text)
    
    # Proposal data (stored as JSON)
    proposal_data = Column(JSON)
    
    # Prompt style configuration (stores selected styles)
    prompt_style_config = Column(JSON)
    
    # Content categorization (FK references)
    content_category_id = Column(PortableUUID(), ForeignKey("content_categories.id"), nullable=True)
    target_audience_id = Column(PortableUUID(), ForeignKey("target_audiences.id"), nullable=True)
    content_goal_id = Column(PortableUUID(), ForeignKey("content_goals.id"), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    # Relationships
    scenes = relationship("SceneDB", back_populates="project", cascade="all, delete-orphan", order_by="SceneDB.order_num")
    audio_segments = relationship("AudioSegmentDB", back_populates="project", cascade="all, delete-orphan", order_by="AudioSegmentDB.order_num")


class SceneDB(Base):
    """Scene table"""
    __tablename__ = "scenes"
    
    id = Column(PortableUUID(), primary_key=True, default=uuid.uuid4)
    project_id = Column(PortableUUID(), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    order_num = Column(Integer, nullable=False)
    
    narration_text = Column(Text)
    veo_prompt = Column(Text)
    emotion = Column(String(50))
    visual_style = Column(String(50))
    subject_description = Column(Text)
    
    start_time = Column(Float, default=0.0)
    end_time = Column(Float, default=0.0)
    estimated_duration = Column(Float, default=0.0)
    
    video_generated = Column(Boolean, default=False)
    audio_synced = Column(Boolean, default=False)
    stock_video_url = Column(String(500))
    
    # Relationships
    project = relationship("ProjectDB", back_populates="scenes")


class AudioSegmentDB(Base):
    """Audio segment table"""
    __tablename__ = "audio_segments"
    
    id = Column(PortableUUID(), primary_key=True, default=uuid.uuid4)
    project_id = Column(PortableUUID(), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    order_num = Column(Integer, nullable=False)
    
    start_time = Column(Float, default=0.0)
    end_time = Column(Float, default=0.0)
    duration = Column(Float, default=0.0)
    text_content = Column(Text)
    is_edited = Column(Boolean, default=False)
    
    # Relationships
    project = relationship("ProjectDB", back_populates="audio_segments")


# ============ Support Models ============

class DraftDB(Base):
    """Draft table for auto-saving unsaved work"""
    __tablename__ = "drafts"
    
    id = Column(PortableUUID(), primary_key=True, default=uuid.uuid4)
    session_id = Column(String(100), nullable=False, index=True)
    draft_type = Column(String(50), nullable=False)
    content = Column(JSON)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))


class VisualTagDB(Base):
    """Database for Visual Builder options (Lighting, Camera, Mood, etc.)"""
    __tablename__ = "visual_tags"
    
    id = Column(PortableUUID(), primary_key=True, default=uuid.uuid4)
    category = Column(String(50), nullable=False, index=True)
    label = Column(String(100), nullable=False)
    value = Column(String(255), nullable=False)
    order_num = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)


class StyleProfileDB(Base):
    """User-saved visual style profiles"""
    __tablename__ = "style_profiles"
    
    id = Column(PortableUUID(), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), nullable=False, unique=True)
    description = Column(String(255))
    config = Column(JSON, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class VideoProfileDB(Base):
    """Master Video Profiles (System-defined, pre-configured styles for content types)"""
    __tablename__ = "video_profiles"
    
    id = Column(String(50), primary_key=True)
    name_th = Column(String(100), nullable=False)
    name_en = Column(String(100), nullable=False)
    description_th = Column(Text)
    description_en = Column(Text)
    config = Column(JSON, nullable=False)
    icon = Column(String(10))
    order_num = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    is_system = Column(Boolean, default=True)


class MediaAssetDB(Base):
    """Central repository for media files (images, audio, video)"""
    __tablename__ = "media_assets"
    
    id = Column(PortableUUID(), primary_key=True, default=uuid.uuid4)
    project_id = Column(PortableUUID(), ForeignKey("projects.id", ondelete="SET NULL"), nullable=True)
    file_path = Column(String(500), nullable=False)
    file_type = Column(String(50))
    asset_type = Column(String(50))
    file_size_bytes = Column(Integer, default=0)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class UsageLogDB(Base):
    """Log AI service usage for cost tracking and auditing"""
    __tablename__ = "usage_logs"
    
    id = Column(PortableUUID(), primary_key=True, default=uuid.uuid4)
    project_id = Column(PortableUUID(), ForeignKey("projects.id", ondelete="SET NULL"), nullable=True)
    service_name = Column(String(50), nullable=False)
    operation = Column(String(50))
    tokens_used = Column(Integer, default=0)
    duration_seconds = Column(Float, default=0.0)
    status = Column(String(20))
    metadata_json = Column(JSON)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc))


# ============ Reference Data Models ============

class ContentCategoryDB(Base):
    """Content Category table - หัวแหน่งเนื้อหา"""
    __tablename__ = "content_categories"
    
    id = Column(PortableUUID(), primary_key=True, default=uuid.uuid4)
    name_th = Column(String(100), nullable=False, unique=True)
    name_en = Column(String(100))
    description = Column(String(255))
    icon = Column(String(10))
    order_num = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class TargetAudienceDB(Base):
    """Target Audience table - กลุ่มเป้าหมาย"""
    __tablename__ = "target_audiences"
    
    id = Column(PortableUUID(), primary_key=True, default=uuid.uuid4)
    name_th = Column(String(100), nullable=False, unique=True)
    name_en = Column(String(100))
    age_range = Column(String(50))
    description = Column(String(255))
    order_num = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class ContentGoalDB(Base):
    """Content Goal table - เป้าหมายเนื้อหา"""
    __tablename__ = "content_goals"
    
    id = Column(PortableUUID(), primary_key=True, default=uuid.uuid4)
    name_th = Column(String(100), nullable=False, unique=True)
    name_en = Column(String(100))
    description = Column(String(255))
    icon = Column(String(10))
    prompt_hint = Column(String(500))
    order_num = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
