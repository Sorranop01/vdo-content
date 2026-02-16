"""
Progress Bar Component
Sidebar progress indicator for workflow steps
"""
import streamlit as st


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


def show_back_button():
    """Show back navigation button"""
    if st.session_state.get("page", 0) > 0:
        if st.button("← Back", key="back_btn"):
            st.session_state.page = max(0, st.session_state.page - 1)
            st.rerun()
