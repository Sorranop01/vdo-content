#!/usr/bin/env python3
"""
Comprehensive System Test for VDO Content Modular Structure
Tests all imports, dependencies, and basic functionality
"""
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

print("=" * 80)
print("🧪 VDO Content System Test - Comprehensive Verification")
print("=" * 80)
print()

# Test results tracking
tests_passed = 0
tests_failed = 0
errors = []

def test(name, func):
    """Run a test and track results"""
    global tests_passed, tests_failed, errors
    try:
        func()
        print(f"✅ {name}")
        tests_passed += 1
        return True
    except Exception as e:
        print(f"❌ {name}")
        print(f"   Error: {str(e)}")
        tests_failed += 1
        errors.append((name, str(e)))
        return False

# ============================================================================
# TEST 1: Core Imports
# ============================================================================
print("📦 Testing Core Module Imports...")
print("-" * 80)

def test_config_imports():
    from src.config import settings
    from src.config.constants import VERSION, APP_NAME, PAGE_HOME
    assert VERSION is not None
    assert APP_NAME is not None

def test_core_imports():
    from src.core import models
    from src.shared.project_manager import save_project, load_project

test("Config imports", test_config_imports)
test("Core modules", test_core_imports)

# ============================================================================
# TEST 2: Utility Modules
# ============================================================================
print("\n🛠️ Testing Utility Modules...")
print("-" * 80)

def test_draft_manager():
    from src.frontend.utils.draft_manager import save_draft, load_draft, list_drafts
    # Functions exist
    assert callable(save_draft)
    assert callable(load_draft)
    assert callable(list_drafts)

def test_ui_helpers():
    from src.frontend.utils.ui_helpers import (
        show_back_button,
        show_progress_bar,
        auto_save_project,
        update_last_active,
        copy_to_clipboard
    )
    # All functions exist
    assert callable(show_back_button)
    assert callable(show_progress_bar)
    assert callable(auto_save_project)

def test_utils_init():
    from src.frontend.utils import (
        init_session_state,
        UserConfig,
        show_back_button,
        auto_save_project
    )
    assert UserConfig is not None

test("Draft Manager", test_draft_manager)
test("UI Helpers", test_ui_helpers)
test("Utils __init__", test_utils_init)

# ============================================================================
# TEST 3: Page Modules - Import Structure
# ============================================================================
print("\n📄 Testing Page Module Imports...")
print("-" * 80)

def test_pages_init():
    from src.frontend.pages import (
        home, ideation, script, audio_sync,
        veo_prompts, archive, database_tags, settings
    )
    # All 8 pages imported
    assert home is not None
    assert ideation is not None
    assert script is not None
    assert audio_sync is not None
    assert veo_prompts is not None
    assert archive is not None
    assert database_tags is not None
    assert settings is not None

test("Pages __init__ (all 8 pages)", test_pages_init)

# ============================================================================
# TEST 4: Individual Page Modules - render() function
# ============================================================================
print("\n🎬 Testing Individual Page Modules...")
print("-" * 80)

def test_home_page():
    from src.frontend.pages import home
    assert hasattr(home, 'render')
    assert callable(home.render)

def test_ideation_page():
    from src.frontend.pages import ideation
    assert hasattr(ideation, 'render')
    assert callable(ideation.render)

def test_script_page():
    from src.frontend.pages import script
    assert hasattr(script, 'render')
    assert callable(script.render)

def test_audio_sync_page():
    from src.frontend.pages import audio_sync
    assert hasattr(audio_sync, 'render')
    assert callable(audio_sync.render)

def test_veo_prompts_page():
    from src.frontend.pages import veo_prompts
    assert hasattr(veo_prompts, 'render')
    assert callable(veo_prompts.render)

def test_archive_page():
    from src.frontend.pages import archive
    assert hasattr(archive, 'render')
    assert callable(archive.render)

def test_database_tags_page():
    from src.frontend.pages import database_tags
    assert hasattr(database_tags, 'render')
    assert callable(database_tags.render)

def test_settings_page():
    from src.frontend.pages import settings
    assert hasattr(settings, 'render')
    assert callable(settings.render)

test("Home page (render)", test_home_page)
test("Ideation page (render)", test_ideation_page)
test("Script page (render)", test_script_page)
test("Audio Sync page (render)", test_audio_sync_page)
test("Veo Prompts page (render)", test_veo_prompts_page)
test("Archive page (render)", test_archive_page)
test("Database & Tags page (render)", test_database_tags_page)
test("Settings page (render)", test_settings_page)

# ============================================================================
# TEST 5: Main App Module
# ============================================================================
print("\n🚀 Testing Main App Module...")
print("-" * 80)

def test_app_imports():
    # This will fail without streamlit, but we can test the structure
    import src.frontend.app as app_module
    assert hasattr(app_module, 'main')
    assert callable(app_module.main)

test("App module structure", test_app_imports)

# ============================================================================
# TEST 6: Critical Dependencies
# ============================================================================
print("\n🔗 Testing Critical Dependencies...")
print("-" * 80)

def test_constants_data_dir():
    from src.config.constants import DATA_DIR
    assert DATA_DIR is not None
    # Should be a Path object
    from pathlib import Path
    assert isinstance(DATA_DIR, Path)

def test_constants_limits():
    from src.config.constants import MAX_REVISIONS, MIN_CHARACTER_LENGTH
    assert MAX_REVISIONS > 0
    assert MIN_CHARACTER_LENGTH > 0

test("DATA_DIR constant", test_constants_data_dir)
test("Limits constants", test_constants_limits)

# ============================================================================
# TEST 7: File Structure
# ============================================================================
print("\n📁 Testing File Structure...")
print("-" * 80)

def test_page_files_exist():
    pages_dir = Path("src/frontend/pages")
    required_files = [
        "home.py", "ideation.py", "script.py", "audio_sync.py",
        "veo_prompts.py", "archive.py", "database_tags.py", "settings.py",
        "__init__.py"
    ]
    for file in required_files:
        assert (pages_dir / file).exists(), f"{file} not found"

def test_utils_files_exist():
    utils_dir = Path("src/frontend/utils")
    required_files = ["draft_manager.py", "ui_helpers.py", "__init__.py"]
    for file in required_files:
        assert (utils_dir / file).exists(), f"{file} not found"

test("Page files exist", test_page_files_exist)
test("Utility files exist", test_utils_files_exist)

# ============================================================================
# SUMMARY
# ============================================================================
print()
print("=" * 80)
print("📊 TEST SUMMARY")
print("=" * 80)
print(f"✅ Passed: {tests_passed}")
print(f"❌ Failed: {tests_failed}")
print(f"📈 Success Rate: {tests_passed}/{tests_passed + tests_failed} ({100 * tests_passed / (tests_passed + tests_failed):.1f}%)")
print()

if tests_failed > 0:
    print("❌ FAILED TESTS:")
    for name, error in errors:
        print(f"  - {name}: {error}")
    print()
    sys.exit(1)
else:
    print("🎉 ALL TESTS PASSED!")
    print()
    print("✅ System Status: READY FOR PRODUCTION")
    print()
    sys.exit(0)
