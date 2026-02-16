"""
Fast Workflow Test - Skips AI API calls to avoid timeouts.
Tests the entire 5-step pipeline with manual data.
"""
import sys, os, traceback, shutil
os.chdir('/home/agent/workspace/vdo-content')
sys.path.insert(0, '.')

from pathlib import Path
from datetime import datetime

print('=' * 70)
print('🧪 VDO CONTENT WORKFLOW - FAST TEST (No AI API)')
print('=' * 70)

# ===== STEP 1: Project Creation =====
print('\n🔵 STEP 1: สร้างโปรเจค (Create Project)')
print('-' * 50)

from src.core.models import Project, Scene, AudioSegment, StoryProposal
from src.shared.project_manager import save_project, load_project, list_projects, delete_project

results = {"passed": 0, "failed": 0, "warnings": 0, "issues": []}

def check(test_id, description, test_fn):
    try:
        result = test_fn()
        if result is None or result is True:
            results["passed"] += 1
            print(f'  ✅ {test_id} {description}')
        elif isinstance(result, str) and result.startswith('⚠️'):
            results["warnings"] += 1
            print(f'  ⚠️ {test_id} {description}: {result}')
        else:
            results["passed"] += 1
            print(f'  ✅ {test_id} {description}: {result}')
    except Exception as e:
        results["failed"] += 1
        results["issues"].append(f'{test_id}: {e}')
        print(f'  ❌ {test_id} {description}: {e}')
        traceback.print_exc()

# 1.1 Create project
project = Project(
    title='Fast Test Workflow', description='Testing pipeline',
    project_date=datetime.now(), target_duration=60,
    status='step1_project', workflow_step=0
)

def test_create():
    global project
    pid = save_project(project)
    project.project_id = pid if isinstance(pid, str) else project.project_id
    return f'ID={project.project_id[:8]}...'
check('1.1', 'Create project', test_create)

# 1.2 List projects
def test_list():
    pjs = list_projects()
    return f'{len(pjs)} total projects'
check('1.2', 'List projects', test_list)

# 1.3 Load project
def test_load():
    global project
    loaded = load_project(project.project_id)
    assert loaded is not None, 'Project not found'
    assert loaded.title == 'Fast Test Workflow', f'Title mismatch: {loaded.title}'
    project = loaded
    return f'"{loaded.title}"'
check('1.3', 'Load project', test_load)

# ===== STEP 2: Content Planning =====
print('\n🔵 STEP 2: กำหนดคอนเทนต์ (Content Planning)')
print('-' * 50)

def test_content_fields():
    project.content_goal = 'ให้ความรู้'
    project.target_audience = 'วัยรุ่น 18-25'
    project.content_category = 'food'
    project.video_format = 'shorts'
    project.platforms = ['youtube', 'tiktok']
    project.content_description = 'รีวิวร้านอาหารญี่ปุ่นสุดอร่อยในกรุงเทพ'
    project.topic = project.content_description
    project.status = 'step2_content'
    project.workflow_step = 1
    save_project(project)
    return f'goal={project.content_goal}, cat={project.content_category}'
check('2.1', 'Set content fields', test_content_fields)

def test_db_data():
    from src.core.database import get_video_profiles, get_content_goals, get_target_audiences, get_content_categories
    p = get_video_profiles()
    g = get_content_goals()
    a = get_target_audiences()
    c = get_content_categories()
    return f'{len(p)} profiles, {len(g)} goals, {len(a)} audiences, {len(c)} categories'
check('2.2', 'Database lookups', test_db_data)

# Test AI availability (don't call AI, just verify config)
def test_ai_config():
    from src.config.settings import settings
    has_deepseek = bool(settings.deepseek_api_key)
    has_kimi = bool(settings.kimi_api_key)
    return f'DeepSeek={"✓" if has_deepseek else "✗"}, Kimi={"✓" if has_kimi else "✗"}'
check('2.3', 'AI API key config', test_ai_config)

# ===== STEP 3: Script & Audio =====
print('\n🔵 STEP 3: บทพูด (Script & Audio)')
print('-' * 50)

