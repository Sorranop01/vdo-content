"""
Shared utilities for UI components
"""

import streamlit as st
from pathlib import Path

# Import from app.py when loaded for module compatibility
# These will be injected by main app


def show_back_button():
    """Show back navigation button"""
    if st.session_state.page > 0:
        if st.button("← ย้อนกลับ", key="back_btn"):
            st.session_state.page = max(0, st.session_state.page - 1)
            st.rerun()


def show_progress_bar():
    """Show workflow progress in sidebar"""
    page = st.session_state.page
    if page == 0:
        return
    
    total_steps = 6
    progress = page / total_steps
    progress = max(0.0, min(progress, 1.0))
    
    st.sidebar.markdown("---")
    st.sidebar.markdown("**📊 Progress:**")
    st.sidebar.progress(progress)
    st.sidebar.caption(f"Step {page}/{total_steps}")


def copy_to_clipboard(text: str, key: str):
    """Copy text with feedback"""
    try:
        import pyperclip
        pyperclip.copy(text)
        st.toast("📋 Copied!", icon="✅")
        return True
    except Exception:
        pass
    # Fallback: show in code box
    st.code(text, language="text")
    st.info("👆 Select and copy (Ctrl+C)")
    return False


def auto_save_project():
    """Auto-save current project if enabled"""
    if st.session_state.auto_save and st.session_state.current_project:
        from ui.utils import save_project, update_last_active
        pid = save_project(st.session_state.current_project)
        update_last_active(st.session_state.current_project.project_id, st.session_state.page)
