"""
Sidebar component for navigation
"""

import streamlit as st


def show_sidebar(
    version: str,
    show_progress_fn,
    workflow_map: dict = None
):
    """
    Render the sidebar navigation
    
    Args:
        version: App version string
        show_progress_fn: Function to show progress bar
        workflow_map: Mapping of workflow names to page indices
    """
    if workflow_map is None:
        workflow_map = {
            "🏠 Home": 0,
            "1️⃣ Ideation": 1,
            "2️⃣ Script": 2,
            "3️⃣ Audio Sync": 3,
            "4️⃣ Veo Prompts": 4,
            "5️⃣ Archive": 5
        }
    
    st.title("🎬 VDO Content V2")
    st.caption(f"v{version}")
    st.markdown("---")
    
    # --- Workflow Navigation ---
    st.subheader("📍 Workflow")
    
    workflow_options = list(workflow_map.keys())
    
    # Determine current selection index based on page state
    current_wf_index = 0
    if 0 <= st.session_state.page <= 5:
        current_wf_index = st.session_state.page
        
    selected_wf = st.radio(
        "ขั้นตอนการทำงาน",
        workflow_options,
        index=current_wf_index,
        label_visibility="collapsed",
        key="wf_nav"
    )
    
    # Handle workflow navigation
    if workflow_map[selected_wf] != st.session_state.page and st.session_state.page <= 5:
        st.session_state.page = workflow_map[selected_wf]
        st.rerun()

    st.markdown("---")
    
    # --- Management Navigation ---
    st.subheader("🛠️ Management")
    
    if st.button("🗃️ Database & Tags", use_container_width=True, type="primary" if st.session_state.page == 6 else "secondary"):
        st.session_state.page = 6
        st.rerun()
        
    # Progress bar (Show only in workflow pages)
    if st.session_state.page <= 5:
        show_progress_fn()
    
    st.markdown("---")
    
    # Current project info
    if st.session_state.current_project:
        project = st.session_state.current_project
        st.success(f"📁 {project.title}")
        st.caption(f"Status: {project.status}")
        st.caption(f"Scenes: {len(project.scenes)}")
        
        if st.button("🏠 กลับ Home", use_container_width=True):
            st.session_state.page = 0
            st.rerun()
    else:
        st.info("No project loaded")
    
    st.markdown("---")
    
    # Settings section (Collapsible)
    with st.expander("⚙️ System Config"):
        # LLM Provider selector
        try:
            from core.llm_config import get_provider_choices, get_model_choices
            
            providers = get_provider_choices()
            provider_ids = [p[0] for p in providers]
            provider_names = [p[1] for p in providers]
            
            # Initialize default if not set
            if "llm_provider" not in st.session_state:
                st.session_state.llm_provider = "deepseek"
            
            current_idx = provider_ids.index(st.session_state.llm_provider) if st.session_state.llm_provider in provider_ids else 0
            
            selected_provider = st.selectbox(
                "🤖 LLM Provider",
                provider_names,
                index=current_idx,
                key="llm_selector"
            )
            
            # Update session state
            st.session_state.llm_provider = provider_ids[provider_names.index(selected_provider)]
            
            # Model selector
            models = get_model_choices(st.session_state.llm_provider)
            if models:
                if "llm_model" not in st.session_state:
                    st.session_state.llm_model = models[0][0]
                
                model_ids = [m[0] for m in models]
                model_names = [m[1] for m in models]
                current_model_idx = model_ids.index(st.session_state.llm_model) if st.session_state.llm_model in model_ids else 0
                
                selected_model = st.selectbox(
                    "📋 Model",
                    model_names,
                    index=current_model_idx,
                    key="model_selector"
                )
                st.session_state.llm_model = model_ids[model_names.index(selected_model)]
        except ImportError:
            st.warning("LLM config not available")
        
        st.divider()
        
        # API Key status (hidden, only show status)
        if st.session_state.api_key:
            st.success("🔑 API Key: ตั้งค่าแล้ว ✅")
        else:
            st.warning("🔑 API Key: ไม่พบ (ตั้งค่าใน .env)")
        
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

