#!/usr/bin/env python3
"""Test script for database migration and seed data"""

import sys
sys.path.insert(0, '/home/agent/workspace/vdo-content')

from src.core.database import init_db, get_content_categories, get_target_audiences

print("=" * 50)
print("DATABASE MIGRATION TEST")
print("=" * 50)

try:
    print("\n1. Running database initialization...")
    init_db()
    print("✅ Database initialized successfully\n")
    
    print("2. Testing get_content_categories()...")
    categories = get_content_categories()
    print(f"✅ Found {len(categories)} categories:\n")
    for cat in categories:
        print(f"   {cat['icon']} {cat['name_th']} ({cat['name_en']})")
    
    print(f"\n3. Testing get_target_audiences()...")
    audiences = get_target_audiences()
    print(f"✅ Found {len(audiences)} audiences:\n")
    for aud in audiences:
        print(f"   👥 {aud['name_th']} ({aud['age_range']})")
    
    print("\n" + "=" * 50)
    print("✅ ALL TESTS PASSED!")
    print("=" * 50)
    
except Exception as e:
    print(f"\n❌ ERROR: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
