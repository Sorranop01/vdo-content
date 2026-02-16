"""
VDO Content V2 - AI Content Pipeline
AI-powered video content creation tool with synchronized narration and visuals

Features V2.2:
- 📂 Home/Dashboard with project list
- 📋 Copy buttons everywhere
- 📊 Progress bar in sidebar
- ← Back navigation
- 💾 Auto-save
- 🌙 Dark mode toggle
- 📁 Batch export prompts
- 🗃️ PostgreSQL database support
"""

import streamlit as st
import json
import os
import uuid
from pathlib import Path
from datetime import datetime
import tempfile

# Load environment variables from .env file
from dotenv import load_dotenv
load_dotenv()

# Add parent directory to path
import sys
sys.path.insert(0, str(Path(__file__).parent))

from core.models import Project, Scene, StoryProposal, AudioSegment, STYLE_PRESETS
from core.scene_splitter import SceneSplitter
from core.prompt_generator import VeoPromptGenerator
from core.script_generator import ScriptGenerator
from core.story_analyzer import StoryAnalyzer
from core.audio_analyzer import AudioAnalyzer
from core.aistudio_generator import generate_ai_studio_output

# AI Transcription support
try:
    from core.transcriber import AudioTranscriber, TranscriptSegment
    TRANSCRIPTION_AVAILABLE = True
except ImportError:
    TRANSCRIPTION_AVAILABLE = False
    AudioTranscriber = None

# Google TTS support
try:
    from core.tts_generator import GoogleTTSGenerator
    TTS_AVAILABLE = True
except ImportError:
    TTS_AVAILABLE = False

# Google Drive Upload support
try:
    from core.drive_uploader import DriveUploader, get_drive_uploader
    DRIVE_UPLOAD_AVAILABLE = True
except ImportError:
    DRIVE_UPLOAD_AVAILABLE = False
    DriveUploader = None
    GoogleTTSGenerator = None

# AI Studio Voice support (Gemini)
try:
    from core.aistudio_voice import AIStudioVoiceGenerator
    AISTUDIO_VOICE_AVAILABLE = True
except ImportError:
    AISTUDIO_VOICE_AVAILABLE = False
    AIStudioVoiceGenerator = None

# Stock Video support
try:
    from core.stock_finder import StockVideoFinder
    STOCK_FINDER_AVAILABLE = True
except ImportError:
    STOCK_FINDER_AVAILABLE = False
    StockVideoFinder = None

# Video Renderer
try:
    from core.video_renderer import VideoRenderer
    RENDERER_AVAILABLE = True
except ImportError:
    RENDERER_AVAILABLE = False
    VideoRenderer = None

# Database support
try:
    from core.database import (
        init_db, db_save_project, db_load_project, db_list_projects, db_delete_project,
        db_save_draft, db_load_draft, db_delete_draft, db_list_drafts, get_visual_tags,
        save_style_profile, list_style_profiles, delete_style_profile,
        add_visual_tag, delete_visual_tag, update_visual_tag, get_all_tags_raw,
        log_api_usage, save_media_asset,
        list_video_profiles, get_video_profile  # Video profile functions
    )
    DATABASE_AVAILABLE = True
    
    # Cache database initialization for multi-user access
    @st.cache_resource
    def _init_database():
        """Initialize database with caching for performance"""
        init_db()
        return True
    
    _init_database()  # Create tables on startup with caching
except Exception as e:
    DATABASE_AVAILABLE = False
    print(f"Database not available: {e}. Using JSON fallback.")
    
    # Mock tags if DB fails
    @st.cache_data(ttl=3600)  # Cache for 1 hour
    def get_visual_tags():
        return {
            "mood": [{"label": "Bright", "value": "bright"}],
            "lighting": [{"label": "Natural", "value": "natural"}],
            "camera_angle": [{"label": "Eye Level", "value": "eye level"}],
            "movement": [{"label": "Static", "value": "static"}]
        }
    def list_style_profiles(): return []
    def save_style_profile(n, c, d): return False
    def add_visual_tag(c, l, v): return False
    def delete_visual_tag(c, l): return False
    def list_video_profiles(): return []
    def get_video_profile(pid): return None

# Exporter support
try:
    from core.exporter import ProjectExporter
    EXPORTER_AVAILABLE = True
except ImportError:
    EXPORTER_AVAILABLE = False
    ProjectExporter = None

# Try to import pyperclip for copy functionality
try:
    import pyperclip
    PYPERCLIP_AVAILABLE = True
except ImportError:
    PYPERCLIP_AVAILABLE = False

