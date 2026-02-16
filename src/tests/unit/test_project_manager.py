import pytest
import uuid
import json
from pathlib import Path
from unittest.mock import patch, MagicMock, mock_open

# Adjust path to find src
import sys
import os
sys.path.append(os.getcwd())

from src.core.models import Project
import importlib
import src.shared.project_manager

# Mock streamlit BEFORE importing/reloading project_manager
mock_st = MagicMock()
# Configure cache_data to be a passthrough decorator
def passthrough_decorator(*args, **kwargs):
    def decorator(f):
        return f
    return decorator
mock_st.cache_data.side_effect = passthrough_decorator

# Apply the mock to sys.modules and RELOAD the module
with patch.dict('sys.modules', {'streamlit': mock_st}):
    importlib.reload(src.shared.project_manager)
    from src.shared.project_manager import save_project, load_project, _sanitize_id

# ============ Test Sanitization ============

def test_sanitize_id_valid_uuid():
    valid_uuid = str(uuid.uuid4())
    assert _sanitize_id(valid_uuid) == valid_uuid

def test_sanitize_id_path_string():
    # Simulate the corruption scenario: a path instead of UUID
    bad_id = "/app/data/some-uuid/project.json"
    sanitized = _sanitize_id(bad_id)
    
    # Logic tries to extract basename if it looks like uuid
    # "project.json" is not uuid, so it should generate new
    assert sanitized != bad_id
    try:
        uuid.UUID(sanitized)
    except ValueError:
        pytest.fail("Sanitized ID is not a valid UUID")

def test_sanitize_id_embedded_uuid_path():
    # If path ends in UUID
    fake_uuid = str(uuid.uuid4())
    bad_id = f"/app/data/{fake_uuid}"
    
    # Should extract valid UUID from basename
    sanitized = _sanitize_id(bad_id)
    assert sanitized == fake_uuid

def test_sanitize_id_garbage():
    sanitized = _sanitize_id("not-a-uuid")
    assert sanitized != "not-a-uuid"
    uuid.UUID(sanitized)  # Should not raise

def test_sanitize_id_empty():
    sanitized = _sanitize_id("")
    assert sanitized != ""
    uuid.UUID(sanitized)


# ============ Test Save Project ============

@pytest.fixture
def mock_project():
    return Project(
        project_id=str(uuid.uuid4()),
        title="Test Project",
        topic="Unit Testing"
    )

@patch("src.shared.project_manager.db_save_project")
@patch("src.shared.project_manager._check_database")
def test_save_project_db_success(mock_check_db, mock_db_save, mock_project):
    """Test normal save flow to DB"""
    mock_check_db.return_value = True
    # Simulate DB returning the same ID
    mock_db_save.return_value = mock_project.project_id
    
    saved_id = save_project(mock_project)
    
    assert saved_id == mock_project.project_id
    mock_db_save.assert_called_once()


@patch("src.shared.project_manager.settings")
@patch("src.shared.project_manager.db_save_project")
@patch("src.shared.project_manager._check_database")
def test_save_project_db_fail_json_fallback(mock_check_db, mock_db_save, mock_settings, mock_project):
    """Test DB failure falling back to JSON"""
    mock_check_db.return_value = True
    mock_db_save.side_effect = Exception("DB Connection Error")
    
    # Mock data dir
    mock_path = MagicMock()
    mock_settings.data_dir = mock_path
    mock_project_dir = MagicMock()
    mock_path.__truediv__.return_value = mock_project_dir
    
    # Mock file operations
    with patch("builtins.open", mock_open()) as mock_file:
        saved_id = save_project(mock_project)
    
    assert saved_id == mock_project.project_id
    # Should have tried to mkdir
    mock_project_dir.mkdir.assert_called_once()
    # Should have opened file to write
    mock_file.assert_called_once()


@patch("src.shared.project_manager.settings")
@patch("src.shared.project_manager._check_database")
def test_save_project_corrupted_id_recovery(mock_check_db, mock_settings):
    """Test saving a project with corrupted ID triggers sanitization"""
    mock_check_db.return_value = False # Force JSON path to test file ops primarily
    
    bad_id = "/var/lib/data/bad_id.json"
    project = Project(project_id=bad_id, title="Bad ID", topic="Test")
    
    # Mock data dir
    mock_path = MagicMock()
    mock_settings.data_dir = mock_path
    
    # Mock path operations
    mock_project_dir = MagicMock()
    mock_path.__truediv__.return_value = mock_project_dir
    
    with patch("builtins.open", mock_open()):
        saved_id = save_project(project)
    
    # Assert IS SANITIZED
    assert saved_id != bad_id
    uuid.UUID(saved_id) # Should be valid UUID
    
    # Also assert project object was updated
    assert project.project_id == saved_id


@patch("src.shared.project_manager.settings")
@patch("src.shared.project_manager._check_database")
def test_save_project_file_conflict_resolution(mock_check_db, mock_settings, mock_project):
    """Test that if target directory exists as a FILE, it is removed"""
    mock_check_db.return_value = False
    
    mock_path = MagicMock()
    mock_settings.data_dir = mock_path
    mock_project_dir = MagicMock()
    mock_path.__truediv__.return_value = mock_project_dir
    
    # Simulate: is_file() returns True (conflict!)
    mock_project_dir.is_file.return_value = True
    
    with patch("builtins.open", mock_open()):
        save_project(mock_project)
        
    # Should have called unlink to remove the conflicting file
    mock_project_dir.unlink.assert_called_once()
    # Then mkdir
    mock_project_dir.mkdir.assert_called()


# ============ Test Load Project ============

@patch("src.shared.project_manager.db_load_project")
@patch("src.shared.project_manager._check_database")
def test_load_project_db_success(mock_check_db, mock_db_load):
    mock_check_db.return_value = True
    pid = str(uuid.uuid4())
    mock_db_load.return_value = {
        "project_id": pid,
        "title": "Loaded from DB",
        "topic": "DB"
    }
    
    project = load_project(pid)
    assert project.title == "Loaded from DB"
    assert project.project_id == pid

@patch("src.shared.project_manager.settings")
@patch("src.shared.project_manager._check_database")
def test_load_project_json_fallback(mock_check_db, mock_settings):
    mock_check_db.return_value = False # Force JSON
    
    pid = str(uuid.uuid4())
    mock_data = {
        "project_id": pid,
        "title": "Loaded from JSON",
        "topic": "File"
    }
    
    mock_path = MagicMock()
    mock_settings.data_dir = mock_path
    
    with patch("builtins.open", mock_open(read_data=json.dumps(mock_data))):
        with patch("json.load", return_value=mock_data):
            project = load_project(pid)
            
    assert project.title == "Loaded from JSON"

@patch("src.shared.project_manager.settings")
@patch("src.shared.project_manager._check_database")
def test_load_project_partial_recovery(mock_check_db, mock_settings):
    """Test loading data with invalid schema fields"""
    mock_check_db.return_value = False
    
    pid = str(uuid.uuid4())
    # Data has extra unknown field
    mock_data = {
        "project_id": pid,
        "title": "Partial Load",
        "unknown_field_xyz": 123
    }
    
    mock_path = MagicMock()
    mock_settings.data_dir = mock_path
    
    with patch("builtins.open", mock_open(read_data=json.dumps(mock_data))):
        with patch("json.load", return_value=mock_data):
            # Should not raise validation error, but strip unknown field
            project = load_project(pid)
            
    assert project.title == "Partial Load"
    # Project model strictness usually ignores extra fields by default in Pydantic V2 unless ConfigDict says otherwise
    # But _safe_create_project handles exceptions if they occur.