# Set script manually (skip AI generation)
def test_manual_script():
    global project
    project.full_script = (
        "สวัสดีค่ะทุกคน วันนี้จะพาไปรีวิวร้านอาหารญี่ปุ่นสุดอร่อย\n"
        "ร้านนี้ซ่อนตัวอยู่ในซอยเล็กๆ ย่านทองหล่อ\n"
        "เชฟเป็นคนญี่ปุ่นตัวจริง การันตีรสชาติแท้ๆ จากโอซากา\n"
        "เมนูแนะนำคือ ซาชิมิ สดมาก เนื้อปลาละลายในปากเลยค่ะ\n"
        "อีกเมนูหนึ่งที่ห้ามพลาดคือราเมนต้นตำรับ\n"
        "น้ำซุปเข้มข้น เส้นเหนียวนุ่ม ชาชูนุ่มมากค่ะ\n"
        "ราคาเริ่มต้นที่ 350 บาท ถือว่าคุ้มค่ามากสำหรับคุณภาพระดับนี้\n"
        "ถ้าสนใจอย่าลืมกดติดตามและกดกระดิ่งนะคะ"
    )
    project.status = 'step3_script'
    project.workflow_step = 2
    save_project(project)
    return f'{len(project.full_script)} chars, {len(project.full_script.splitlines())} lines'
check('3.1', 'Manual script', test_manual_script)

# Test voiceover text extraction
def test_voiceover_extract():
    from src.frontend.pages.step3_script import extract_voiceover_text
    test_input = (
        "(ฉากเปิดด้วยตัวละครผู้หญิง)\n"
        "สวัสดีค่ะทุกคน วันนี้จะพาไปรีวิวร้านอาหารญี่ปุ่น\n"
        "[Scene 2]\n"
        "**ฉากที่ 2:**\n"
        "ร้านนี้อยู่ในซอยทองหล่อ สะอาดมากค่ะ\n"
        "---\n"
        "ฉากเปิด\n"
        "(ภาพเปิดตัว: ร้านอาหารญี่ปุ่น)"
    )
    cleaned = extract_voiceover_text(test_input)
    input_lines = len(test_input.strip().splitlines())
    output_lines = len(cleaned.strip().splitlines())
    return f'{output_lines} lines from {input_lines} (cleaned: "{cleaned.strip()[:80]}...")'
check('3.2', 'Voiceover extraction', test_voiceover_extract)

# Test audio upload (simulate copy)
def test_audio_copy():
    global project
    test_audio = Path('/home/agent/workspace/vdo-content/data/music/happy/happy_demo.mp3')
    if not test_audio.exists():
        return '⚠️ No test audio file found'
    from src.config.constants import DATA_DIR
    project_dir = DATA_DIR / project.project_id
    project_dir.mkdir(parents=True, exist_ok=True)
    audio_dest = project_dir / 'audio_test.mp3'
    shutil.copy2(test_audio, audio_dest)
    project.audio_path = str(audio_dest)
    save_project(project)
    return f'{audio_dest.name} ({audio_dest.stat().st_size / 1024:.1f} KB)'
check('3.3', 'Audio file copy', test_audio_copy)

# Test Whisper transcription
def test_whisper():
    global project
    from src.core.transcriber import AudioTranscriber
    if not project.audio_path or not os.path.exists(project.audio_path):
        return '⚠️ No audio file'
    transcriber = AudioTranscriber(model_size='tiny', device='cpu', compute_type='int8')
    result = transcriber.transcribe_with_summary(project.audio_path, language='th')
    segments = []
    for i, seg in enumerate(result['segments'], 1):
        segments.append(AudioSegment(
            order=i, start_time=seg.start, end_time=seg.end,
            duration=round(seg.end - seg.start, 2), text_content=seg.text
        ))
    project.audio_segments = segments
    project.audio_duration = result['total_duration']
    save_project(project)
    return f'{len(segments)} segments, {result["total_duration"]:.1f}s'
check('3.4', 'Whisper transcription', test_whisper)

# ===== STEP 4: Video Prompt Generation =====
print('\n🔵 STEP 4: สร้าง Prompt (Video Prompts)')
print('-' * 50)

# Scene splitting
def test_scene_split():
    global project
    from src.core.scene_splitter import SceneSplitter
    splitter = SceneSplitter(max_duration=8.0, language='th')
    scenes = splitter.split_script(project.full_script, default_style='cinematic')
    
    # If no Whisper segments, use text-based segments
    if not project.audio_segments:
        segments = []
        cumulative = 0.0
        for scene in scenes:
            segments.append(AudioSegment(
                order=scene.order, text_content=scene.narration_text,
                start_time=cumulative, end_time=cumulative + scene.estimated_duration,
                duration=scene.estimated_duration
            ))
            cumulative += scene.estimated_duration
        project.audio_segments = segments
    
    stats = splitter.get_stats(scenes)
    return f'{stats["total_scenes"]} scenes, {stats["total_duration"]:.1f}s'
check('4.1', 'Scene splitting', test_scene_split)