# Page config with dark mode support
st.set_page_config(
    page_title="VDO Content V2",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Constants
DATA_DIR = Path(__file__).parent / "data" / "projects"
DATA_DIR.mkdir(parents=True, exist_ok=True)
MAX_REVISIONS = 3
VERSION = "2.2.0"


# ============ Dark Mode CSS ============
def apply_dark_mode():
    """Apply dark mode styling"""
    if st.session_state.get("dark_mode", False):
        st.markdown("""
        <style>
        .stApp {
            background-color: #1a1a2e;
            color: #eaeaea;
        }
        .stSidebar {
            background-color: #16213e;
        }
        .stTextInput > div > div > input,
        .stTextArea > div > div > textarea,
        .stSelectbox > div > div > div {
            background-color: #0f3460;
            color: #eaeaea;
        }
        .stButton > button {
            background-color: #e94560;
            color: white;
        }
        </style>
        """, unsafe_allow_html=True)


# ============ Mobile Responsive CSS ============
def apply_mobile_styles():
    """Apply responsive mobile-friendly styles"""
    st.markdown("""
    <style>
    /* Mobile Responsive Breakpoints */
    @media (max-width: 768px) {
        /* Sidebar - full width when open on mobile */
        [data-testid="stSidebar"] {
            width: 100% !important;
            min-width: 100% !important;
        }
        
        /* Main content - full width on mobile */
        .main .block-container {
            padding-left: 1rem !important;
            padding-right: 1rem !important;
            max-width: 100% !important;
        }
        
        /* Stack columns vertically on mobile */
        [data-testid="column"] {
            width: 100% !important;
            flex: 100% !important;
            min-width: 100% !important;
        }
        
        /* Larger touch targets for buttons */
        .stButton > button {
            min-height: 48px !important;
            font-size: 16px !important;
            padding: 12px 24px !important;
        }
        
        /* Input fields - larger touch area */
        .stTextInput > div > div > input,
        .stTextArea > div > div > textarea,
        .stSelectbox > div > div {
            min-height: 48px !important;
            font-size: 16px !important;
        }
        
        /* Cards - full width with proper spacing */
        .stContainer {
            padding: 8px !important;
        }
        
        /* Metrics - stack and center */
        [data-testid="stMetricValue"] {
            font-size: 1.5rem !important;
        }
        
        /* Expander - easier to tap */
        .streamlit-expanderHeader {
            padding: 16px !important;
        }
        
        /* Title sizing for mobile */
        h1 { font-size: 1.75rem !important; }
        h2 { font-size: 1.5rem !important; }
        h3 { font-size: 1.25rem !important; }
        
        /* Popover buttons - better mobile sizing */
        [data-testid="stPopover"] button {
            min-height: 44px !important;
        }
        
        /* CRITICAL: Fix button click issues in stacked columns */
        [data-testid="stHorizontalBlock"] {
            position: relative;
            z-index: 1;
        }
        
        /* Ensure buttons in columns are clickable on mobile */
        [data-testid="column"] .stButton {
            position: relative;
            z-index: 10;
            isolation: isolate;
        }
        
        [data-testid="column"] .stButton > button {
            position: relative;
            z-index: 11;
            pointer-events: auto !important;
            touch-action: manipulation;
            -webkit-tap-highlight-color: rgba(0,0,0,0.1);
        }
        
        /* Prevent any overlay from blocking buttons */
        .stButton > button {
            pointer-events: auto !important;
        }
    }
    
    /* Small mobile devices (< 480px) */
    @media (max-width: 480px) {
        /* Even larger touch targets */
        .stButton > button {
            min-height: 56px !important;
            width: 100% !important;
        }
        
        /* Single action per row */
        [data-testid="stHorizontalBlock"] {
            flex-wrap: wrap !important;
        }
        
        /* Reduce padding further */
        .main .block-container {
            padding-left: 0.5rem !important;
            padding-right: 0.5rem !important;
        }
        
        /* Smaller titles for very small screens */
        h1 { font-size: 1.5rem !important; }
        h2 { font-size: 1.25rem !important; }
    }
    
    /* Touch interaction improvements */
    @media (hover: none) and (pointer: coarse) {
        /* For touch devices - visual feedback */
        .stButton > button:active {
            transform: scale(0.98);
            opacity: 0.9;
        }
        
        /* Remove hover effects that can be sticky on touch */
        .stButton > button:hover {
            transform: none;
        }
    }
    </style>
    """, unsafe_allow_html=True)


# ============ User Config & Persistence ============
USER_CONFIG_FILE = DATA_DIR / "user_config.json"

def save_user_config(config: dict):
    """Save user preferences and last state"""
    try:
        current = load_user_config()
        current.update(config)
        with open(USER_CONFIG_FILE, "w") as f:
            json.dump(current, f)
    except Exception:
        pass

def load_user_config() -> dict:
    """Load user preferences"""
    if USER_CONFIG_FILE.exists():
        try:
            with open(USER_CONFIG_FILE, "r") as f:
                return json.load(f)
        except Exception:
            pass
    return {}

def update_last_active(project_id: str, page_index: int):
    """Update last active state"""
    save_user_config({
        "last_project_id": project_id,
        "last_page": page_index,
        "last_updated": datetime.now().isoformat()
    })

# ============ Session State ============
def init_session_state():
    """Initialize session state"""
    # Generate unique session ID if not exists
    if "session_id" not in st.session_state:
        st.session_state.session_id = str(uuid.uuid4())[:8]
    
    defaults = {
        "current_project": None,
        "proposal": None,
        "proposal_version": 1,
        "script": "",
        "audio_segments": [],
        "scenes": [],
        "page": 0,  # 0 = Home
        "api_key": os.getenv("DEEPSEEK_API_KEY", ""),
        "dark_mode": False,
        "auto_save": True,
        # Draft fields for Ideation (persist on page refresh)
        "draft_title": "",
        "draft_topic": "",
        "draft_style": "documentary",
        "draft_duration": 60,
        "draft_character": "",
        "draft_loaded": False  # Flag to prevent reload loop
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value
    
    # Auto-Load Last Project (Only on first load)
    if "init_done" not in st.session_state:
        config = load_user_config()
        last_id = config.get("last_project_id")
        last_page = config.get("last_page", 0)
        
        if last_id and not st.session_state.current_project:
            try:
                project = load_project(last_id)
                reset_session_for_project(project)  # ✅ Use new reset function
                st.session_state.page = last_page
                st.toast(f"🔄 Resumed project: {project.title}", icon="📂")
            except Exception:
                pass
        
        # Load draft
        if DATABASE_AVAILABLE:
            try:
                draft = db_load_draft(st.session_state.session_id, "ideation")
                if draft:
                    st.session_state.draft_title = draft.get("title", "")
                    st.session_state.draft_topic = draft.get("topic", "")
                    
                    # Validate style - ensure it's a valid enum value
                    loaded_style = draft.get("style", "documentary")
                    valid_styles = ["realistic", "cinematic", "animated", "documentary", "minimalist", "energetic"]
                    st.session_state.draft_style = loaded_style if loaded_style in valid_styles else "documentary"
                    
                    st.session_state.draft_duration = draft.get("duration", 60)
                    st.session_state.draft_character = draft.get("character", "")
            except Exception:
                pass
        
        st.session_state.init_done = True


def reset_session_for_project(project):
    """Reset all session state when loading a project to prevent data leakage"""
    # Clear all project-specific session variables
    keys_to_clear = [
        'scenes', 'proposal', 'uploaded_audio_path', 'audio_file_name',
        'character_reference', 'style_instructions', 'visual_style_preset',
        'selected_techniques', 'enable_qa', 'script_method', 'ai_provider',
        'selected_language', 'selected_tone', 'selected_voice_tone'
    ]
    
    for key in keys_to_clear:
        if key in st.session_state:
            del st.session_state[key]
    
    # Load ALL data from the selected project
    st.session_state.current_project = project
    st.session_state.script = project.full_script or ""
    st.session_state.audio_segments = project.audio_segments or []
    st.session_state.scenes = project.scenes or []  # ✅ Load scenes (was missing!)
    st.session_state.proposal = project.proposal  # ✅ Load proposal (was missing!)
    
    # Load additional project properties
    if project.audio_path:
        st.session_state.uploaded_audio_path = project.audio_path
    
    if project.character_reference:
        st.session_state.character_reference = project.character_reference
    
    if project.style_instructions:
        st.session_state.style_instructions = project.style_instructions
    
    # Load default style from project
    if project.default_style:
        st.session_state.draft_style = project.default_style
    
    # Set video profile if exists
    if project.video_profile_id:
        st.session_state.video_profile_id = project.video_profile_id


# ============ Utility Functions ============
def copy_to_clipboard(text: str, key: str):
    """Copy text using JavaScript (works on remote servers including HTTP)"""
    import streamlit.components.v1 as components
    import html
    import json
    
    # Escape text properly for JavaScript string
    # Use JSON.stringify to safely encode the text
    json_escaped = json.dumps(text)
    
    # JavaScript to copy to clipboard with robust fallback
    # The fallback method works even on HTTP (non-secure contexts)
    js_code = f"""
        <script>
        (function() {{
            const textToCopy = {json_escaped};
            
            function fallbackCopy(text) {{
                // Create a hidden textarea
                const ta = document.createElement('textarea');
                ta.value = text;
                ta.style.position = 'fixed';
                ta.style.left = '-9999px';
                ta.style.top = '0';
                ta.style.opacity = '0';
                ta.style.zIndex = '9999';  // Ensure it's on top
                document.body.appendChild(ta);
                ta.focus();
                ta.select();
                
                try {{
                    const successful = document.execCommand('copy');
                    if (successful) {{
                        console.log('Fallback copy succeeded');
                        showSuccess();
                    }} else {{
                        console.log('Fallback copy failed');
                        showError();
                    }}
                }} catch (err) {{
                    console.error('Fallback copy error:', err);
                    showError();
                }}
                
                document.body.removeChild(ta);
            }}
            
            function showSuccess() {{
                const msg = document.getElementById('copy-msg-{key}');
                if (msg) {{
                    msg.innerHTML = '✅ คัดลอกแล้ว!';
                    msg.style.color = '#00c853';
                    msg.style.fontWeight = 'bold';
                }}
            }}
            
            function showError() {{
                const msg = document.getElementById('copy-msg-{key}');
                if (msg) {{
                    msg.innerHTML = '⚠️ กรุณาเลือกข้อความและกด Ctrl+C';
                    msg.style.color = '#ff9800';
                }}
            }}
            
            // Try modern clipboard API first (requires HTTPS or localhost)
            if (navigator.clipboard && window.isSecureContext) {{
                navigator.clipboard.writeText(textToCopy)
                    .then(function() {{
                        console.log('Clipboard API succeeded');
                        showSuccess();
                    }})
                    .catch(function(err) {{
                        console.log('Clipboard API failed, trying fallback:', err);
                        fallbackCopy(textToCopy);
                    }});
            }} else {{
                // Use fallback for non-secure contexts (HTTP)
                console.log('Using fallback copy (non-secure context)');
                fallbackCopy(textToCopy);
            }}
        }})();
        </script>
        <div id="copy-msg-{key}" style="color: #888; font-size: 14px; margin-top: 5px; padding: 5px; border-radius: 4px; background: #f0f0f0;">⏳ กำลังคัดลอก...</div>
    """
    
    # Increase height to 60px for better visibility and prevent clipping issues
    components.html(js_code, height=60)
    return True


def save_draft_to_db():
    """Save current draft to database"""
    if not DATABASE_AVAILABLE:
        return False
    
    try:
        content = {
            "title": st.session_state.draft_title,
            "topic": st.session_state.draft_topic,
            "style": st.session_state.draft_style,
            "duration": st.session_state.draft_duration,
            "character": st.session_state.draft_character
        }
        db_save_draft(st.session_state.session_id, "ideation", content)
        return True
    except Exception as e:
        print(f"Draft save error: {e}")
        return False


def clear_draft_from_db():
    """Clear draft from database after project is created"""
    if not DATABASE_AVAILABLE:
        return
    
    try:
        db_delete_draft(st.session_state.session_id, "ideation")
    except Exception:
        pass


def show_progress_bar():
    """Show workflow progress in sidebar"""
    page = st.session_state.page
    if page == 0:
        return
    
    # Total steps including Settings page
    total_steps = 6
    progress = page / total_steps
    
    # Safeguard to ensure progress is between 0.0 and 1.0
    progress = max(0.0, min(progress, 1.0))
    
    st.sidebar.markdown("---")
    st.sidebar.markdown("**📊 Progress:**")
    st.sidebar.progress(progress)
    st.sidebar.caption(f"Step {page}/{total_steps}")


def show_back_button():
    """Show back navigation button"""
    if st.session_state.page > 0:
        if st.button("← Back", key="back_btn"):
            st.session_state.page = max(0, st.session_state.page - 1)
            st.rerun()


def auto_save_project():
    """Auto-save current project if enabled"""
    if st.session_state.auto_save and st.session_state.current_project:
        pid = save_project(st.session_state.current_project)
        # Also save as last active
        update_last_active(st.session_state.current_project.project_id, st.session_state.page)


# ============ Project Management ============
def save_project(project: Project) -> str:
    """Save project to database (or JSON fallback)"""
    project_data = project.model_dump(mode="json")
    
    if DATABASE_AVAILABLE:
        try:
            project_id = db_save_project(project_data)
            return project_id
        except Exception as e:
            st.warning(f"DB save failed: {e}. Using JSON fallback.")
    
    # JSON fallback
    project_dir = DATA_DIR / project.project_id
    project_dir.mkdir(parents=True, exist_ok=True)
    project_file = project_dir / "project.json"
    with open(project_file, "w", encoding="utf-8") as f:
        json.dump(project_data, f, ensure_ascii=False, indent=2, default=str)
    return str(project_file)


@st.cache_data(ttl=300)  # Cache for 5 minutes
def load_project(project_id: str) -> Project:
    """Load project from database (or JSON fallback)"""
    if DATABASE_AVAILABLE:
        try:
            data = db_load_project(project_id)
            if data:
                return Project(**data)
        except Exception as e:
            st.warning(f"DB load failed: {e}. Using JSON fallback.")
    
    # JSON fallback
    project_file = DATA_DIR / project_id / "project.json"
    with open(project_file, "r", encoding="utf-8") as f:
        data = json.load(f)
    return Project(**data)


def delete_project(project_id: str) -> bool:
    """Delete project from database (or JSON fallback)"""
    if DATABASE_AVAILABLE:
        try:
            return db_delete_project(project_id)
        except Exception:
            pass
    
    # JSON fallback
    import shutil
    project_dir = DATA_DIR / project_id
    if project_dir.exists():
        shutil.rmtree(project_dir)
        return True
    return False


@st.cache_data(ttl=60)  # Cache for 1 minute (shorter for list view)
def list_projects() -> list[dict]:
    """List all projects from database (or JSON fallback)"""
    if DATABASE_AVAILABLE:
        try:
            return db_list_projects()
        except Exception as e:
            st.warning(f"DB list failed: {e}. Using JSON fallback.")
    
    # JSON fallback
    projects = []
    if DATA_DIR.exists():
        for project_dir in DATA_DIR.iterdir():
            if project_dir.is_dir():
                project_file = project_dir / "project.json"
                if project_file.exists():
                    try:
                        with open(project_file, "r", encoding="utf-8") as f:
                            data = json.load(f)
                            projects.append({
                                "id": data["project_id"],
                                "title": data["title"],
                                "status": data.get("status", "draft"),
                                "scenes": len(data.get("scenes", [])),
                                "created": data.get("created_at", ""),
                                "topic": data.get("topic", "")[:50]
                            })
                    except Exception:
                        pass
    return sorted(projects, key=lambda x: x["created"], reverse=True)


def export_all_prompts(project: Project) -> str:
    """Export all prompts to a single text file"""
    lines = [
        f"# VDO Content Export",
        f"# Project: {project.title}",
        f"# Topic: {project.topic}",
        f"# Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        f"# Scenes: {len(project.scenes)}",
        "",
        "=" * 60,
        ""
    ]
    
    for scene in project.scenes:
        lines.extend([
            f"## Scene {scene.order}",
            f"Time: {scene.time_range}",
            f"Duration: {scene.audio_duration:.1f}s",
            "",
            "### Thai Narration:",
            scene.narration_text,
            "",
            "### Veo 3 Prompt:",
            scene.veo_prompt,
            "",
            "-" * 40,
            ""
        ])
    
    return "\n".join(lines)


# ============ Main App ============
def main():
    init_session_state()
    apply_dark_mode()
    apply_mobile_styles()  # Enable responsive mobile layout
    
    # Sidebar
    with st.sidebar:
        st.title("🎬 VDO Content V2")
        st.caption(f"v{VERSION}")
        st.markdown("---")
        
        # --- Workflow Navigation ---
        st.subheader("📍 Workflow")
        
        # Workflow pages mapping
        workflow_map = {
            "🏠 Home": 0,
            "1️⃣ Ideation": 1,
            "2️⃣ Script": 2,
            "3️⃣ Audio Sync": 3,
            "4️⃣ Veo Prompts": 4,
            "5️⃣ Archive": 5
        }
        workflow_options = list(workflow_map.keys())
        
        # FIX: Remember last workflow page when viewing non-workflow pages
        # Determine current selection index based on page state
        if st.session_state.page in workflow_map.values():
            # User is on a workflow page - update last_workflow_page
            current_wf_index = list(workflow_map.values()).index(st.session_state.page)
            st.session_state.last_workflow_page = st.session_state.page
        else:
            # User is on a non-workflow page (e.g., Settings page 6, Database page)
            # Check if we have a remembered workflow page
            if "last_workflow_page" in st.session_state and st.session_state.last_workflow_page in workflow_map.values():
                current_wf_index = list(workflow_map.values()).index(st.session_state.last_workflow_page)
            else:
                # Default to Home if never visited a workflow page
                current_wf_index = 0
                st.session_state.last_workflow_page = 0
        
        # Use on_change callback pattern to avoid race conditions
        def _on_workflow_change():
            wf_key = st.session_state.wf_nav
            st.session_state.page = workflow_map[wf_key]
            st.session_state.last_workflow_page = workflow_map[wf_key]
            # Note: Streamlit auto-reruns after on_change, no manual rerun needed
            
        selected_wf = st.radio(
            "Workflow Steps",
            workflow_options,
            index=current_wf_index,
            label_visibility="collapsed",
            key="wf_nav",
            on_change=_on_workflow_change
        )
        # Note: Navigation happens via on_change callback, no need for manual check

        st.markdown("---")
        
        # --- Management Navigation ---
        st.subheader("🛠️ Management")
        
        if st.button("🗃️ Database & Tags", use_container_width=True, type="primary" if st.session_state.page == 6 else "secondary"):
            st.session_state.page = 6
            st.rerun()
            
        # Progress bar (Show only in workflow pages)
        if st.session_state.page <= 5:
            show_progress_bar()
        
        st.markdown("---")
        
        # Current project info
        if st.session_state.current_project:
            project = st.session_state.current_project
            st.success(f"📁 {project.title}")
            st.caption(f"Status: {project.status}")
            st.caption(f"Scenes: {len(project.scenes)}")
            
            if st.button("🏠 Back to Home", use_container_width=True):
                st.session_state.page = 0
                st.rerun()
        else:
            st.info("No project loaded")
        
        st.markdown("---")
        
        # Settings section (Collapsible)
        with st.expander("⚙️ System Config"):
            # API Key status (hidden, only show status)
            if st.session_state.api_key:
                st.success("🔑 API Key: Configured ✅")
            else:
                st.warning("🔑 API Key: Not found (configure in .env)")
            
            # Dark mode toggle
            dark_mode = st.toggle(
                "🌙 Dark Mode",
                value=st.session_state.dark_mode,
                key="dark_mode_toggle"
            )
            st.session_state.dark_mode = dark_mode
            
            # Auto-save toggle
            auto_save = st.toggle(
                "💾 Auto-save",
                value=st.session_state.auto_save,
                key="auto_save_toggle"
            )
            st.session_state.auto_save = auto_save
    
    # Main content based on page
    if st.session_state.page == 0:
        show_home_page()
    elif st.session_state.page == 1:
        show_ideation_page()
    elif st.session_state.page == 2:
        show_script_page()
    elif st.session_state.page == 3:
        show_audio_sync_page()
    elif st.session_state.page == 4:
        show_veo_prompts_page()
    elif st.session_state.page == 5:
        show_archive_page()
    elif st.session_state.page == 6:
        show_settings_page()


# ============ PAGE 0: HOME/DASHBOARD ============
def _goto_create_project():
    """Callback: Navigate to create new project (on_click pattern for mobile)"""
    st.session_state.current_project = None
    st.session_state.proposal = None
    st.session_state.script = ""
    st.session_state.audio_segments = []
    st.session_state.page = 1
    # Note: Do NOT call st.rerun() here - Streamlit auto-reruns after callback


def show_home_page():
    """Page 0: Dashboard with project list"""
    st.title("🏠 VDO Content Dashboard")
    
    st.markdown("---")
    
    # Mobile-first layout: Primary action button comes FIRST, outside columns
    # This ensures touch events work reliably on all mobile devices
    st.button(
        "➕ Create New Project", 
        type="primary", 
        use_container_width=True,
        on_click=_goto_create_project,
        key="create_project_btn"
    )
    
    # Metrics in columns (stacks on mobile via CSS)
    col1, col2 = st.columns(2)
    with col1:
        st.metric("📂 Total Projects", len(list_projects()))
    with col2:
        completed = len([p for p in list_projects() if p["status"] == "completed"])
        st.metric("✅ Completed", completed)
    
    st.markdown("---")
    
    # Project list
    st.subheader("📂 Recent Projects")
    
    projects = list_projects()
    
    if not projects:
        st.info("No projects yet. Click 'Create New Project' to begin")
        return
    
    # Display projects in cards
    for i, p in enumerate(projects):
        status_emoji = {
            "draft": "📝",
            "scripting": "✍️",
            "recording": "🎤",
            "editing": "🎬",
            "completed": "✅"
        }.get(p["status"], "📁")
        
        with st.container():
            col1, col2, col3, col4 = st.columns([3, 1, 1, 1])
            
            with col1:
                st.markdown(f"**{status_emoji} {p['title']}**")
                st.caption(f"{p['topic']}...")
                
                # Edit Title Feature
                with st.popover("✏️ Edit Title", help="Rename Project"):
                    new_title = st.text_input("New Title", value=p['title'], key=f"edit_title_{p['id']}")
                    if st.button("Save", key=f"save_title_{p['id']}"):
                        try:
                            # Load, Update, Save
                            proj_obj = load_project(p['id'])
                            proj_obj.title = new_title
                            save_project(proj_obj)
                            st.success("Saved!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error: {e}")
            
            with col2:
                st.caption(f"🎬 {p['scenes']} scenes")
            
            with col3:
                if st.button("📂 Open", key=f"open_{p['id']}"):
                    project = load_project(p['id'])
                    reset_session_for_project(project)  # ✅ Use new reset function
                    
                    # Go to appropriate page based on status
                    status_page = {
                        "draft": 1,
                        "scripting": 2,
                        "recording": 3,
                        "editing": 4,
                        "completed": 5
                    }
                    st.session_state.page = status_page.get(p['status'], 1)
                    st.rerun()
            
            with col4:
                if st.button("🗑️", key=f"delete_{p['id']}", help="Delete project"):
                    delete_project(p['id'])
                    st.rerun()
            
            st.markdown("---")


# ============ PAGE 1: IDEATION ============
def show_ideation_page():
    """Page 1: Topic input and story proposal"""
    show_back_button()
    
    st.title("1️⃣ Ideation - Story Planning")
    
    st.markdown("Enter topic → AI analyzes and creates story outline → Approve/Reject")
    
    st.markdown("---")
    
    # Input section with draft persistence
    col1, col2 = st.columns(2)
    
    with col1:
        title = st.text_input(
            "📌 Project Title",
            value=st.session_state.draft_title,
            placeholder="e.g., Weight Loss in 2 Months",
            key="ideation_title"
        )
        # Save to draft on change
        if title != st.session_state.draft_title:
            st.session_state.draft_title = title
        
        topic = st.text_area(
        "💡 Topic/Content to Create",
        value=st.session_state.draft_topic,
        height=100,
        placeholder="e.g., Role of AI in the future, How to make coffee, Phone review",
        key="ideation_topic"
    )
    if topic != st.session_state.draft_topic:
        st.session_state.draft_topic = topic
    
    # Content Type Selection (NEW)
    st.markdown("---")
    st.markdown("### 🎬 Content Type")
    
    # Load video profiles from database
    from core.database import get_video_profiles
    video_profiles = get_video_profiles()
    
    if video_profiles:
        # Initialize draft_content_type if not exists
        if "draft_content_type" not in st.session_state:
            st.session_state.draft_content_type = video_profiles[0]["id"]
        
        # Create dropdown with icons
        profile_options = {
            p["id"]: f"{p['icon']} {p['name_en']} - {p['description_en']}"
            for p in video_profiles
        }
        
        selected_profile_id = st.selectbox(
            "Select Content Type",
            options=list(profile_options.keys()),
            format_func=lambda x: profile_options[x],
            index=list(profile_options.keys()).index(st.session_state.draft_content_type) 
                if st.session_state.draft_content_type in profile_options 
                else 0,
            key="content_type_selector"
        )
        
        if selected_profile_id != st.session_state.draft_content_type:
            st.session_state.draft_content_type = selected_profile_id
            st.session_state.draft_video_profile = selected_profile_id
            st.rerun()
    
    st.markdown("---")
    
    with st.expander("⚙️ Advanced Settings", expanded=False):
        # Duration slider
        target_duration = st.slider(
            "⏱️ Target Duration (seconds)",
            30, 300,
            value=st.session_state.draft_duration,
            key="ideation_duration"
        )
        if target_duration != st.session_state.draft_duration:
            st.session_state.draft_duration = target_duration

        # Aspect ratio selection
        ratio = st.selectbox(
            "📐 Aspect Ratio",
            ["16:9 (Landscape - YouTube)", "9:16 (Portrait - TikTok/Reels)", "1:1 (Square - Instagram)", "21:9 (Ultrawide)"],
            index=0,
            key="ideation_ratio"
        )
        aspect_ratio = ratio.split()[0]  # "16:9"

    # Video Direction Styles will be selected in Step 2.5

    
    # Draft controls
    if st.session_state.draft_title or st.session_state.draft_topic:
        col_draft1, col_draft2 = st.columns([3, 1])
        with col_draft1:
            st.info("💾 Unsaved draft available")
        with col_draft2:
            if st.button("💾 Save Draft", help="Save draft to database"):
                if save_draft_to_db():
                    st.success("✅ Draft saved!")
                else:
                    st.warning("⚠️ Could not save draft")
    
    # Analyze button
    if st.button("🔍 Analyze Topic", type="primary", disabled=not topic):
        if not st.session_state.api_key:
            st.warning("Please enter DeepSeek API Key in Settings (sidebar)")
        else:
            with st.spinner("🤔 Analyzing..."):
                analyzer = StoryAnalyzer(api_key=st.session_state.api_key)
                
                feedback = ""
                if st.session_state.proposal and st.session_state.proposal.status == "rejected":
                    feedback = st.session_state.proposal.feedback
                
                proposal = analyzer.analyze_topic(
                    topic=topic,
                    style=selected_profile_id,
                    target_duration=target_duration,
                    previous_feedback=feedback
                )
                
                st.session_state.proposal = proposal
                st.session_state.proposal_version = proposal.version
    
    # Show proposal
    if st.session_state.proposal:
        proposal = st.session_state.proposal
        
        st.markdown("---")
        st.subheader(f"📋 Story Outline (Version {proposal.version}/{MAX_REVISIONS})")
        
        # Analysis
        st.markdown("**🔍 Analysis:**")
        st.write(proposal.analysis if proposal.analysis else "No data available")
        
        # Outline
        st.markdown("**📖 Outline:**")
        for i, item in enumerate(proposal.outline, 1):
            st.markdown(f"{i}. {item}")
        
        # Key points
        if proposal.key_points:
            st.markdown("**💡 Key Points:**")
            for point in proposal.key_points:
                st.markdown(f"- {point}")
        
        st.markdown("---")
        
        # Character Reference Validation (Consistency Check)
        MIN_CHARACTER_LENGTH = 40
        character_ref = st.session_state.draft_character
        if len(character_ref) < MIN_CHARACTER_LENGTH:
            st.warning(f"""⚠️ **Character Reference too short** ({len(character_ref)}/{MIN_CHARACTER_LENGTH} characters)
            
For consistent video across scenes, add more character details such as:
- Gender, age, ethnicity
- Clothing (color, style, type)
- Distinctive features (hairstyle, glasses)

**Example:** "Thai woman, early 30s, wearing pink casual t-shirt, short black hair, athletic build" """)
        
        # Approval buttons
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("✅ Approve", type="primary", use_container_width=True):
                proposal.status = "approved"
                
                # Map visual tag style labels back to Project enum values
                style_mapping = {
                    "Realistic": "realistic",
                    "3D Animation (3D)": "animated",
                    "Anime": "animated",
                    "Cinematic": "cinematic",
                    "Documentary": "documentary",
                    "Minimalist": "minimalist",
                    "Energetic": "energetic",
                    # Defaults for other styles
                    "Digital Art": "cinematic",
                    "Oil Painting": "cinematic",
                    "Watercolor": "cinematic",
                    "Cartoon": "animated",
                    "Comic Book": "animated",
                    "Sketch": "realistic",
                    "Vintage Film": "cinematic",
                    "Cyberpunk": "cinematic",
                    "Steampunk": "cinematic",
                    "Fantasy": "animated",
                    "Fashion": "realistic",
                    "Portrait": "realistic",
                    "Product": "realistic",
                    "Food": "realistic",
                    "Nature": "realistic",
                    "Street": "realistic",
                    "Abstract": "cinematic",
                    "Surreal": "cinematic",
                    "Noir": "cinematic",
                    "Pop Art": "cinematic"
                }
                
                # Convert style label to enum value
                mapped_style = style_mapping.get(selected_profile_id, "documentary")
                
                # Get optional fields with defaults
                visual_theme = st.session_state.get("draft_visual_theme", "")
                directors_note = st.session_state.get("draft_directors_note", "")
                
                # Create project
                project = Project(
                    title=title or f"Project-{datetime.now().strftime('%Y%m%d-%H%M')}",
                    topic=topic,
                    proposal=proposal,
                    default_style=mapped_style,
                    video_profile_id=st.session_state.get("draft_video_profile"),  # Master video profile
                    target_duration=target_duration,
                    character_reference=st.session_state.draft_character,
                    visual_theme=visual_theme,  # New
                    directors_note=directors_note,  # New
                    aspect_ratio=aspect_ratio, # New
                    status="scripting"
                )
                
                # Save to database and get the generated ID
                project_id = save_project(project)
                project.project_id = project_id  # Assign ID back to object
                st.session_state.current_project = project
                
                # Clear draft after successful project creation
                st.session_state.draft_title = ""
                st.session_state.draft_topic = ""
                st.session_state.draft_style = "documentary"
                st.session_state.draft_duration = 60
                st.session_state.draft_character = ""
                st.session_state.draft_video_profile = "educational"  # Reset to default
                st.session_state.proposal = None
                
                # CRITICAL FIX: Clear audio/scene state from previous session to prevent leakage
                if "audio_segments" in st.session_state:
                    del st.session_state.audio_segments
                if "uploaded_audio_path" in st.session_state:
                    del st.session_state.uploaded_audio_path
                
                clear_draft_from_db()  # Also clear from database
                
                st.success("✅ Approved! Go to Script →")
                st.session_state.page = 2
                st.rerun()
        
        with col2:
            if proposal.version < MAX_REVISIONS:
                reject_feedback = st.text_input(
                    "📝 Rejection Reason",
                    placeholder="Tell AI what changes you want...",
                    key="reject_feedback"
                )
                
                if st.button("❌ Reject & Revise", use_container_width=True, disabled=not reject_feedback):
                    proposal.status = "rejected"
                    proposal.feedback = reject_feedback
                    st.session_state.proposal = proposal
                    
                    st.warning(f"⏳ AI is rethinking... (Round {proposal.version + 1})")
                    st.rerun()
            else:
                st.error(f"❌ Maximum rejections reached ({MAX_REVISIONS}  times)")


# ============ PAGE 2: SCRIPT ============
def show_script_page():
    """Page 2: Generate and display script for AI Studio"""
    show_back_button()
    
    st.title("2️⃣ Script - Create Narration")
    
    if not st.session_state.current_project:
        st.warning("Please create and approve project in Ideation first")
        if st.button("← Go to Ideation"):
            st.session_state.page = 1
            st.rerun()
        return
    
    project = st.session_state.current_project
    
    # Project info with editable duration
    col_info1, col_info2 = st.columns([2, 2])
    
    with col_info1:
        st.markdown(f"**📁 Project:** {project.title}")
        st.caption(f"Topic: {project.topic[:50]}...")
    
    with col_info2:
        # Editable duration slider
        with st.popover("⏱️ Edit Duration", help="Change target duration for script"):
            new_duration = st.slider(
                "Target Duration (seconds)",
                30, 300,
                value=project.target_duration,
                key="edit_project_duration"
            )
            
            if new_duration != project.target_duration:
                if st.button("💾 Save Duration", type="primary"):
                    project.target_duration = new_duration
                    st.session_state.current_project = project
                    save_project(project)
                    st.success(f"✅ Duration updated to {new_duration}s!")
                    st.rerun()
            
            # Show current stats
            target_chars = new_duration * 10
            st.caption(f"📊 ~{target_chars} Thai characters | ~{new_duration // 8} scenes")
    
    st.markdown("---")
    
    # Generate script section
    col1, col2 = st.columns([3, 2])
    
    with col1:
        st.subheader("📝 Create Script")
        
        script_method = st.radio(
            "Script Method",
            ["🤖 AI Generate", "✏️ Write Manually"],
            horizontal=True
        )
        
        if script_method == "🤖 AI Generate":
            # AI Provider selector
            provider_col1, provider_col2 = st.columns([2, 3])
            with provider_col1:
                ai_provider = st.selectbox(
                    "Select AI",
                    ["gemini", "deepseek"],  # Changed default to Gemini
                    index=0,
                    format_func=lambda x: {"deepseek": "🤖 DeepSeek", "gemini": "✨ Gemini (Recommended)"}.get(x, x),
                    help="Gemini generates Thai better than DeepSeek"
                )
            
            # New: Writing Style Selector
            script_tone = st.selectbox(
                "🎭 Writing Style (Tone)",
                [
                    "Conversational (Casual)", 
                    "Professional (Formal)", 
                    "Storytelling (Narrative)", 
                    "Sales/Persuasive", 
                    "Educational (Informative)", 
                    "Humorous (Funny)", 
                    "Dramatic",
                    "Urgent (Exciting)"
                ],
                index=0,
                help="Select narration tone"
            )

            with provider_col2:
                st.warning("⚠️ **Note**: DeepSeek may produce garbled Thai! Recommend using **Gemini** instead")
            
            if st.button(f"🤖 Generate Script ({ai_provider})", type="primary"):
                try:
                    import time
                    start_t = time.time()
                    with st.spinner(f"Generating script with {ai_provider}..."):
                        generator = ScriptGenerator(api_key=st.session_state.api_key, provider=ai_provider)
                        
                        # Get story proposal from session state
                        proposal = st.session_state.proposal if hasattr(st.session_state, 'proposal') else None
                        
                        # Get visual theme from project
                        visual_theme = project.visual_theme if hasattr(project, 'visual_theme') else None
                        
                        # Append tone to style
                        combined_style = f"{project.default_style}, Tone: {script_tone}"
                        
                        script = generator.generate_script(
                            topic=project.topic,
                            style=combined_style,
                            target_duration=project.target_duration,
                            language="th",
                            story_proposal=proposal,
                            visual_context=visual_theme
                        )
                        st.session_state.script = script
                        
                        if DATABASE_AVAILABLE and hasattr(project, 'project_id') and project.project_id:
                            log_api_usage(
                                service=ai_provider.capitalize(),
                                operation="generate_script",
                                status="success",
                                project_id=project.project_id,
                                duration=time.time() - start_t,
                                meta={"topic_len": len(project.topic)}
                            )
                except Exception as e:
                    if DATABASE_AVAILABLE:
                        log_api_usage(service=ai_provider.capitalize(), operation="generate_script", status="failed", meta={"error": str(e)})
                    st.error(f"Error: {e}")
        
        # Script editor
        script = st.text_area(
            "Thai Narration",
            value=st.session_state.script,
            height=300,
            placeholder="Narration text will appear here..."
        )
        st.session_state.script = script
    
    with col2:
        st.subheader("⚙️ Settings")
        style = STYLE_PRESETS.get(project.default_style)
        if style:
            st.info(f"**Style:** {style.name}")
            st.caption(f"Voice Speed: {style.voice_speed}x")
            st.caption(f"Voice Style: {style.voice_style}")
    
    # Save and next
    st.markdown("---")
    
    if st.button("💾 Save & Go to Audio Sync →", type="primary", use_container_width=True):
        project.full_script = st.session_state.script
        project.status = "recording"
        
        # Generate style instructions for AI Studio using DeepSeek
        try:
            style_inst, script_text = generate_ai_studio_output(project, st.session_state.script)
            project.style_instructions = style_inst
        except Exception as e:
            # Fallback if generation fails
            st.warning(f"⚠️ Could not generate style instructions: {e}")
            project.style_instructions = "Read aloud in a warm and friendly tone."
        
        st.session_state.current_project = project
        save_project(project)
        
        st.success("Saved!")
        st.session_state.page = 3
        st.rerun()



# ============ PAGE 3: AUDIO SYNC ============
def show_audio_sync_page():
    """Page 3: Upload audio and analyze timing"""
    show_back_button()
    
    st.title("3️⃣ Audio Sync - Analyze Audio")
    
    if not st.session_state.current_project:
        st.warning("Please create a project first")
        return
    
    project = st.session_state.current_project
    
    st.markdown(f"**📁 Project:** {project.title}")
    st.markdown("---")
    
    # ===== RESTORE AUDIO SEGMENTS FROM PROJECT ON PAGE LOAD =====
    if "audio_segments" not in st.session_state or not st.session_state.audio_segments:
        if hasattr(project, 'audio_segments') and project.audio_segments:
            st.session_state.audio_segments = project.audio_segments
            st.info("📂 Load segments from existing project")
    
    # ===== RESTORE AUDIO PATH FROM PROJECT =====
    if "uploaded_audio_path" not in st.session_state or not st.session_state.uploaded_audio_path:
        if hasattr(project, 'audio_path') and project.audio_path and os.path.exists(project.audio_path):
            st.session_state.uploaded_audio_path = project.audio_path
    
    # ===== SIMPLIFIED WORKFLOW: AI STUDIO + UPLOAD =====
    st.subheader("🎙️ Generate Voice")
    
    # Step 1: Show Copy Format for AI Studio
    st.info("📍 **Steps:** Copy data below → Paste in AI Studio → Generate voice → Upload back")
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        # Display Style Instructions (from script page)
        st.markdown("**Style instructions** 🎭")
        
        # New: Voice Tone Selector
        voice_tone = st.selectbox(
            "Adjust Voice Tone",
            [
                "Default",
                "Warm & Friendly",
                "Professional & Clear", 
                "Excited & Energetic",
                "Calm & Soothing",
                "Serious & Authoritative",
                "Bright & Cheerful"
            ],
            index=0,
            key="voice_tone_selector"
        )
        
        # Get style from project or use default
        base_style = project.style_instructions if hasattr(project, 'style_instructions') and project.style_instructions else "Read aloud in a warm and friendly tone."
        
        # Modify style based on selection
        if voice_tone != "Default":
            tone_only = voice_tone.split("(")[0].strip()
            final_style = f"Tone: {tone_only}. {base_style}"
        else:
            final_style = base_style
        
        # Use dynamic key to force update when voice_tone changes
        style_box = st.text_area(
            "Copy this to AI Studio:",
            value=final_style,
            height=80,
            key=f"ai_studio_style_{voice_tone.replace(' ', '_')}",
            help="Style instructions for AI Studio"
        )
        
        st.markdown("---")
        
        # Display Text (full script)
        st.markdown("**Text** 📝")
        
        if project.full_script:
            text_box = st.text_area(
                "Copy script to AI Studio:",
                value=project.full_script,
                height=200,
                key="ai_studio_text",
                help="Script from Script page"
            )
            
            # Copy button helper
            st.caption(f"📊 {len(project.full_script)} characters | Select text and press Ctrl+C to copy")
        else:
            st.warning("⚠️ No script yet. Please go back to Script page first.")
    
    with col2:
        st.link_button(
            "🌟 Open AI Studio",
            "https://aistudio.google.com/generate-speech",
            type="primary",
            use_container_width=True
        )
        
        st.markdown("---")
        
        st.info("""
        **How to use:**
        1. Copy Style
        2. Copy Text
        3. Open AI Studio
        4. Paste both parts
        5. Select voice
        6. Generate
        7. Download
        """)
    
    st.markdown("---")
    
    # ===== SHOW EXISTING AUDIO IF AVAILABLE =====
    if st.session_state.get("uploaded_audio_path") and os.path.exists(st.session_state.uploaded_audio_path):
        st.success(f"✅ Audio file in project: {Path(st.session_state.uploaded_audio_path).name}")
        st.audio(st.session_state.uploaded_audio_path)
        
        if st.button("🗑️ Delete Audio File", type="secondary", help="Delete current audio and reset analysis"):
            # Clear file from project
            project.audio_path = None
            
            # Clear from session state
            if "uploaded_audio_path" in st.session_state:
                del st.session_state.uploaded_audio_path
            
            # Clear analysis results
            if "audio_segments" in st.session_state:
                del st.session_state.audio_segments
                
            project.audio_duration = 0
            
            auto_save_project()
            st.rerun()
    
    # Step 2: Upload Audio File
    st.markdown("**2️⃣ Upload generated audio file:**")
    
    uploaded_audio = st.file_uploader(
        "Select audio file (MP3, WAV, M4A)",
        type=["mp3", "wav", "m4a", "ogg", "flac"],
        key="audio_upload",
        help="Upload file downloaded from AI Studio"
    )
    
    if uploaded_audio:
        st.success(f"✅ Uploaded: {uploaded_audio.name} ({uploaded_audio.size / 1024:.1f} KB)")
        
        # ===== SAVE TO PROJECT FOLDER (PERSISTENT) =====
        project_dir = DATA_DIR / project.project_id
        project_dir.mkdir(parents=True, exist_ok=True)
        
        audio_filename = f"audio_{uploaded_audio.name}"
        permanent_path = project_dir / audio_filename
        
        with open(permanent_path, "wb") as f:
            f.write(uploaded_audio.getvalue())
        
        uploaded_path = str(permanent_path)
        
        # Store path in session state AND project
        st.session_state.uploaded_audio_path = uploaded_path
        project.audio_path = uploaded_path
        auto_save_project()
    
    st.markdown("---")
    
    # ===== ANALYSIS TOOLS =====
    if st.session_state.get("uploaded_audio_path") and os.path.exists(st.session_state.uploaded_audio_path):
        tmp_path = st.session_state.uploaded_audio_path
        
        st.markdown("---")
        
        # Analysis buttons - Audio-First Workflow
        st.markdown("### 🛠️ Select Analysis Method")
        
        # Priority 1: AI Sync (The best way)
        with st.container():
            st.markdown("""
            <div style='background-color: rgba(233, 69, 96, 0.1); padding: 20px; border-radius: 10px; border-left: 5px solid #e94560;'>
                <h4>🚀 Recommended: AI Auto-Sync & Transcription</h4>
                <p>System will listen and transcribe audio with precise timing - most accurate for Veo 3</p>
            </div>
            """, unsafe_allow_html=True)
            
            if st.button("🎙️ Start AI Transcription (Whisper)", type="primary", use_container_width=True):
                if not TRANSCRIPTION_AVAILABLE:
                    st.error("❌ faster-whisper not installed")
                    st.code("pip install faster-whisper")
                else:
                    try:
                        with st.spinner("🔄 Loading AI model (first time may take a while)..."):
                            transcriber = AudioTranscriber(model_size="base", device="cpu", compute_type="int8")
                        
                        with st.spinner("🎧 Listening to audio and splitting scenes (≤8s)..."):
                            result = transcriber.transcribe_with_summary(tmp_path, language="th")
                        
                        # Convert to AudioSegment for compatibility
                        segments = []
                        for i, seg in enumerate(result["segments"], 1):
                            segments.append(AudioSegment(
                                order=i,
                                start_time=seg.start,
                                end_time=seg.end,
                                duration=round(seg.end - seg.start, 2),
                                text_content=seg.text
                            ))
                        
                        st.session_state.audio_segments = segments
                        project.audio_duration = result["total_duration"]
                        project.audio_path = tmp_path # Use the path from session state
                        
                        # Always update script with the reality of what was said
                        project.full_script = result["full_text"]
                        
                        auto_save_project()
                        st.success(f"✅ Success! Split into {len(segments)} scenes (total {result['total_duration']:.1f}s)")
                        st.rerun()
                        
                    except Exception as e:
                        st.error(f"❌ Error: {str(e)}")
    
    # Show segments with warnings
    if "audio_segments" in st.session_state and st.session_state.audio_segments:
        st.markdown("---")
        
        # Header with Clear Button
        col_head, col_clear = st.columns([3, 1])
        with col_head:
            st.subheader("📊 Review Scenes & Timing")
        with col_clear:
             if st.button("🗑️ Clear Analysis Results", use_container_width=True, help="Clear all scene splits (keeps audio file)"):
                 # Clear segments
                 st.session_state.audio_segments = []
                 project.audio_segments = []
                 
                 auto_save_project()
                 st.rerun()
        
        segments = st.session_state.audio_segments
        
        # Check for any segments > 8s
        over_limit = [s for s in segments if s.duration > 8.05] # small buffer
        if over_limit:
            st.warning(f"⚠️ Found {len(over_limit)} scenes exceeding 8 seconds (Veo 3 may cut your clips!)")
        
        for i, seg in enumerate(segments):
            status_color = "🔴" if seg.duration > 8.05 else "🟢"
            with st.expander(f"{status_color} Scene {seg.order}: {seg.time_range} ({seg.duration:.1f}s)", expanded=(i < 3)):
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    new_text = st.text_area("Text heard by AI", value=seg.text_content, key=f"seg_text_{i}", height=80)
                    if new_text != seg.text_content:
                        seg.text_content = new_text
                        seg.is_edited = True
                
                with col2:
                    st.markdown(f"**Duration:** {seg.duration:.1f}s")
                    if seg.duration > 8.0:
                        st.error("Exceeds 8s!")
                    
                    new_start = st.number_input("Start", value=seg.start_time, key=f"seg_start_{i}", step=0.1)
                    new_end = st.number_input("End", value=seg.end_time, key=f"seg_end_{i}", step=0.1)
                    if new_start != seg.start_time or new_end != seg.end_time:
                        seg.start_time = new_start
                        seg.end_time = new_end
                        seg.duration = round(new_end - new_start, 2)
                        seg.is_edited = True
        
        st.session_state.audio_segments = segments
        
        # Next button
        st.markdown("---")
        
        # Advanced Options: QA Toggle
        with st.expander("⚙️ Advanced Options", expanded=False):
            enable_qa = st.checkbox(
                "🔍 Enable AI Quality Review",
                value=False,  # Default OFF for maximum consistency
                help="AI will review and improve prompts (may alter results, disable for strict accuracy)"
            )
            if enable_qa:
                st.info("ℹ️ QA enabled - Prompts will be refined by AI (may affect character consistency)")
            
            st.markdown("---")
            
            # Direction Style Selection (Video Editing Style)
            st.markdown("🎬 **Video Direction Style**")
            st.caption("เลือกสไตล์การตัดต่อและทิศทางวิดีโอ")
            
            try:
                from core.direction_styles import DIRECTION_STYLES, get_direction_style
                
                # Build options for direction style
                direction_options = ["(ไม่เลือก / Default)"]
                direction_values = [None]
                
                for style_id, style in DIRECTION_STYLES.items():
                    direction_options.append(f"{style.icon} {style.name}")
                    direction_values.append(style_id)
                
                # Get current value from project
                current_direction = project.direction_style
                try:
                    current_idx = direction_values.index(current_direction) if current_direction else 0
                except ValueError:
                    current_idx = 0
                
                selected_direction = st.selectbox(
                    "Direction Style",
                    options=direction_options,
                    index=current_idx,
                    key="direction_style_select",
                    help="เลือกสไตล์การตัดต่อ เช่น Match Cut, Stop Motion"
                )
                
                # Update project.direction_style based on selection
                selected_idx = direction_options.index(selected_direction)
                new_direction_style = direction_values[selected_idx]
                
                if new_direction_style != project.direction_style:
                    project.direction_style = new_direction_style
                
                # Show description if selected
                if new_direction_style:
                    style_obj = get_direction_style(new_direction_style)
                    if style_obj:
                        st.info(f"📋 {style_obj.description_th}")
                        
            except ImportError as e:
                st.warning(f"⚠️ Direction Styles not available: {e}")
            
            st.markdown("---")
            
            # NEW: Prompt Style Selection (Content Approach)
            st.markdown("🎨 **Prompt Style (Content Approach)**")
            st.caption("เลือกแนวทางการสร้าง Prompt ตามประเภทเนื้อหา")
            
            # Import prompt styles
            try:
                from core.prompt_styles import (
                    get_all_categories, 
                    get_category_display_name, 
                    get_styles_by_category, 
                    get_style_by_id,
                    get_style_summary
                )
                
                # Initialize prompt_style_config in session if not exists
                if "prompt_style_config" not in st.session_state:
                    st.session_state.prompt_style_config = {}
                
                # Create 2x2 grid for style selectors
                col_s1, col_s2 = st.columns(2)
                
                categories = get_all_categories()
                
                for i, category in enumerate(categories):
                    icon, name_th, name_en = get_category_display_name(category)
                    styles = get_styles_by_category(category)
                    
                    # Build options
                    options = [None] + [s.style_id for s in styles]
                    
                    def format_option(style_id, styles=styles):
                        if style_id is None:
                            return "— ไม่เลือก (Default) —"
                        for s in styles:
                            if s.style_id == style_id:
                                return f"{s.icon} {s.name_th}"
                        return style_id
                    
                    # Get current value
                    current_value = st.session_state.prompt_style_config.get(category)
                    current_index = 0
                    if current_value in options:
                        current_index = options.index(current_value)
                    
                    # Place in appropriate column
                    with col_s1 if i < 2 else col_s2:
                        selected = st.selectbox(
                            f"{icon} {name_th}",
                            options=options,
                            index=current_index,
                            format_func=format_option,
                            key=f"prompt_style_{category}",
                            help=name_en
                        )
                        
                        # Update session state
                        if selected:
                            st.session_state.prompt_style_config[category] = selected
                        elif category in st.session_state.prompt_style_config:
                            del st.session_state.prompt_style_config[category]
                
                # Show summary of selected styles
                if st.session_state.prompt_style_config:
                    summary = get_style_summary(st.session_state.prompt_style_config, lang="th")
                    st.success(f"✅ เลือกแล้ว: {summary}")
                    
            except ImportError as e:
                st.warning(f"⚠️ Prompt Styles module not available: {e}")
            
            st.markdown("---")
            st.markdown("🎥 **Video Techniques (Filming)**")
            video_techniques = st.multiselect(
                "Select special techniques (will be mixed into prompts)",
                [
                    "Stop Motion", 
                    "Hyperlapse", 
                    "Slow Motion", 
                    "Drone Shot", 
                    "Handheld", 
                    "Cinematic", 
                    "Match Cut", 
                    "Macro (Extreme Close-up)",
                    "Minimalist",
                    "Vintage Film"
                ],
                default=[],
                help="These techniques will be added to every scene's prompt"
            )
        
        # Store QA setting in session for button handler
        st.session_state.prompt_qa_enabled = enable_qa if 'enable_qa' in dir() else False
        
        if st.button("✅ Confirm & Generate Veo Prompts →", type="primary", use_container_width=True):
            # CRITICAL FIX: Load project and segments from session state
            # These variables must be loaded INSIDE the button handler
            project = st.session_state.current_project
            segments = st.session_state.audio_segments
            
            try:
                # Get QA setting from session state
                enable_qa = st.session_state.get("prompt_qa_enabled", True)
                
                # Create scenes from segments with QA toggle
                prompt_gen = VeoPromptGenerator(
                    character_reference=project.character_reference,
                    enable_qa=enable_qa
                )
                
                scenes = []
                for seg in segments:
                    scene = Scene(
                        order=seg.order,
                        start_time=seg.start_time,
                        end_time=seg.end_time,
                        narration_text=seg.text_content,
                        visual_style=project.default_style,
                        subject_description=project.character_reference,
                        audio_synced=True
                    )
                    scene.estimated_duration = seg.duration
                    scenes.append(scene)
                
                # Generate prompts with Director's Vision settings
                with st.spinner("🎬 Generating Veo Prompts..."):
                    # Prepare Director's Note with Techniques
                    base_note = project.directors_note or ""
                    tech_str = ", ".join(video_techniques)
                    final_note = f"{base_note}. Techniques: {tech_str}" if video_techniques else base_note
                    
                    # Get prompt style config from session state
                    prompt_style_config = st.session_state.get("prompt_style_config", {})
                    
                    # Pass visual settings to ensure prompts reflect user's Director's Vision
                    project_context = {
                        "visual_theme": project.visual_theme or "",
                        "directors_note": final_note,
                        "aspect_ratio": project.aspect_ratio or "16:9",
                        "direction_style": project.direction_style,  # Video direction style (Match Cut, etc.)
                        "prompt_style_config": prompt_style_config if prompt_style_config else None  # Content approach styles
                    }
                    scenes = prompt_gen.generate_all_prompts(
                        scenes, 
                        project.character_reference,
                        project_context
                    )
                
                project.scenes = scenes
                project.audio_segments = segments
                project.status = "editing"
                
                st.session_state.current_project = project
                save_project(project)
                
                st.success(f"✅ Generated {len(scenes)} scenes!")
                st.session_state.page = 4
                st.rerun()
                
            except Exception as e:
                st.error(f"❌ Error occurred: {str(e)}")
                import traceback
                st.code(traceback.format_exc())


# ============ PAGE 4: VEO PROMPTS ============
def show_veo_prompts_page():
    """Page 4: Display Veo 3 prompts for each scene"""
    show_back_button()
    
    st.title("4️⃣ Veo Prompts - Scene Prompts")
    
    if not st.session_state.current_project:
        st.warning("Please create a project first")
        return
    
    project = st.session_state.current_project
    
    # Load scenes from project if not in session (data isolation fix)
    if not project.scenes:
        st.warning("No scenes yet. Please upload audio and analyze first")
        return
    
    st.markdown(f"**📁 Project:** {project.title}")
    st.markdown(f"**🎬 Total Scenes:** {len(project.scenes)} | **⏱️ Duration:** {project.total_duration:.1f}s")
    
    st.markdown("---")
    
    # Batch actions - Enhanced with ZIP export
    st.subheader("📦 Export & Actions")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        # ZIP Export (NEW)
        if EXPORTER_AVAILABLE:
            exporter = ProjectExporter()
            zip_data = exporter.export_full_package(project)
            safe_title = "".join(c for c in project.title if c.isalnum() or c in (' ', '-', '_')).strip().replace(' ', '_')
            st.download_button(
                "📦 Export ZIP Package",
                data=zip_data,
                file_name=f"{safe_title}_VDO_Content.zip",
                mime="application/zip",
                use_container_width=True,
                type="primary",
                help="Download complete package: prompts, script, scenes, metadata"
            )
        else:
            st.button("📦 Export ZIP (N/A)", disabled=True, use_container_width=True)
    
    with col2:
        # Enhanced prompts text export
        if EXPORTER_AVAILABLE:
            exporter = ProjectExporter()
            prompts_text = exporter.export_all_prompts_text(project)
        else:
            prompts_text = export_all_prompts(project)
        
        st.download_button(
            "📄 Download Prompts",
            data=prompts_text,
            file_name=f"{project.title}_prompts.txt",
            mime="text/plain",
            use_container_width=True,
            help="Download all Veo 3 prompts as text file"
        )
    
    with col3:
        # Copy All Prompts - Enhanced
        if st.button("📋 Copy All Prompts", use_container_width=True, help="Copy all prompts to clipboard"):
            if EXPORTER_AVAILABLE:
                exporter = ProjectExporter()
                all_prompts = exporter.export_all_prompts_text(project)
            else:
                all_prompts = "\n\n---\n\n".join([
                    f"Scene {s.order}:\n{s.veo_prompt}" 
                    for s in project.scenes
                ])
            copy_to_clipboard(all_prompts, "all_prompts")
    
    with col4:
        completed = sum(1 for s in project.scenes if s.video_generated)
        st.metric("Progress", f"{completed}/{len(project.scenes)}")
    
    st.markdown("---")
    
    # --- Draft Preview (New) ---
    st.subheader("🎞️ Draft Video Preview")
    st.caption("View overview of audio and scene duration (Storyboard Animation)")
    
    # Music Selection
    music_dir = Path("data/music")
    music_files = []
    if music_dir.exists():
        for f in music_dir.glob("**/*.mp3"):
            music_files.append(f)
            
    selected_music = None
    if music_files:
        music_options = ["(No Music)"] + [f.name for f in music_files]
        music_choice = st.selectbox("🎵 Background Music", music_options)
        
        if music_choice != "(No Music)":
            # Find full path
            for f in music_files:
                if f.name == music_choice:
                    selected_music = str(f)
                    break
    
    col_prev1, col_prev2 = st.columns([1, 2])
    with col_prev1:
        if st.button("▶️ Generate Preview Video", type="primary", use_container_width=True):
            if not RENDERER_AVAILABLE:
                st.error("Renderer not available")
            else:
                try:
                    with st.spinner("🎞️ Rendering draft video (FFmpeg)..."):
                        renderer = VideoRenderer()
                        vid_path = renderer.render_draft(project, music_path=selected_music)
                        st.session_state.preview_video = vid_path
                        st.success("✅ Render Complete!")
                except Exception as e:
                    st.error(f"Render failed: {e}")
                    
    with col_prev2:
        if "preview_video" in st.session_state and st.session_state.preview_video:
            if os.path.exists(st.session_state.preview_video):
                st.video(st.session_state.preview_video)
            else:
                st.warning("File not found. Please render again.")

    st.markdown("---")
    st.markdown("""
    **📌 How to Use:**
    1. Copy each scene prompt
    2. to Veo 3 → Paste → Generate
    3. Download video and save
    4. Repeat for all scenes
    5. Combine in CapCut
    """)
    
    st.markdown("---")
    
    # Show scenes
    for scene in project.scenes:
        status_icon = "✅" if scene.video_generated else "⬜"
        
        with st.expander(
            f"{status_icon} Scene {scene.order}: [{scene.time_range}] - {scene.narration_text[:40]}...",
            expanded=not scene.video_generated
        ):
            tab_prompt, tab_stock = st.tabs(["📝 Veo Prompt (AI Gen)", "🎞️ Stock Video (Free)"])
            
            with tab_prompt:
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    st.markdown("**�� Narration (Thai):**")
                    st.info(scene.narration_text)
                    
                    st.markdown("**🎬 Veo 3 Prompt (English):**")
                    st.code(scene.veo_prompt, language="text")
                    
                    # Copy button directly below (no nested columns to avoid z-index issues)
                    if st.button("📋 คัดลอก Prompt", key=f"copy_scene_{scene.order}", help="Copy prompt to clipboard", use_container_width=True):
                        copy_to_clipboard(scene.veo_prompt, f"scene_{scene.order}")
                
                with col2:
                    st.markdown("**⏱️ Timing:**")
                    st.caption(f"Start: {scene.start_time:.1f}s")
                    st.caption(f"End: {scene.end_time:.1f}s")
                    st.caption(f"Duration: {scene.audio_duration:.1f}s")
                    
                    st.markdown("---")
                    
                    scene.video_generated = st.checkbox(
                        "✅ Generated",
                        value=scene.video_generated,
                        key=f"vid_gen_{scene.scene_id}"
                    )

            with tab_stock:
                if not STOCK_FINDER_AVAILABLE:
                    st.warning("⚠️ Stock Finder module not loaded.")
                else:
                    if scene.stock_video_url:
                        st.success("✅ Selected Stock Video:")
                        st.video(scene.stock_video_url)
                        if st.button("❌ Remove Stock Video", key=f"rm_stock_{scene.scene_id}"):
                            scene.stock_video_url = ""
                            st.rerun()
                    else:
                        st.markdown("Search free videos from **Pexels** instead of AI generation")
                        
                        # Extract simple keywords from prompt or narration
                        # (Ideally we'd use AI to extract keywords, but for now simple split)
                        default_query = scene.veo_prompt.split(',')[0] if scene.veo_prompt else "business"
                        
                        col_s1, col_s2 = st.columns([3, 1])
                        with col_s1:
                            query = st.text_input("🔍 Keywords (English)", value=default_query, key=f"q_{scene.scene_id}")
                        with col_s2:
                            st.markdown("<br>", unsafe_allow_html=True)
                            search_btn = st.button("Search", key=f"s_btn_{scene.scene_id}")
                        
                        if search_btn or query:
                            # Pexels API Key
                            pexels_key = os.getenv("PEXELS_API_KEY", "")
                            if not pexels_key:
                                st.error("❌ PEXELS_API_KEY not found in .env")
                            else:
                                finder = StockVideoFinder(api_key=pexels_key)
                                with st.spinner("Searching Pexels..."):
                                    results = finder.search_video(query, orientation="landscape") # TODO: use project.aspect_ratio logic
                                
                                if not results:
                                    st.info("No videos found.")
                                else:
                                    # Show results in grid
                                    cols = st.columns(3)
                                    for i, vid in enumerate(results):
                                        with cols[i % 3]:
                                            st.image(vid["thumbnail"], use_container_width=True)
                                            st.caption(f"👤 {vid['photographer']} | ⏱️ {vid['duration']}s")
                                            if st.button("✅ Select", key=f"sel_{scene.scene_id}_{vid['id']}"):
                                                scene.stock_video_url = vid["url"]
                                                scene.video_generated = True # Mark as done
                                                st.success("Selected!")
                                                st.rerun()
    
    # Progress
    completed = sum(1 for s in project.scenes if s.video_generated)
    st.progress(completed / len(project.scenes) if project.scenes else 0)
    st.caption(f"Progress: {completed}/{len(project.scenes)} scenes")
    
    # Save and next
    st.markdown("---")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("💾 Save", use_container_width=True):
            save_project(project)
            st.success("Saved!")
    
    with col2:
        if st.button("➡️ Go to Archive", type="primary", use_container_width=True):
            save_project(project)
            st.session_state.page = 5
            st.rerun()


# ============ PAGE 6: SETTINGS ============
def show_settings_page():
    """Page 6: Manage Database (Tags & Presets)"""
    st.title("⚙️ Settings & Database")
    
    if not DATABASE_AVAILABLE:
        st.error("❌ Database not available")
        return

    tab1, tab2, tab3 = st.tabs(["🏷️ Visual Library", "💾 Style Presets (Saved Styles)", "🎬 Master Video Profiles"])
    
    # --- Tab 1: Visual Tags Manager ---
    with tab1:
        st.caption("Manage options that appear in Visual Builder page (editable like Excel)")
        
        # 1. Fetch all data
        all_tags = get_all_tags_raw()
        
        # 2. Category Filter
        categories = sorted(list(set(t["category"] for t in all_tags)))
        # Map nice names
        cat_map = {
            "mood": "🎨 Mood",
            "lighting": "💡 Lighting (Lighting)",
            "camera_angle": "🎥 Camera Angle",
            "movement": "🎬 Movement",
            "shot_size": "📐 Shot Size",
            "style": "🖌️ Style"
        }
        
        selected_cat = st.radio(
            "Category",
            categories,
            format_func=lambda x: cat_map.get(x, x.title()),
            horizontal=True
        )
        
        # 3. Prepare Data for Editor
        current_tags = [t for t in all_tags if t["category"] == selected_cat]
        
        # Convert to list of dicts for editor
        editor_data = [
            {"id": t["id"], "Label (Display Name)": t["label"], "Prompt Value (AI Input)": t["value"]}
            for t in current_tags
        ]
        
        # 4. Data Editor
        edited_df = st.data_editor(
            editor_data,
            num_rows="dynamic",
            use_container_width=True,
            key=f"editor_{selected_cat}",
            hide_index=True,
            column_config={
                "id": None, # Hide ID
                "Label (Display Name)": st.column_config.TextColumn(required=True),
                "Prompt Value (AI Input)": st.column_config.TextColumn(required=True)
            }
        )
        
        # 5. Save Changes Logic
        if st.button(f"💾 Save Changes to '{selected_cat}'", type="primary"):
            # This is a simplified sync logic. 
            # In a real app with concurrent users, we'd handle diffs more carefully.
            # Here we just delete old for this cat and re-insert active ones.
            
            try:
                # 1. Delete existing for this category
                # (We do this one by one to use existing logic, or could allow bulk delete in DB)
                for old in current_tags:
                    delete_visual_tag(selected_cat, old["label"])
                
                # 2. Add new/updated
                for row in edited_df:
                    label = row["Label (Display Name)"]
                    val = row["Prompt Value (AI Input)"]
                    if label and val:
                        add_visual_tag(selected_cat, label, val)
                
                st.success("✅ Data saved successfully!")
                st.rerun()
            except Exception as e:
                st.error(f"Error saving: {e}")

    # --- Tab 2: Style Presets Manager ---
    with tab2:
        st.caption("Manage saved visual style presets")
        
        profiles = list_style_profiles()
        
        if not profiles:
            st.info("No presets yet (create in Ideation page)")
        else:
            # Grid Layout
            cols = st.columns(3)
            for i, p in enumerate(profiles):
                with cols[i % 3]:
                    with st.container(border=True):
                        st.markdown(f"### 📁 {p['name']}")
                        
                        # Show summary chips
                        conf = p["config"]
                        moods = conf.get("mood", [])
                        style = conf.get("style", "")
                        
                        st.caption(f"🎨 {style}")
                        if moods:
                            st.caption(f"✨ {', '.join(moods[:2])}")
                        
                        # Actions
                        col_a, col_b = st.columns(2)
                        with col_a:
                            with st.popover("🔍 View Details"):
                                st.json(conf)
                        with col_b:
                            if st.button("🗑️", key=f"del_p_{p['id']}", help="Delete Preset"):
                                if delete_style_profile(p["id"]):
                                    st.toast("Deleted!")
                                    st.rerun()
                                    
    # --- Tab 3: Master Video Profiles ---
    with tab3:
        st.caption("Manage Master Profiles used as templates for projects (Admin)")
        
        try:
            from core.database import update_video_profile
            
            v_profiles = list_video_profiles()
            
            for vp in v_profiles:
                with st.expander(f"{vp['icon']} {vp['name_en']} ({vp['name_th']})", expanded=False):
                    col1, col2 = st.columns([1, 2])
                    
                    with col1:
                        st.info("ℹ️ Profile Info")
                        new_name_th = st.text_input("Thai Name", vp['name_th'], key=f"vp_nth_{vp['id']}")
                        new_name_en = st.text_input("English Name", vp['name_en'], key=f"vp_nen_{vp['id']}")
                        new_desc_th = st.text_area("Description (Thai)", vp['description_th'], key=f"vp_dth_{vp['id']}")
                        
                    with col2:
                        st.warning("⚠️ Configuration (JSON)")
                        st.caption("Edit internal settings (e.g., Prompt Suffix, Voice Speed)")
                        
                        # JSON Editor for Config
                        import json
                        config_str = json.dumps(vp['config'], indent=2, ensure_ascii=False)
                        new_config_str = st.text_area("Config JSON", config_str, height=300, key=f"vp_conf_{vp['id']}")
                        
                    if st.button(f"💾 Save {vp['name_en']}", key=f"save_vp_{vp['id']}"):
                        try:
                            new_config = json.loads(new_config_str)
                            
                            update_video_profile(
                                vp['id'],
                                new_config,
                                name_th=new_name_th,
                                name_en=new_name_en,
                                description_th=new_desc_th
                            )
                            st.success(f"✅ Save {vp['name_en']} Done!")
                            st.rerun()
                        except json.JSONDecodeError:
                            st.error("❌ Invalid JSON format in Config")
                        except Exception as e:
                            st.error(f"❌ Error: {e}")
                            
        except ImportError:
            st.error("❌ core.database.update_video_profile not found")

def show_archive_page():
    """Page 5: Upload final video and get Drive link"""
    show_back_button()
    
    st.title("5️⃣ Archive - Upload & Save")
    
    if not st.session_state.current_project:
        st.warning("Please create a project first")
        return
    
    project = st.session_state.current_project
    
    st.markdown(f"**📁 Project:** {project.title}")
    st.markdown("---")
    
    st.markdown("""
    **📌 Final Steps:**
    1. Combine all scene clips in CapCut
    2. Export as video file
    3. Upload to Google Drive via link below
    """)
    
    st.markdown("---")
    
    # Project summary
    st.subheader("📊 Project Summary")
    
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Scenes", len(project.scenes))
    col2.metric("Total Duration", f"{project.total_duration:.1f}s")
    col3.metric("Completed", f"{project.completed_scenes}/{len(project.scenes)}")
    
    st.markdown("---")
    
    # Export Production Kit (NEW)
    st.subheader("📦 Export Production Kit")
    st.info("Export all files for editing (audio file + timing card images)")
    
    if st.button("📦 Create Production Kit", type="primary", use_container_width=True):
        if not EXPORTER_AVAILABLE:
            st.error("❌ core.exporter module not loaded. Please check dependencies (Pillow).")
        else:
            try:
                with st.spinner("📦 Generating Scene Cards & Packaging..."):
                    exporter = ProjectExporter(output_dir="data/exports")
                    export_path = exporter.export_project(project)
                    
                    # Zip it
                    shutil.make_archive(export_path, 'zip', export_path)
                    zip_path = f"{export_path}.zip"
                    
                    st.success(f"✅ Created Production Kit: {Path(zip_path).name}")
                    
                    # Download button
                    with open(zip_path, "rb") as f:
                        st.download_button(
                            "⬇️ Download Kit (.zip)",
                            data=f,
                            file_name=Path(zip_path).name,
                            mime="application/zip",
                            use_container_width=True
                        )
            except Exception as e:
                st.error(f"Export failed: {e}")
                if "Pillow" in str(e) or "PIL" in str(e):
                    st.warning("💡 Tip: Try installing Pillow: `pip install Pillow`")


    st.markdown("---")
    
    # ===== GOOGLE DRIVE UPLOAD SECTION (NEW) =====
    st.subheader("📤 Upload Video to Google Drive")
    
    if not DRIVE_UPLOAD_AVAILABLE:
        st.warning("⚠️ Google Drive upload not available")
        st.info("install with: `pip install google-api-python-client google-auth`")
    else:
        # Check configuration
        uploader = get_drive_uploader()
        
        if not uploader.is_configured:
            st.error("❌ Google Drive not configured")
            st.markdown("""
            **Setup Instructions:**
            1. Create Service Account in Google Cloud Console
            2. Download JSON key file
            3. configure in `.env`:
            ```
            GOOGLE_SERVICE_ACCOUNT_FILE=/path/to/key.json
            GOOGLE_DRIVE_FOLDER_ID=1YRFq0KvZ65QRp1psXkUDK6onIALswhE3
            ```
            4. Share folder with service account email
            """)
        else:
            st.success("✅ Google Drive Ready to use")
            
            # Initialize session state for uploaded videos
            if 'uploaded_videos' not in st.session_state:
                st.session_state.uploaded_videos = {}
            
            # Scene-by-scene upload
            st.markdown("**Upload video for each scene:**")
            st.caption("Filewill be namedNameas Scene_01.mp4, Scene_02.mp4 ... Automatic")
            
            for scene in project.scenes:
                with st.expander(f"🎬 Scene {scene.order}: {scene.narration_text[:50]}...", expanded=False):
                    col1, col2 = st.columns([3, 1])
                    
                    with col1:
                        # File uploader for this scene
                        uploaded_file = st.file_uploader(
                            f"Select video file",
                            type=["mp4", "mov", "avi", "mkv", "webm"],
                            key=f"video_upload_scene_{scene.order}",
                            help="Upload video for gen from Veo 3 for this scene"
                        )
                        
                        if uploaded_file:
                            # Save to temp file
                            temp_dir = Path("data/temp_uploads")
                            temp_dir.mkdir(parents=True, exist_ok=True)
                            
                            temp_path = temp_dir / f"scene_{scene.order}_{uploaded_file.name}"
                            with open(temp_path, "wb") as f:
                                f.write(uploaded_file.getvalue())
                            
                            # Store in session state
                            st.session_state.uploaded_videos[scene.order] = str(temp_path)
                            
                            st.success(f"✅ {uploaded_file.name} ({uploaded_file.size / 1024 / 1024:.1f} MB)")
                    
                    with col2:
                        st.caption(f"**Duration:**")
                        st.caption(f"{scene.audio_duration:.1f}s")
                        st.caption(f"**Filename:**")
                        st.caption(f"Scene_{scene.order:02d}.mp4")
            
            st.markdown("---")
            
            # Batch upload button
            if st.session_state.uploaded_videos:
                num_uploaded = len(st.session_state.uploaded_videos)
                total_scenes = len(project.scenes)
                
                col_upload, col_status = st.columns([2, 1])
                
                with col_upload:
                    if st.button(
                        f"🚀 Upload all to Google Drive ({num_uploaded} File)", 
                        type="primary",
                        use_container_width=True
                    ):
                        try:
                            # Authenticate
                            with st.spinner("🔑 Connecting Google Drive..."):
                                uploader.authenticate()
                            
                            # Prepare upload list
                            video_files = []
                            for scene_num, file_path in st.session_state.uploaded_videos.items():
                                video_files.append((file_path, scene_num))
                            
                            # Upload with progress
                            progress_bar = st.progress(0)
                            status_text = st.empty()
                            
                            def progress_callback(current, total, filename):
                                progress_bar.progress(current / total)
                                status_text.text(f"📤 Uploading ({current}/{total}): {filename}")
                            
                            # Upload
                            result = uploader.upload_scene_videos(
                                video_files,
                                project.title,
                                progress_callback=progress_callback
                            )
                            
                            # Show results
                            st.success(f"✅ Upload successful {len(result['files'])} File!")
                            
                            # Display links
                            st.markdown(f"**📁 Project Folder:** [Open Google Drive]({result['folder_url']})")
                            
                            # Show uploaded files
                            with st.expander("📋 Uploaded files list", expanded=True):
                                for file_info in result['files']:
                                    if 'error' in file_info:
                                        st.error(f"❌ Scene {file_info['scene']}: {file_info['error']}")
                                    else:
                                        st.success(f"✅ Scene {file_info['scene']}: [{file_info['name']}]({file_info['webViewLink']})")
                            
                            # Save folder URL to project
                            project.drive_folder_link = result['folder_url']
                            save_project(project)
                            
                            # Clear uploaded videos from session
                            st.session_state.uploaded_videos = {}
                            
                        except FileNotFoundError as e:
                            st.error(f"❌ not foundFile Service Account: {e}")
                            st.info("Please check GOOGLE_SERVICE_ACCOUNT_FILE in .env")
                        except ValueError as e:
                            st.error(f"❌ Invalid configuration: {e}")
                        except Exception as e:
                            st.error(f"❌ Upload failed: {e}")
                            import traceback
                            st.code(traceback.format_exc())
                
                with col_status:
                    st.metric("Uploaded", f"{num_uploaded}/{total_scenes}")
            else:
                st.info("💡 UploadFilevideooffor each scene above")
    
    st.markdown("---")
    
    # Google Drive link (keep existing section)
    st.subheader("📂 Google Drive Folder Link")

    
    drive_link = st.text_input(
        "🔗 Google Drive Folder Link",
        value=project.drive_folder_link,
        help="Enter link of folder to save"
    )
    project.drive_folder_link = drive_link
    
    if drive_link and "drive.google.com" in drive_link:
        st.markdown(f"[📂 Open Google Drive Folder]({drive_link})")
        st.info("👆 Click to open folder alreadyUploadFilevideo")
    
    st.markdown("---")
    
    # Category tagging
    st.subheader("🏷️ Category")
    
    category = st.selectbox(
        "SelectCategory",
        ["health", "lifestyle", "education", "entertainment", "business", "other"]
    )
    
    tags = st.text_input(
        "Tags (separated by comma)",
        placeholder="e.g.: Weight loss, Health, Exercise"
    )
    
    # Complete project
    st.markdown("---")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("💾 Save", use_container_width=True):
            save_project(project)
            st.success("Saved!")
    
    with col2:
        if st.button("🎉 Project completed", type="primary", use_container_width=True):
            project.status = "completed"
            project.updated_at = datetime.now()
            
            save_project(project)
            
            st.balloons()
            st.success("🎉 Project complete!")
            
            # Show summary
            st.markdown("---")
            st.markdown(f"""
            ### ✅ Summary
            
            - **Name:** {project.title}
            - **Topic:** {project.topic}
            - **Number of scenes:** {len(project.scenes)}
            - **Duration:** {project.total_duration:.1f} seconds
            - **Status:** Completed ✅
            - **Drive Folder:** [Link]({project.drive_folder_link})
            """)


if __name__ == "__main__":
    main()
