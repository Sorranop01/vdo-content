"""
UI Helper Utilities
Common UI components used across pages
"""
import streamlit as st
from typing import Optional
from datetime import datetime

from src.core.models import Project


def show_back_button():
    """Show back navigation button"""
    if st.session_state.get("page", 0) > 0:
        if st.button("← Back", key="back_btn"):
            st.session_state.page = max(0, st.session_state.page - 1)
            st.rerun()


def show_progress_bar():
    """Show workflow progress in sidebar"""
    page = st.session_state.get("page", 0)
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


def goto_page(page_num: int):
    """Navigate to specific page"""
    st.session_state.page = page_num
    st.rerun()


def goto_next_page():
    """Navigate to next page"""
    current = st.session_state.get("page", 0)
    st.session_state.page = current + 1
    st.rerun()


def goto_prev_page():
    """Navigate to previous page"""
    current = st.session_state.get("page", 0)
    st.session_state.page = max(0, current - 1)
    st.rerun()


def auto_save_project():
    """Auto-save current project if enabled"""
    from src.shared.project_manager import save_project
    
    if st.session_state.get("auto_save") and st.session_state.get("current_project"):
        pid = save_project(st.session_state.current_project)
        # Also save as last active
        update_last_active(st.session_state.current_project.project_id, st.session_state.get("page", 0))


def update_last_active(project_id: str, page: int):
    """Update last active project and page"""
    try:
        from src.core.database import db_update_last_active
        db_update_last_active(project_id, page)
    except Exception as e:
        import logging
        logging.getLogger("vdo_content.ui_helpers").debug(f"Failed to update last active: {e}")


def check_step_requirements(step: int) -> tuple[bool, str]:
    """
    Check if required data exists for a given step.
    
    Returns:
        (ok, message) — ok=True if step can proceed, message explains what's missing.
    """
    project = st.session_state.get("current_project")
    
    # Step 1 (สร้างโปรเจค) — always allowed
    if step <= 0:
        return True, ""
    
    # Step 2+ requires a project
    if not project:
        return False, "กรุณาสร้างหรือเลือกโปรเจคก่อน (Step 1)"
    
    if step <= 1:
        return True, ""
    
    # Step 3 (บทพูด) requires content plan from Step 2
    if step == 2:
        has_content = bool(
            project.content_description or project.content_goal or project.topic
        )
        if not has_content:
            return False, "กรุณากำหนดเนื้อหาก่อน (Step 2: กำหนดคอนเทนต์)"
        return True, ""
    
    # Step 4 (สร้าง Prompt) requires script from Step 3
    if step == 3:
        has_script = bool(project.full_script)
        if not has_script:
            return False, "กรุณาเขียนหรือสร้างบทพูดก่อน (Step 3: บทพูด)"
        return True, ""
    
    # Step 5 (อัพโหลด) requires scenes with prompts from Step 4
    if step == 4:
        has_scenes = bool(project.scenes and len(project.scenes) > 0)
        if not has_scenes:
            return False, "กรุณาสร้าง Scenes และ Prompts ก่อน (Step 4: สร้าง Prompt)"
        return True, ""
    
    return True, ""


def show_step_guard(step: int) -> bool:
    """
    Show a warning and redirect button if step requirements are not met.
    
    Returns:
        True if step can proceed, False if blocked (UI warning shown).
    """
    ok, message = check_step_requirements(step)
    if not ok:
        st.warning(f"⚠️ {message}")
        
        # Show redirect button to the correct step
        target_step = max(0, step - 1)
        step_names = {0: "สร้างโปรเจค", 1: "กำหนดคอนเทนต์", 2: "บทพูด", 3: "สร้าง Prompt"}
        btn_label = f"← ไป {step_names.get(target_step, 'ขั้นตอนก่อนหน้า')}"
        
        if st.button(btn_label, type="primary", key=f"guard_redirect_{step}"):
            st.session_state.page = target_step
            st.rerun()
        return False
    return True

