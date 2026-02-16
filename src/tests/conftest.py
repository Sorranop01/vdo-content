"""
Pytest Configuration and Fixtures
VDO Content V2 Test Suite
"""

import pytest
import sys
from pathlib import Path
from datetime import datetime
from typing import Generator

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core.models import Project, Scene, StoryProposal, AudioSegment


# ============ Test Data Fixtures ============

@pytest.fixture
def sample_scene() -> Scene:
    """Create a sample scene for testing"""
    return Scene(
        order=1,
        narration_text="ประเทศไทยเป็นประเทศที่สวยงาม มีวัฒนธรรมอันเก่าแก่",
        veo_prompt="A beautiful Thailand landscape with ancient temples, golden sunrise lighting",
        start_time=0.0,
        end_time=5.5,
        visual_style="documentary",
        emotion="calm"
    )


@pytest.fixture
def sample_scenes() -> list[Scene]:
    """Create multiple sample scenes for testing"""
    return [
        Scene(
            order=1,
            narration_text="ประเทศไทยเป็นประเทศที่สวยงาม",
            veo_prompt="Beautiful Thai landscape with golden temples",
            start_time=0.0,
            end_time=5.0,
            visual_style="documentary"
        ),
        Scene(
            order=2,
            narration_text="อาหารไทยมีรสชาติเป็นเอกลักษณ์",
            veo_prompt="Thai cuisine being prepared by skilled chef",
            start_time=5.0,
            end_time=10.0,
            visual_style="documentary"
        ),
        Scene(
            order=3,
            narration_text="คนไทยมีน้ำใจ รอยยิ้มสยาม",
            veo_prompt="Friendly Thai people smiling at camera",
            start_time=10.0,
            end_time=15.0,
            visual_style="documentary"
        )
    ]


@pytest.fixture
def sample_project(sample_scenes) -> Project:
    """Create a sample project for testing"""
    return Project(
        title="Test Project",
        topic="Testing VDO Content features",
        description="A test project for unit testing",
        full_script="ประเทศไทยเป็นประเทศที่สวยงาม อาหารไทยมีรสชาติเป็นเอกลักษณ์",
        scenes=sample_scenes,
        target_duration=60,
        default_style="documentary",
        character_reference="Thai person, modern style",
        visual_theme="bright, warm, friendly",
        aspect_ratio="16:9"
    )


@pytest.fixture
def sample_project_no_scenes() -> Project:
    """Create a project without scenes for edge case testing"""
    return Project(
        title="Empty Project",
        topic="Testing empty project",
        scenes=[]
    )


@pytest.fixture
def sample_proposal() -> StoryProposal:
    """Create a sample story proposal"""
    return StoryProposal(
        topic="วิธีทำอาหารไทยง่ายๆ",
        analysis="This topic is about Thai cooking, suitable for food content",
        outline=["Introduction", "Ingredients", "Step-by-step", "Final result"],
        key_points=["Simple recipes", "Local ingredients", "Quick cooking"],
        status="pending"
    )


@pytest.fixture
def sample_audio_segment() -> AudioSegment:
    """Create a sample audio segment"""
    return AudioSegment(
        order=1,
        start_time=0.0,
        end_time=5.5,
        duration=5.5,
        text_content="ประเทศไทยเป็นประเทศที่สวยงาม"
    )


# ============ FastAPI Test Client Fixture ============

@pytest.fixture
def api_client():
    """Create FastAPI test client"""
    try:
        from fastapi.testclient import TestClient
        from api.main import app
        return TestClient(app)
    except ImportError:
        pytest.skip("FastAPI or test dependencies not installed")


# ============ Exporter Fixture ============

@pytest.fixture
def exporter():
    """Create ProjectExporter instance"""
    from core.exporter import ProjectExporter
    return ProjectExporter()


# ============ Mock Fixtures ============

@pytest.fixture
def mock_deepseek_response():
    """Mock DeepSeek API response"""
    return {
        "choices": [{
            "message": {
                "content": "A beautiful cinematic shot of Thailand..."
            }
        }]
    }


# ============ Pytest Configuration ============

def pytest_configure(config):
    """Configure pytest markers"""
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests"
    )
    config.addinivalue_line(
        "markers", "api: marks tests as API tests"
    )
