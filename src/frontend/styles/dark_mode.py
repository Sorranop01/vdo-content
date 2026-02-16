"""
Dark Mode Styling
CSS for dark mode theme
"""
import streamlit as st


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
