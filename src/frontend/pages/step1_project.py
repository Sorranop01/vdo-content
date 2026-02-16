"""
Step 1: สร้างโปรเจค (Create Project)
Project creation with title, description, and date
"""
import streamlit as st
from datetime import datetime

# Imports
from src.core.models import Project
from src.shared.project_manager import save_project, list_projects, load_project, delete_project
from src.frontend.utils import reset_session_for_project
from src.config.constants import STEP_CONTENT


def _create_new_project():
    """Initialize a fresh project"""
    st.session_state.current_project = None
    st.session_state.page = 0


def render():
    """Step 1: สร้างโปรเจค"""
    st.title("1️⃣ สร้างโปรเจค")
    st.caption("สร้างโปรเจคใหม่หรือเปิดโปรเจคที่มีอยู่")
    
    st.markdown("---")
    
    # Tab layout: Create New vs Open Existing
    tab_new, tab_existing = st.tabs(["➕ สร้างใหม่", "📂 โปรเจคที่มีอยู่"])
    
    with tab_new:
        _render_create_form()
    
    with tab_existing:
        _render_project_list()


def _render_create_form():
    """Form to create new project"""
    st.subheader("📝 ข้อมูลโปรเจค")
    
    # Project Title (required)
    title = st.text_input(
        "📌 ชื่อโปรเจค *",
        value=st.session_state.get("draft_title", ""),
        placeholder="เช่น รีวิวร้านอาหารญี่ปุ่น, สอนทำเค้ก",
        key="step1_title"
    )
    
    # Description
    description = st.text_area(
        "📄 รายละเอียดโปรเจค",
        value=st.session_state.get("draft_description", ""),
        height=100,
        placeholder="อธิบายเกี่ยวกับโปรเจคของคุณ...",
        key="step1_description"
    )
    
    # Project Date
    col1, col2 = st.columns(2)
    with col1:
        project_date = st.date_input(
            "📅 วันที่เริ่มโปรเจค",
            value=datetime.now().date(),
            key="step1_date"
        )
    
    with col2:
        # Target Duration
        target_duration = st.slider(
            "⏱️ ความยาวเป้าหมาย (วินาที)",
            30, 300, 60,
            key="step1_duration"
        )
    
    st.markdown("---")
    
    # Action Buttons
    col_save, col_next = st.columns(2)
    
    with col_save:
        if st.button("💾 บันทึกโปรเจค", use_container_width=True, disabled=not title):
            project = Project(
                title=title,
                description=description,
                project_date=datetime.combine(project_date, datetime.min.time()),
                target_duration=target_duration,
                status="step1_project",
                workflow_step=0
            )
            
            project_id = save_project(project)
            project.project_id = project_id if isinstance(project_id, str) else project.project_id
            st.session_state.current_project = project
            
            # Clear drafts
            st.session_state.draft_title = ""
            st.session_state.draft_description = ""
            
            st.success(f"✅ บันทึกโปรเจค '{title}' สำเร็จ!")
    
    with col_next:
        if st.button("➡️ ถัดไป: กำหนดคอนเทนต์", type="primary", use_container_width=True, disabled=not title):
            # Create and save project first
            project = Project(
                title=title,
                description=description,
                project_date=datetime.combine(project_date, datetime.min.time()),
                target_duration=target_duration,
                status="step2_content",
                workflow_step=1
            )
            
            project_id = save_project(project)
            project.project_id = project_id if isinstance(project_id, str) else project.project_id
            st.session_state.current_project = project
            
            # Navigate to Step 2
            st.session_state.page = STEP_CONTENT
            st.rerun()
    
    if not title:
        st.info("💡 กรุณากรอกชื่อโปรเจคเพื่อดำเนินการต่อ")


def _render_project_list():
    """Display existing projects"""
    projects = list_projects()
    
    if not projects:
        st.info("📭 ยังไม่มีโปรเจค กรุณาสร้างโปรเจคใหม่")
        return
    
    # Metrics
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("📂 โปรเจคทั้งหมด", len(projects))
    with col2:
        completed = len([p for p in projects if p.get("status") == "completed"])
        st.metric("✅ เสร็จสิ้น", completed)
    with col3:
        in_progress = len([p for p in projects if p.get("status") != "completed"])
        st.metric("🔄 กำลังดำเนินการ", in_progress)
    
    st.markdown("---")
    
    # Status filter
    filter_status = st.selectbox(
        "🔍 กรองตามสถานะ",
        ["ทั้งหมด", "step1_project", "step2_content", "step3_script", "step4_prompt", "step5_upload", "completed"],
        format_func=lambda x: {
            "ทั้งหมด": "🌐 ทั้งหมด",
            "step1_project": "1️⃣ สร้างโปรเจค",
            "step2_content": "2️⃣ กำหนดคอนเทนต์",
            "step3_script": "3️⃣ บทพูด",
            "step4_prompt": "4️⃣ สร้าง Prompt",
            "step5_upload": "5️⃣ อัพโหลด",
            "completed": "✅ เสร็จสิ้น"
        }.get(x, x)
    )
    
    # Filter projects
    if filter_status != "ทั้งหมด":
        projects = [p for p in projects if p.get("status") == filter_status]
    
    # Display project cards
    for i, p in enumerate(projects):
        status_emoji = {
            "step1_project": "1️⃣",
            "step2_content": "2️⃣",
            "step3_script": "3️⃣",
            "step4_prompt": "4️⃣",
            "step5_upload": "5️⃣",
            "completed": "✅",
            # Legacy support
            "draft": "📝",
            "scripting": "✍️",
            "recording": "🎤",
            "editing": "🎬"
        }.get(p.get("status", "draft"), "📁")
        
        with st.container():
            col1, col2, col3 = st.columns([4, 1, 1])
            
            with col1:
                st.markdown(f"**{status_emoji} {p.get('title', 'Untitled')}**")
                if p.get('topic'):
                    st.caption(f"🎯 {p.get('topic')[:50]}...")
                elif p.get('description'):
                    st.caption(f"📄 {p.get('description')[:50]}...")
            
            with col2:
                if st.button("📂 เปิด", key=f"open_{p.get('id', i)}", use_container_width=True):
                    try:
                        project = load_project(p.get('id'))
                        reset_session_for_project(project)
                        
                        # Go to appropriate step based on status
                        step_map = {
                            "step1_project": 0,
                            "step2_content": 1,
                            "step3_script": 2,
                            "step4_prompt": 3,
                            "step5_upload": 4,
                            "completed": 4,
                            # Legacy
                            "draft": 0,
                            "scripting": 2,
                            "recording": 2,
                            "editing": 3
                        }
                        st.session_state.page = step_map.get(p.get('status'), 0)
                        st.rerun()
                    except Exception as e:
                        st.error(f"❌ ไม่สามารถเปิดโปรเจค: {e}")
                        st.info("💡 ข้อมูลอาจเสียหาย — ลองสร้างโปรเจคใหม่ หรือตรวจสอบ Database")
            
            with col3:
                if st.button("🗑️", key=f"del_{p.get('id', i)}", help="ลบโปรเจค"):
                    delete_project(p.get('id'))
                    st.rerun()
            
            st.markdown("---")
