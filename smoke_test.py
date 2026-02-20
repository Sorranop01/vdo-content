import sys
import logging
from pathlib import Path

# Setup logging
logging.basicConfig(level=logging.INFO)

print("Starting smoke test...")

errors = []

try:
    print("1. Testing models.py")
    from src.core.models import Scene, Project
    scene = Scene(scene_id="s1", order=1, narration_text="Hello world")
    proj = Project(project_id="p1", title="Test", scenes=[scene])
    print("   [OK] models")
except Exception as e:
    errors.append(f"models: {e}")

try:
    print("2. Testing templates_manager.py")
    from src.core.templates_manager import list_templates, load_template
    th_template = load_template("builtin-thai-lifestyle")
    if not th_template:
        raise ValueError("th_template not found")
    print(f"   [OK] Loaded template: {th_template.name}")
except Exception as e:
    errors.append(f"templates_manager: {e}")

try:
    print("3. Testing platform_adapter.py")
    from src.core.platform_adapter import generate_platform_variants
    variants = generate_platform_variants("A dog in the park", platforms=["tiktok", "youtube"])
    if not variants or "tiktok" not in variants:
        raise ValueError("Failed to generate variants")
    print("   [OK] platform_adapter generated tiktok and youtube")
except Exception as e:
    errors.append(f"platform_adapter: {e}")

try:
    print("4. Testing consistency_checker.py")
    from src.core.consistency_checker import VisualConsistencyChecker, extract_visual_attributes
    checker = VisualConsistencyChecker()
    s1 = Scene(scene_id="s1", order=1, narration_text="1", veo_prompt="A Thai woman with black hair")
    s2 = Scene(scene_id="s2", order=2, narration_text="2", veo_prompt="A European man with blonde hair")
    report = checker.check([s1, s2])
    print(f"   [OK] Consistency found {len(report.issues)} issues")
except Exception as e:
    errors.append(f"consistency_checker: {e}")

try:
    print("5. Testing analytics.py")
    from src.core.analytics import get_project_stats
    stats = get_project_stats()
    print("   [OK] analytics module loads")
except Exception as e:
    errors.append(f"analytics: {e}")

try:
    print("6. Testing exporter.py")
    from src.core.exporter import ProjectExporter
    exporter = ProjectExporter()
    edl = exporter.export_edl(proj)
    print("   [OK] exporter generated EDL string")
except Exception as e:
    errors.append(f"exporter: {e}")

if errors:
    print("\nSMOKE TEST FAILED:")
    for err in errors:
        print(f" - {err}")
    sys.exit(1)
else:
    print("\nALL SMOKE TESTS PASSED!")
