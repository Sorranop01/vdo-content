"""
Session State Management
Handles Streamlit session state initialization and management
"""
import streamlit as st
import uuid
from typing import Any


def init_session_state(defaults: dict[str, Any] = None):
    """Initialize session state with default values"""
    # Generate unique session ID if not exists
    if "session_id" not in st.session_state:
        st.session_state.session_id = str(uuid.uuid4())[:8]
    
    # Default values
    base_defaults = {
        "current_project": None,
        "proposal": None,
        "proposal_version": 1,
        "script": "",
        "audio_segments": [],
        "scenes": [],
        "page": 0,  # 0 = Home
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
    
    # Merge with provided defaults
    if defaults:
        base_defaults.update(defaults)
    
    # Set defaults
    for key, value in base_defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


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
    st.session_state.scenes = project.scenes or []
    st.session_state.proposal = project.proposal
    
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
