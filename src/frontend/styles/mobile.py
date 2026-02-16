"""
Mobile Responsive Styling
CSS for mobile-friendly responsive design
"""
import streamlit as st


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
