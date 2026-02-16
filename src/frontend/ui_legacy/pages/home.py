"""
Home Page - Dashboard with project list and template gallery
"""

import streamlit as st
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from core.models import Project


def show_home_page(
    list_projects_fn,
    load_project_fn,
    save_project_fn,
    delete_project_fn
):
    """
    Page 0: Dashboard with project list
    
    Args:
        list_projects_fn: Function to list all projects
        load_project_fn: Function to load a project by ID
        save_project_fn: Function to save a project
        delete_project_fn: Function to delete a project by ID
    """
    st.title("🏠 VDO Content Dashboard")
    
    st.markdown("---")
    
    # Quick actions
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("➕ สร้างโปรเจคใหม่", type="primary", use_container_width=True):
            st.session_state.current_project = None
            st.session_state.proposal = None
            st.session_state.script = ""
            st.session_state.audio_segments = []
            st.session_state.page = 1
            st.rerun()
    
    projects = list_projects_fn()
    
    with col2:
        st.metric("📂 Total Projects", len(projects))
    
    with col3:
        completed = len([p for p in projects if p["status"] == "completed"])
        st.metric("✅ Completed", completed)
    
    st.markdown("---")
    
    # ============ Template Gallery ============
    st.subheader("📚 Quick Start from Template")
    
    try:
        from core.templates import TemplateManager
        
        manager = TemplateManager()
        templates = manager.list_templates()
        
        # Show templates in columns
        cols = st.columns(5)
        for i, template in enumerate(templates[:5]):  # Show first 5
            with cols[i]:
                emoji = {
                    "news": "📰",
                    "tutorial": "📚",
                    "product": "🛍️",
                    "story": "📖",
                    "knowledge": "🧠"
                }.get(template.category, "📁")
                
                st.markdown(f"**{emoji} {template.name}**")
                st.caption(f"{template.target_duration}s • {template.scene_count} scenes")
                
                if st.button("Use", key=f"use_template_{template.id}", use_container_width=True):
                    # Show dialog to get topic
                    st.session_state.selected_template = template.id
                    st.session_state.show_template_dialog = True
                    st.rerun()
        
        # Template dialog
        if st.session_state.get("show_template_dialog"):
            with st.container():
                st.divider()
                st.subheader("🎬 Create from Template")
                
                topic = st.text_input("หัวข้อเนื้อหา", placeholder="เช่น: วิธีลดน้ำหนัก 5 กก. ใน 1 เดือน")
                title = st.text_input("ชื่อโปรเจค (optional)", placeholder="ถ้าว่างจะใช้หัวข้อ")
                
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("✅ สร้าง", type="primary", use_container_width=True):
                        if topic:
                            template_id = st.session_state.selected_template
                            project = manager.apply_template(template_id, topic, title or None)
                            
                            # Save and open
                            save_project_fn(project)
                            st.session_state.current_project = project
                            st.session_state.show_template_dialog = False
                            st.session_state.page = 1  # Go to ideation
                            st.success(f"สร้างโปรเจค '{project.title}' จาก template!")
                            st.rerun()
                        else:
                            st.warning("กรุณากรอกหัวข้อ")
                
                with col2:
                    if st.button("❌ ยกเลิก", use_container_width=True):
                        st.session_state.show_template_dialog = False
                        st.rerun()
    except ImportError:
        st.info("Template system not available")
    
    st.markdown("---")
    
    # Project list
    st.subheader("📂 Recent Projects")
    
    if not projects:
        st.info("ยังไม่มีโปรเจค กด 'สร้างโปรเจคใหม่' เพื่อเริ่มต้น")
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
                with st.popover("✏️ แก้ไขชื่อ", help="เปลี่ยนชื่อโปรเจค"):
                    new_title = st.text_input("ชื่อใหม่", value=p['title'], key=f"edit_title_{p['id']}")
                    if st.button("บันทึก", key=f"save_title_{p['id']}"):
                        try:
                            proj_obj = load_project_fn(p['id'])
                            proj_obj.title = new_title
                            save_project_fn(proj_obj)
                            st.success("บันทึกแล้ว!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error: {e}")
            
            with col2:
                st.caption(f"🎬 {p['scenes']} scenes")
            
            with col3:
                if st.button("📂 Open", key=f"open_{p['id']}"):
                    project = load_project_fn(p['id'])
                    st.session_state.current_project = project
                    st.session_state.script = project.full_script
                    st.session_state.audio_segments = project.audio_segments
                    
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
                    delete_project_fn(p['id'])
                    st.rerun()
            
            st.markdown("---")

