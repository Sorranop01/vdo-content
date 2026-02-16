"""
Unit Tests for Core Models
"""

import pytest
from datetime import datetime
from core.models import Project, Scene, StoryProposal, AudioSegment, StylePreset


class TestScene:
    """Test suite for Scene model"""
    
    def test_scene_creation(self):
        """Test basic scene creation"""
        scene = Scene(
            order=1,
            narration_text="Test narration text",
            start_time=0.0,
            end_time=5.0
        )
        assert scene.order == 1
        assert scene.narration_text == "Test narration text"
        assert scene.start_time == 0.0
        assert scene.end_time == 5.0
    
    def test_scene_audio_duration_property(self, sample_scene):
        """Test audio_duration property calculation"""
        duration = sample_scene.audio_duration
        expected = sample_scene.end_time - sample_scene.start_time
        assert duration == pytest.approx(expected, rel=0.01)
    
    def test_scene_time_range_property(self, sample_scene):
        """Test time_range property formatting"""
        time_range = sample_scene.time_range
        assert isinstance(time_range, str)
        assert " - " in time_range
        assert ":" in time_range
    
    def test_scene_word_count_auto_calculation(self):
        """Test that word count is auto-calculated"""
        scene = Scene(
            order=1,
            narration_text="one two three four five",
            start_time=0,
            end_time=5
        )
        assert scene.word_count == 5
    
    def test_scene_default_values(self):
        """Test default values are set correctly"""
        scene = Scene(order=1, narration_text="Test", start_time=0, end_time=1)
        assert scene.visual_style == "documentary"
        assert scene.emotion == "neutral"
        assert scene.transition == "cut"
        assert scene.prompt_copied is False
        assert scene.video_generated is False


class TestProject:
    """Test suite for Project model"""
    
    def test_project_creation(self, sample_project):
        """Test project creation with scenes"""
        assert sample_project.title == "Test Project"
        assert len(sample_project.scenes) == 3
    
    def test_project_scene_count_property(self, sample_project):
        """Test scene_count property"""
        assert sample_project.scene_count == 3
    
    def test_project_total_duration_property(self, sample_project):
        """Test total_duration property"""
        total = sample_project.total_duration
        assert total > 0
    
    def test_project_completed_scenes_property(self, sample_project):
        """Test completed_scenes property"""
        # Initially none are completed
        assert sample_project.completed_scenes == 0
        
        # Mark one as complete
        sample_project.scenes[0].video_generated = True
        assert sample_project.completed_scenes == 1
    
    def test_project_default_status(self):
        """Test default project status"""
        project = Project(title="Test", topic="Test topic")
        assert project.status == "draft"
    
    def test_project_empty_scenes(self, sample_project_no_scenes):
        """Test project with no scenes"""
        assert sample_project_no_scenes.scene_count == 0
        assert sample_project_no_scenes.total_duration == 0


class TestStoryProposal:
    """Test suite for StoryProposal model"""
    
    def test_proposal_creation(self, sample_proposal):
        """Test proposal creation"""
        assert sample_proposal.topic == "วิธีทำอาหารไทยง่ายๆ"
        assert sample_proposal.status == "pending"
    
    def test_proposal_default_version(self):
        """Test default version is 1"""
        proposal = StoryProposal(topic="Test topic")
        assert proposal.version == 1
    
    def test_proposal_status_values(self):
        """Test valid status values"""
        pending = StoryProposal(topic="Test", status="pending")
        approved = StoryProposal(topic="Test", status="approved")
        rejected = StoryProposal(topic="Test", status="rejected")
        
        assert pending.status == "pending"
        assert approved.status == "approved"
        assert rejected.status == "rejected"


class TestAudioSegment:
    """Test suite for AudioSegment model"""
    
    def test_audio_segment_creation(self, sample_audio_segment):
        """Test audio segment creation"""
        assert sample_audio_segment.order == 1
        assert sample_audio_segment.duration == 5.5
    
    def test_audio_segment_time_range_property(self, sample_audio_segment):
        """Test time_range property"""
        time_range = sample_audio_segment.time_range
        assert isinstance(time_range, str)
        assert " - " in time_range


class TestStylePreset:
    """Test suite for StylePreset model"""
    
    def test_style_preset_creation(self):
        """Test style preset creation"""
        preset = StylePreset(
            name="Test Style",
            description="A test style",
            lighting="natural",
            color_grade="warm"
        )
        assert preset.name == "Test Style"
        assert preset.lighting == "natural"
    
    def test_style_preset_defaults(self):
        """Test style preset default values"""
        preset = StylePreset(
            name="Test",
            description="Test",
            lighting="natural",
            color_grade="neutral"
        )
        assert preset.voice_speed == 1.0
        assert preset.voice_style == "neutral"
        assert "high quality" in preset.quality_tags
