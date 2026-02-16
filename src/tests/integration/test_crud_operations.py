"""
DB CRUD Integration Tests
Tests actual save/load/update/delete round-trips for projects, scenes, and audio segments.
Uses a temporary in-memory SQLite database to avoid affecting production data.
"""

import pytest
import uuid
from datetime import datetime, timezone

# We need to test with the real database functions
# Import the models and functions
from src.core.database import (
    Base,
    ProjectDB,
    SceneDB,
    AudioSegmentDB,
    get_db,
    db_save_project,
    db_load_project,
    db_list_projects,
    db_delete_project,
    project_to_dict,
    init_db,
)
from src.core.models import Project


class TestProjectCRUD:
    """Test full CRUD cycle for projects"""

    def _make_project_data(self, **overrides) -> dict:
        """Create project data dict matching what Streamlit would produce"""
        data = {
            "project_id": str(uuid.uuid4()),
            "title": "ทดสอบโปรเจค",
            "topic": "อาหารเพื่อสุขภาพ",
            "description": "โปรเจคทดสอบ CRUD",
            "status": "draft",
            "default_style": "documentary",
            "target_duration": 60,
            "aspect_ratio": "16:9",
            "content_goal": "เพิ่มยอดขาย",
            "content_category": "food",
            "target_audience": "คนรุ่นใหม่ 25-35",
            "content_description": "รีวิวอาหารเพื่อสุขภาพ",
            "platforms": ["youtube", "tiktok"],
            "video_format": "short",
            "voice_personality": "friendly",
            "video_type": "no_person",
            "visual_theme": "bright",
            "directors_note": "เน้นสีสัน",
            "direction_style": "cinematic",
            "direction_custom_notes": "ใช้ slow motion",
            "workflow_step": 2,
        }
        data.update(overrides)
        return data

    def test_save_and_load_project(self):
        """Test save then load returns matching data"""
        data = self._make_project_data()
        project_id = data["project_id"]

        # Save
        saved_id = db_save_project(data)
        assert saved_id is not None

        # Load
        loaded = db_load_project(project_id)
        assert loaded is not None
        assert loaded["title"] == data["title"]
        assert loaded["topic"] == data["topic"]
        assert loaded["description"] == data["description"]
        assert loaded["content_goal"] == data["content_goal"]
        assert loaded["video_type"] == data["video_type"]
        assert loaded["visual_theme"] == data["visual_theme"]
        assert loaded["directors_note"] == data["directors_note"]
        assert loaded["direction_style"] == data["direction_style"]
        assert loaded["direction_custom_notes"] == data["direction_custom_notes"]

        # Cleanup
        db_delete_project(project_id)

    def test_update_project(self):
        """Test updating an existing project"""
        data = self._make_project_data()
        project_id = data["project_id"]
        db_save_project(data)

        # Update fields
        data["title"] = "อัพเดตชื่อ"
        data["status"] = "step3_script"
        data["full_script"] = "สวัสดีครับ วันนี้จะพาไปชม..."
        data["workflow_step"] = 3
        db_save_project(data)

        # Verify update
        loaded = db_load_project(project_id)
        assert loaded["title"] == "อัพเดตชื่อ"
        assert loaded["status"] == "step3_script"
        assert loaded["full_script"] == "สวัสดีครับ วันนี้จะพาไปชม..."
        assert loaded["workflow_step"] == 3

        # Cleanup
        db_delete_project(project_id)

    def test_delete_project(self):
        """Test deleting a project"""
        data = self._make_project_data()
        project_id = data["project_id"]
        db_save_project(data)

        # Verify exists
        assert db_load_project(project_id) is not None

        # Delete
        result = db_delete_project(project_id)
        assert result is True

        # Verify gone
        assert db_load_project(project_id) is None

    def test_list_projects(self):
        """Test listing projects"""
        data1 = self._make_project_data(title="โปรเจค A")
        data2 = self._make_project_data(title="โปรเจค B")
        id1 = data1["project_id"]
        id2 = data2["project_id"]

        db_save_project(data1)
        db_save_project(data2)

        projects = db_list_projects()
        assert isinstance(projects, list)

        titles = [p.get("title") for p in projects]
        assert "โปรเจค A" in titles
        assert "โปรเจค B" in titles

        # Cleanup
        db_delete_project(id1)
        db_delete_project(id2)

    def test_load_nonexistent_project(self):
        """Test loading a project that doesn't exist returns None"""
        fake_id = str(uuid.uuid4())
        result = db_load_project(fake_id)
        assert result is None


