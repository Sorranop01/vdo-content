"""
VDO Content V3 - Main Application File
5-Step Workflow: สร้างโปรเจค → กำหนดคอนเทนต์ → บทพูด → สร้าง Prompt → อัพโหลด
"""
import streamlit as st
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add project root to path for imports (app.py is at project root)
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Import configuration
from src.config import settings
from src.config.constants import (
    VERSION, APP_NAME,
    STEP_PROJECT, STEP_CONTENT, STEP_SCRIPT, STEP_VIDEO_PROMPT, STEP_UPLOAD,
    STEP_DATABASE, STEP_SETTINGS
)

# Import frontend utilities
from src.frontend.utils import init_session_state
from src.frontend.styles import apply_dark_mode, apply_mobile_styles
from src.frontend.components import show_progress_bar

# Page configuration
st.set_page_config(
    page_title=f"{APP_NAME}",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="collapsed"
)


def check_password() -> bool:
    """Simple password gate using .streamlit/secrets.toml credentials."""
    if st.session_state.get("authenticated"):
        return True

    # Check if credentials are configured
    try:
        credentials = st.secrets.get("credentials", {})
    except Exception:
        credentials = {}

    if not credentials:
        # No credentials configured — skip auth (dev mode)
        return True

    st.markdown(
        """
        <style>
        .login-container {
            max-width: 400px;
            margin: 80px auto;
            padding: 40px;
            border-radius: 16px;
            background: rgba(30, 30, 40, 0.8);
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255,255,255,0.1);
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("## 🎬 VDO Content")
        st.markdown("กรุณาเข้าสู่ระบบ")
        
        with st.form("login_form"):
            username = st.text_input("👤 ชื่อผู้ใช้", placeholder="username")
            password = st.text_input("🔑 รหัสผ่าน", type="password", placeholder="password")
            submitted = st.form_submit_button("เข้าสู่ระบบ", use_container_width=True, type="primary")

        if submitted:
            if username in credentials and credentials[username] == password:
                st.session_state["authenticated"] = True
                st.session_state["username"] = username
                st.rerun()
            else:
                st.error("❌ ชื่อผู้ใช้หรือรหัสผ่านไม่ถูกต้อง")

    return False


def render_sidebar():
    """Render sidebar navigation with 5-step workflow"""
    with st.sidebar:
        st.title(f"🎬 {APP_NAME}")
        st.caption(f"v{VERSION}")
        st.markdown("---")
        
        # 5-Step Workflow Navigation
        st.subheader("📍 5 ขั้นตอน")
        
        workflow_map = {
            "1️⃣ สร้างโปรเจค": STEP_PROJECT,
            "2️⃣ กำหนดคอนเทนต์": STEP_CONTENT,
            "3️⃣ บทพูด": STEP_SCRIPT,
            "4️⃣ สร้าง Prompt": STEP_VIDEO_PROMPT,
            "5️⃣ อัพโหลดไฟล์": STEP_UPLOAD
        }
        workflow_options = list(workflow_map.keys())
        
        # Determine current selection
        if st.session_state.page in workflow_map.values():
            current_wf_index = list(workflow_map.values()).index(st.session_state.page)
            st.session_state.last_workflow_page = st.session_state.page
        else:
            if "last_workflow_page" in st.session_state and st.session_state.last_workflow_page in workflow_map.values():
                current_wf_index = list(workflow_map.values()).index(st.session_state.last_workflow_page)
            else:
                current_wf_index = 0
                st.session_state.last_workflow_page = STEP_PROJECT
        
        # CRITICAL: Sync the radio widget's session key with the current page.
        # Without this, Streamlit uses the stale wf_nav value (from the previous
        # render) instead of the index parameter, causing "Next" button navigation
        # to bounce back to the old step.
        st.session_state.wf_nav = workflow_options[current_wf_index]
        
        # Workflow selector with callback
        def _on_workflow_change():
            wf_key = st.session_state.wf_nav
            st.session_state.page = workflow_map[wf_key]
            st.session_state.last_workflow_page = workflow_map[wf_key]
        
        st.radio(
            "ขั้นตอน",
            workflow_options,
            index=current_wf_index,
            label_visibility="collapsed",
            key="wf_nav",
            on_change=_on_workflow_change
        )
        
        # Show workflow progress
        project = st.session_state.get("current_project")
        if project:
            step = project.workflow_step if hasattr(project, 'workflow_step') else 0
            st.progress(min((step + 1) / 5, 1.0))
            st.caption(f"📁 {project.title[:20]}..." if len(project.title) > 20 else f"📁 {project.title}")
        
        st.markdown("---")
        
        # Management Navigation
        st.subheader("🛠️ จัดการ")
        
        if st.button("🗃️ Database & Tags", use_container_width=True, 
                    type="primary" if st.session_state.page == STEP_DATABASE else "secondary"):
            st.session_state.page = STEP_DATABASE
            st.rerun()
        
        if st.button("⚙️ Settings", use_container_width=True,
                    type="primary" if st.session_state.page == STEP_SETTINGS else "secondary"):
            st.session_state.page = STEP_SETTINGS
            st.rerun()
        
        st.markdown("---")
        
        # Show logged-in user and logout button
        username = st.session_state.get("username", "")
        if username:
            st.caption(f"👤 เข้าสู่ระบบเป็น: **{username}**")
            if st.button("🚪 ออกจากระบบ", use_container_width=True):
                st.session_state["authenticated"] = False
                st.session_state["username"] = ""
                st.rerun()
            st.markdown("---")
        
        st.caption("🎬 AI Content Pipeline  \n⚡ Powered by AI Studio & Veo 3")


def main():
    """Main application logic"""
    # Apply styles first (for login page too)
    apply_dark_mode()
    apply_mobile_styles()
    
    # ── Login Gate ──
    if not check_password():
        st.stop()
    
    # Initialize session state
    api_key = os.getenv("DEEPSEEK_API_KEY", "")
    init_session_state(defaults={"api_key": api_key})
    
    # Render sidebar
    render_sidebar()
    
    # Get current page
    page = st.session_state.get("page", STEP_PROJECT)
    
    # Render appropriate page
    if page == STEP_PROJECT:       # Step 1: สร้างโปรเจค
        from src.frontend.pages import step1_project
        step1_project.render()
    elif page == STEP_CONTENT:     # Step 2: กำหนดคอนเทนต์
        from src.frontend.pages import step2_content
        step2_content.render()
    elif page == STEP_SCRIPT:      # Step 3: บทพูด
        from src.frontend.pages import step3_script
        step3_script.render()
    elif page == STEP_VIDEO_PROMPT: # Step 4: สร้าง Prompt
        from src.frontend.pages import step4_video_prompt
        step4_video_prompt.render()
    elif page == STEP_UPLOAD:      # Step 5: อัพโหลดไฟล์
        from src.frontend.pages import step5_upload
        step5_upload.render()
    elif page == STEP_DATABASE:    # Database & Tags
        from src.frontend.pages import database_tags
        database_tags.render()
    elif page == STEP_SETTINGS:    # Settings
        from src.frontend.pages import settings
        settings.render()
    else:
        st.warning("⚠️ ไม่พบหน้านี้")
        if st.button("🏠 กลับหน้าแรก", type="primary"):
            st.session_state.page = STEP_PROJECT
            st.rerun()


if __name__ == "__main__":
    main()