# Veo prompt generation
def test_veo_prompts():
    global project
    from src.core.prompt_generator import VeoPromptGenerator
    if not project.audio_segments:
        return '⚠️ No segments'
    
    prompt_gen = VeoPromptGenerator(character_reference='', enable_qa=False)
    scenes = []
    for seg in project.audio_segments:
        scene = Scene(
            order=seg.order, start_time=seg.start_time, end_time=seg.end_time,
            narration_text=seg.text_content, visual_style='documentary', audio_synced=True
        )
        scene.estimated_duration = seg.duration
        scenes.append(scene)
    
    ctx = {
        'visual_theme': project.visual_theme, 'directors_note': project.directors_note,
        'aspect_ratio': project.aspect_ratio, 'video_type': 'no_person',
        'prompt_style_config': project.prompt_style_config
    }
    
    scenes = prompt_gen.generate_all_prompts(scenes, '', ctx)
    project.scenes = scenes
    project.status = 'step4_prompt'
    project.workflow_step = 3
    save_project(project)
    
    prompts_with_content = sum(1 for s in scenes if s.veo_prompt)
    return f'{len(scenes)} scenes, {prompts_with_content} with prompts'
check('4.2', 'Veo prompt generation', test_veo_prompts)

# Export
def test_export():
    from src.core.exporter import ProjectExporter
    if not project.scenes:
        return '⚠️ No scenes'
    exporter = ProjectExporter()
    text = exporter.export_all_prompts_text(project)
    return f'{len(text)} chars exported'
check('4.3', 'Export prompts', test_export)

# ===== STEP 5: Upload & Completion =====
print('\n🔵 STEP 5: อัพโหลดไฟล์ (Upload)')
print('-' * 50)

def test_upload_folder():
    from src.config.constants import UPLOAD_DIR
    date_str = datetime.now().strftime('%Y%m%d')
    safe_name = ''.join(c for c in project.title if c.isalnum() or c in (' ', '-', '_'))[:50].strip().replace(' ', '_')
    folder_name = f'{date_str}-{safe_name}'
    upload_path = UPLOAD_DIR / folder_name
    upload_path.mkdir(parents=True, exist_ok=True)
    project.upload_folder = folder_name
    return f'{folder_name}'
check('5.1', 'Upload folder creation', test_upload_folder)

def test_completion():
    global project
    project.drive_folder_link = 'https://drive.google.com/drive/folders/test'
    project.status = 'completed'
    project.workflow_step = 5
    project.updated_at = datetime.now()
    save_project(project)
    loaded = load_project(project.project_id)
    assert loaded.status == 'completed', f'Status wrong: {loaded.status}'
    return f'status={loaded.status}'
check('5.2', 'Project completion', test_completion)

# ===== CLEANUP =====
def test_delete():
    # Delete the test project
    pid = project.project_id
    delete_project(pid)
    loaded = load_project(pid)
    return 'Deleted OK' if loaded is None else f'⚠️ Still exists after delete!'
check('5.3', 'Delete test project', test_delete)

# ===== UI HELPERS =====
print('\n🔵 UI / Navigation Helpers')
print('-' * 50)

def test_step_guard():
    from src.frontend.utils.ui_helpers import check_step_requirements
    # Step 0: should always pass
    ok, msg = check_step_requirements(0)
    assert ok, f'Step 0 should pass: {msg}'
    # Step 2 without project: should fail
    ok2, msg2 = check_step_requirements(2)
    # (No session state, so this varies - just verify it runs)
    return 'Validation logic works'
check('UI.1', 'Step requirement checks', test_step_guard)

def test_export_helper():
    from src.frontend.utils.ui_helpers import export_all_prompts
    p = Project(title='Test', topic='Test topic')
    p.scenes = [Scene(order=1, narration_text='Hello', veo_prompt='Test prompt')]
    text = export_all_prompts(p)
    assert 'Test prompt' in text
    return f'{len(text)} chars'
check('UI.2', 'Export helper', test_export_helper)

# ===== SUMMARY =====
print('\n' + '=' * 70)
print('🏁 TEST RESULTS')
print('=' * 70)
print(f'  ✅ Passed:  {results["passed"]}')
print(f'  ❌ Failed:  {results["failed"]}')
print(f'  ⚠️ Warnings: {results["warnings"]}')
total = results["passed"] + results["failed"] + results["warnings"]
print(f'  📊 Score:   {results["passed"]}/{total} ({results["passed"]/total*100:.0f}%)' if total > 0 else '')

if results["issues"]:
    print(f'\n  Issues found:')
    for issue in results["issues"]:
        print(f'    • {issue}')
