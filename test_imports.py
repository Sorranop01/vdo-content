#!/usr/bin/env python3
"""Comprehensive import test for all modules"""

import sys
from pathlib import Path

# Add project root to path (same as app.py does)
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

print("=" * 60)
print("COMPREHENSIVE IMPORT TEST")
print("=" * 60)
print(f"\nProject root: {project_root}")
print(f"Python path: {sys.path[0]}\n")

errors = []

# Test 1: Core modules
print("1. Testing src.core imports...")
try:
    from src.core.database import (
        get_content_categories, 
        get_target_audiences,
        get_video_profiles,
        init_db
    )
    print("   ✅ src.core.database")
except Exception as e:
    errors.append(f"src.core.database: {e}")
    print(f"   ❌ src.core.database: {e}")

try:
    from src.core.models import Project, Scene
    print("   ✅ src.core.models")
except Exception as e:
    errors.append(f"src.core.models: {e}")
    print(f"   ❌ src.core.models: {e}")

try:
    from src.core.story_analyzer import StoryAnalyzer
    print("   ✅ src.core.story_analyzer")
except Exception as e:
    errors.append(f"src.core.story_analyzer: {e}")
    print(f"   ❌ src.core.story_analyzer: {e}")

# Test 2: Shared modules
print("\n2. Testing src.shared imports...")
try:
    from src.shared.project_manager import save_project
    print("   ✅ src.shared.project_manager")
except Exception as e:
    errors.append(f"src.shared.project_manager: {e}")
    print(f"   ❌ src.shared.project_manager: {e}")

# Test 3: Config modules
print("\n3. Testing src.config imports...")
try:
    from src.config.constants import VERSION, APP_NAME
    print(f"   ✅ src.config.constants (Version: {VERSION})")
except Exception as e:
    errors.append(f"src.config.constants: {e}")
    print(f"   ❌ src.config.constants: {e}")

try:
    from src.config import settings
    print("   ✅ src.config.settings")
except Exception as e:
    errors.append(f"src.config.settings: {e}")
    print(f"   ❌ src.config.settings: {e}")

# Test 4: Frontend modules
print("\n4. Testing src.frontend imports...")
try:
    from src.frontend.utils import init_session_state
    print("   ✅ src.frontend.utils")
except Exception as e:
    errors.append(f"src.frontend.utils: {e}")
    print(f"   ❌ src.frontend.utils: {e}")

try:
    from src.frontend.styles import apply_dark_mode
    print("   ✅ src.frontend.styles")
except Exception as e:
    errors.append(f"src.frontend.styles: {e}")
    print(f"   ❌ src.frontend.styles: {e}")

try:
    from src.frontend.components import show_progress_bar
    print("   ✅ src.frontend.components")
except Exception as e:
    errors.append(f"src.frontend.components: {e}")
    print(f"   ❌ src.frontend.components: {e}")

# Test 5: Database functions
print("\n5. Testing database functions...")
try:
    cats = get_content_categories()
    print(f"   ✅ get_content_categories() - {len(cats)} categories")
except Exception as e:
    errors.append(f"get_content_categories: {e}")
    print(f"   ❌ get_content_categories(): {e}")

try:
    auds = get_target_audiences()
    print(f"   ✅ get_target_audiences() - {len(auds)} audiences")
except Exception as e:
    errors.append(f"get_target_audiences: {e}")
    print(f"   ❌ get_target_audiences(): {e}")

# Summary
print("\n" + "=" * 60)
if errors:
    print(f"❌ FAILED: {len(errors)} errors found")
    print("\nErrors:")
    for err in errors:
        print(f"  - {err}")
    sys.exit(1)
else:
    print("✅ ALL TESTS PASSED!")
    print("=" * 60)
    sys.exit(0)