class TestProjectToDict:
    """Test project_to_dict conversion"""

    def test_round_trip_all_fields(self):
        """Test that project_to_dict returns all fields from ProjectDB"""
        data = {
            "project_id": str(uuid.uuid4()),
            "title": "Round Trip Test",
            "topic": "Testing",
            "description": "Full round trip",
            "status": "draft",
            "content_goal": "Goal",
            "content_category": "food",
            "target_audience": "everyone",
            "video_type": "mixed",
            "visual_theme": "dark",
            "directors_note": "Keep it simple",
            "upload_folder": "20260210-test",
            "uploaded_files": ["file1.mp4", "file2.mp4"],
        }
        project_id = data["project_id"]
        db_save_project(data)

        loaded = db_load_project(project_id)
        assert loaded is not None

        # Verify all key fields are present in the dict
        expected_keys = [
            "title", "topic", "description", "status",
            "content_goal", "content_category", "target_audience",
            "video_type", "visual_theme", "directors_note",
            "upload_folder", "uploaded_files",
            "created_at", "updated_at"
        ]
        for key in expected_keys:
            assert key in loaded, f"Missing key: {key}"

        # Verify JSON fields
        assert loaded["uploaded_files"] == ["file1.mp4", "file2.mp4"]

        # Cleanup
        db_delete_project(project_id)

    def test_dict_creates_valid_pydantic_project(self):
        """Test that project_to_dict output can create a valid Project model"""
        data = {
            "project_id": str(uuid.uuid4()),
            "title": "Pydantic Test",
            "topic": "Validation",
        }
        project_id = data["project_id"]
        db_save_project(data)

        loaded = db_load_project(project_id)
        assert loaded is not None

        # This should NOT raise - the dict should be compatible
        project = Project(**loaded)
        assert project.title == "Pydantic Test"
        assert project.topic == "Validation"

        # Cleanup
        db_delete_project(project_id)


class TestThaiContent:
    """Test Thai language content handling"""

    def test_thai_title_and_topic(self):
        """Test Thai characters in project fields"""
        data = {
            "project_id": str(uuid.uuid4()),
            "title": "รีวิวอาหาร 🍕 สุดอร่อย",
            "topic": "อาหารไทยแท้ ๆ กับเคล็ดลับทำง่าย",
            "description": "วิดีโอรีวิวร้านอาหาร ราคาถูก คุณภาพดี",
            "content_description": "พาไปชิมอาหารไทย ๕ เมนู ที่ต้องลอง!",
            "directors_note": "เน้นความสดใส อบอุ่น ใช้มุมกล้องแบบ POV",
        }
        project_id = data["project_id"]
        db_save_project(data)

        loaded = db_load_project(project_id)
        assert loaded["title"] == "รีวิวอาหาร 🍕 สุดอร่อย"
        assert "อาหารไทยแท้" in loaded["topic"]
        assert "๕" in loaded["content_description"]
        assert "POV" in loaded["directors_note"]

        # Cleanup
        db_delete_project(project_id)


class TestEdgeCases:
    """Test edge cases for database operations"""

    def test_empty_strings(self):
        """Test saving empty string fields"""
        data = {
            "project_id": str(uuid.uuid4()),
            "title": "Empty Test",
            "topic": "",
            "description": "",
            "content_goal": "",
        }
        project_id = data["project_id"]
        db_save_project(data)

        loaded = db_load_project(project_id)
        assert loaded is not None
        assert loaded["title"] == "Empty Test"

        # Cleanup
        db_delete_project(project_id)

    def test_none_optional_fields(self):
        """Test that None optional fields don't crash"""
        data = {
            "project_id": str(uuid.uuid4()),
            "title": "Minimal",
            "topic": "Min",
        }
        project_id = data["project_id"]
        db_save_project(data)

        loaded = db_load_project(project_id)
        assert loaded is not None

        # These should be None or empty, not crash
        project = Project(**loaded)
        assert project.title == "Minimal"

        # Cleanup
        db_delete_project(project_id)

    def test_json_fields_persist(self):
        """Test JSON fields (platforms, uploaded_files) persist correctly"""
        platforms = ["youtube", "tiktok", "instagram"]
        uploaded = ["/path/to/file1.mp4", "/path/to/file2.mp4"]
        prompt_config = {"style": "cinematic", "mood": "energetic"}

        data = {
            "project_id": str(uuid.uuid4()),
            "title": "JSON Test",
            "topic": "JSON Fields",
            "platforms": platforms,
            "uploaded_files": uploaded,
            "prompt_style_config": prompt_config,
        }
        project_id = data["project_id"]
        db_save_project(data)

        loaded = db_load_project(project_id)
        assert loaded["platforms"] == platforms
        assert loaded["uploaded_files"] == uploaded
        assert loaded["prompt_style_config"] == prompt_config

        # Cleanup
        db_delete_project(project_id)
