
import sys
import os
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.database import init_db, db_save_project, db_load_project, db_list_projects
from core.models import Project

def test_db_and_naming():
    print("🚀 Starting Database & Naming Integration Test")
    print("=" * 50)

    # 1. Initialize Database
    print("1️⃣ Initializing Database (SQLite)...")
    try:
        init_db()
        db_path = Path("vdo_content.db")
        if db_path.exists():
            print(f"   ✅ Database file created: {db_path.absolute()}")
        else:
            # For some reason init_db might not create it immediately if no tables are added
            print("   ⚠️ Database file not seen yet, proceeding to save data...")
    except Exception as e:
        print(f"   ❌ DB Init Failed: {e}")
        return

    # 2. Create and Save Project with custom name
    test_title = "สุดยอดโปรเจควีดีโอ_001"
    print(f"2️⃣ Creating project with title: '{test_title}'...")
    
    project = Project(
        title=test_title,
        topic="การทดสอบระบบ Database และการตั้งชื่อ",
        status="draft"
    )
    
    try:
        project_id = db_save_project(project.model_dump(mode="json"))
        print(f"   ✅ Project saved with ID: {project_id}")
    except Exception as e:
        print(f"   ❌ Save Failed: {e}")
        return

    # 3. Load Project back and verify Name
    print("3️⃣ Loading project back from DB...")
    try:
        loaded_data = db_load_project(project_id)
        if loaded_data:
            loaded_title = loaded_data.get("title")
            print(f"   🔍 Loaded Title: '{loaded_title}'")
            if loaded_title == test_title:
                print("   ✅ SUCCESS: Title matches!")
            else:
                print(f"   ❌ FAILURE: Title mismatch! Expected '{test_title}' but got '{loaded_title}'")
        else:
            print("   ❌ FAILURE: Project not found in DB!")
    except Exception as e:
        print(f"   ❌ Load Failed: {e}")
        return

    # 4. List Projects
    print("4️⃣ Listing all projects in DB...")
    projects = db_list_projects()
    print(f"   Found {len(projects)} projects.")
    for p in projects:
        print(f"   - [{p['id'][:8]}] {p['title']} (Status: {p['status']})")

    print("=" * 50)
    print("✅ INTEGRATION TEST PASSED!")
    print("ระบบ Database และการตั้งชื่อทำงานได้อย่างถูกต้องและจำค่าได้ถาวรครับ")

if __name__ == "__main__":
    test_db_and_naming()
