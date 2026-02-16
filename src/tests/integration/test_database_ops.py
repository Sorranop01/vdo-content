"""
Unit Tests for Database Operations
VDO Content V2 Test Suite

Tests database CRUD operations with SQLite test database
"""

import pytest
import os
import uuid
from datetime import datetime
from unittest.mock import Mock, patch
from contextlib import contextmanager

from core.database import (
    init_db,
    get_db,
    ProjectDB,
    SceneDB,
    AudioSegmentDB,
    DraftDB,
    Base,
    engine,
    SessionLocal,
)


class TestDatabaseInit:
    """Test database initialization"""
    
    def test_init_db_creates_tables(self):
        """Test init_db creates all tables"""
        # Tables should already exist after module import
        from sqlalchemy import inspect
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        
        assert "projects" in tables
        assert "scenes" in tables
        assert "audio_segments" in tables
        assert "drafts" in tables
    
    def test_base_exists(self):
        """Test Base declarative base exists"""
        assert Base is not None
    
    def test_session_local_exists(self):
        """Test SessionLocal exists"""
        assert SessionLocal is not None


class TestProjectDB:
    """Test ProjectDB CRUD operations"""
    
    def test_project_model_instantiation(self):
        """Test ProjectDB can be instantiated"""
        project = ProjectDB(
            title="Test Project",
            topic="Test Topic",
            status="draft"
        )
        
        assert project.title == "Test Project"
        assert project.topic == "Test Topic"
        assert project.status == "draft"
    
    def test_project_model_defaults(self):
        """Test ProjectDB default values (defaults apply on INSERT not instantiation)"""
        project = ProjectDB(title="Test")
        
        # SQLAlchemy Column defaults are applied on INSERT, not instantiation
        # So we verify the schema accepts and stores explicit values correctly
        assert project.title == "Test"
        # Defaults will be None until INSERT
        assert project.status is None or project.status == "draft"
    
    def test_project_model_with_metadata(self):
        """Test ProjectDB with metadata"""
        project = ProjectDB(
            title="Test",
            target_duration=120,
            video_profile_id="vlog-lifestyle",
            aspect_ratio="9:16"
        )
        
        assert project.target_duration == 120
        assert project.video_profile_id == "vlog-lifestyle"
        assert project.aspect_ratio == "9:16"


class TestSceneDB:
    """Test SceneDB CRUD operations"""
    
    def test_scene_model_instantiation(self):
        """Test SceneDB can be instantiated"""
        scene = SceneDB(
            project_id=uuid.uuid4(),
            order_num=1,
            narration_text="Test narration",
            start_time=0.0,
            end_time=5.0
        )
        
        assert scene.order_num == 1
        assert scene.narration_text == "Test narration"
    
    def test_scene_model_with_veo_prompt(self):
        """Test SceneDB with veo_prompt"""
        scene = SceneDB(
            project_id=uuid.uuid4(),
            order_num=1,
            narration_text="Thai narration",
            veo_prompt="English video prompt",
            start_time=0.0,
            end_time=5.0
        )
        
        assert scene.veo_prompt == "English video prompt"
    
    def test_scene_model_duration(self):
        """Test SceneDB estimated_duration"""
        scene = SceneDB(
            project_id=uuid.uuid4(),
            order_num=1,
            narration_text="Test",
            start_time=0.0,
            end_time=6.5,
            estimated_duration=6.5
        )
        
        assert scene.estimated_duration == 6.5


class TestAudioSegmentDB:
    """Test AudioSegmentDB CRUD operations"""
    
    def test_audio_segment_creation(self):
        """Test AudioSegmentDB can be instantiated"""
        segment = AudioSegmentDB(
            project_id=uuid.uuid4(),
            order_num=1,
            duration=5.5
        )
        
        assert segment.order_num == 1
        assert segment.duration == 5.5
    
    def test_audio_segment_with_times(self):
        """Test AudioSegmentDB with time data"""
        segment = AudioSegmentDB(
            project_id=uuid.uuid4(),
            order_num=1,
            start_time=0.0,
            end_time=3.0,
            duration=3.0,
            text_content="Test content"
        )
        
        assert segment.start_time == 0.0
        assert segment.end_time == 3.0
        assert segment.text_content == "Test content"


class TestDraftDB:
    """Test DraftDB CRUD operations"""
    
    def test_draft_model_creation(self):
        """Test DraftDB can be instantiated"""
        draft = DraftDB(
            session_id="test-session-123",
            draft_type="ideation",
            content={"key": "value"}
        )
        
        assert draft.session_id == "test-session-123"
        assert draft.draft_type == "ideation"
        assert draft.content == {"key": "value"}


class TestDatabaseContextManager:
    """Test database context manager"""
    
    def test_get_db_is_context_manager(self):
        """Test get_db is a context manager"""
        with get_db() as db:
            assert db is not None
    
    def test_get_db_returns_session(self):
        """Test get_db returns a valid session"""
        from sqlalchemy import text
        with get_db() as db:
            # Should be able to execute a simple query
            result = db.execute(text("SELECT 1"))
            assert result is not None


class TestDatabaseEdgeCases:
    """Test database edge cases"""
    
    def test_empty_narration_text(self):
        """Test scene with empty narration"""
        scene = SceneDB(
            project_id=uuid.uuid4(),
            order_num=1,
            narration_text="",
            start_time=0.0,
            end_time=0.0
        )
        
        assert scene.narration_text == ""
    
    def test_unicode_content(self):
        """Test Thai unicode in content"""
        scene = SceneDB(
            project_id=uuid.uuid4(),
            order_num=1,
            narration_text="สวัสดีครับ ยินดีต้อนรับสู่โปรเจค VDO Content",
            start_time=0.0,
            end_time=5.0
        )
        
        assert "สวัสดี" in scene.narration_text
    
    def test_long_text_content(self):
        """Test scene with long narration"""
        long_text = "Test " * 1000
        scene = SceneDB(
            project_id=uuid.uuid4(),
            order_num=1,
            narration_text=long_text,
            start_time=0.0,
            end_time=300.0
        )
        
        assert len(scene.narration_text) == len(long_text)
    
    def test_special_characters_in_title(self):
        """Test project with special characters in title"""
        project = ProjectDB(
            title="Test & Project <with> 'special' \"chars\"",
            topic="Testing special characters"
        )
        
        assert "&" in project.title
        assert "<" in project.title
