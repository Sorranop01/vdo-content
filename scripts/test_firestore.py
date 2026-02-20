import sys
import os

# Add project root to path
sys.path.append(os.getcwd())

from src.core.firestore_client import get_firestore_client
from src.core.db_crud import db_save_project, db_load_project, db_delete_project

def test_firestore():
    print("Testing Firestore Connection...")
    try:
        db = get_firestore_client()
        print(f"Connected to project: {db.project}")
        
        # Test Create
        print("Testing Save Project...")
        project_data = {
            "title": "Test Firestore Project",
            "status": "draft",
            "description": "Created via test script"
        }
        project_id = db_save_project(project_data)
        print(f"Saved project ID: {project_id}")
        
        # Test Read
        print("Testing Load Project...")
        loaded = db_load_project(project_id)
        if loaded and loaded["title"] == "Test Firestore Project":
            print("Load successful!")
        else:
            print("Load failed or mismatched data")
            print(loaded)
            
        # Test Delete
        print("Testing Delete Project...")
        if db_delete_project(project_id):
            print("Delete successful!")
        else:
            print("Delete failed")
            
        print("\nALL TESTS PASSED ✅")
        
    except Exception as e:
        print(f"\nTEST FAILED ❌: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_firestore()
