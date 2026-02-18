"""
Mobile Responsive Styling
Comprehensive CSS for mobile-friendly VDO Content app
Fixes: touch targets, sidebar overlay, z-index stacking, scroll blocking
"""
import streamlit as st


def apply_mobile_styles():
    """Apply responsive mobile-friendly styles"""
    st.markdown("""
    <style>
    /* ============================================
       MOBILE RESPONSIVE — VDO Content
       ============================================ */
    
    /* ---- Global Touch Device Fixes ---- */
    @media (hover: none) and (pointer: coarse) {
        /* Prevent 300ms tap delay on all touch devices */
        * {
            touch-action: manipulation;
        }
        
        /* Prevent iOS zoom on input focus (font-size must be ≥16px) */
        input, textarea, select, .stTextInput input, .stTextArea textarea {
            font-size: 16px !important;
        }
        
        /* Visual tap feedback */
        .stButton > button:active,
        [data-testid="stBaseButton-secondary"]:active {
            transform: scale(0.97);
            opacity: 0.85;
            transition: transform 0.05s ease, opacity 0.05s ease;
        }
        
        /* Remove sticky hover effects on touch */
        .stButton > button:hover {
            transform: none !important;
        }
    }
    
    /* ---- Tablet & Mobile (≤ 768px) ---- */
    @media (max-width: 768px) {
    
        /* --- SIDEBAR FIX (most critical) --- */
        /* Sidebar must float OVER content, not push it */
        [data-testid="stSidebar"] {
            z-index: 999 !important;
            position: fixed !important;
            top: 0 !important;
            left: 0 !important;
            height: 100vh !important;
            width: 85vw !important;
            max-width: 320px !important;
            min-width: unset !important;
            overflow-y: auto !important;
            -webkit-overflow-scrolling: touch !important;
            transition: transform 0.25s ease !important;
            box-shadow: 4px 0 24px rgba(0,0,0,0.5) !important;
        }
        
        /* When sidebar is collapsed, slide it off-screen */
        [data-testid="stSidebar"][aria-expanded="false"] {
            transform: translateX(-100%) !important;
            box-shadow: none !important;
        }
        
        /* Sidebar toggle button (hamburger) — always accessible */
        [data-testid="stSidebarCollapsedControl"],
        [data-testid="collapsedControl"] {
            z-index: 1000 !important;
            position: fixed !important;
            top: 0.5rem !important;
            left: 0.5rem !important;
        }
        
        /* Sidebar close button — larger touch target */
        [data-testid="stSidebar"] [data-testid="stSidebarCollapseButton"] button,
        [data-testid="stSidebar"] button[kind="header"] {
            min-width: 44px !important;
            min-height: 44px !important;
            padding: 8px !important;
        }
        
        /* Sidebar internal padding */
        [data-testid="stSidebar"] [data-testid="stSidebarContent"] {
            padding: 1rem 0.75rem !important;
        }
        
        /* --- MAIN CONTENT --- */
        .main .block-container {
            padding-left: 1rem !important;
            padding-right: 1rem !important;
            padding-top: 3rem !important;
            max-width: 100% !important;
        }
        
        /* --- COLUMNS → STACK VERTICALLY --- */
        [data-testid="stHorizontalBlock"] {
            flex-wrap: wrap !important;
            gap: 0.5rem !important;
        }
        
        [data-testid="column"] {
            width: 100% !important;
            flex: 0 0 100% !important;
            min-width: 100% !important;
        }
        
        /* --- BUTTONS — Large Touch Targets --- */
        .stButton > button,
        [data-testid="stBaseButton-primary"],
        [data-testid="stBaseButton-secondary"] {
            min-height: 48px !important;
            font-size: 15px !important;
            padding: 10px 20px !important;
            border-radius: 8px !important;
            /* Ensure buttons are always tappable */
            position: relative !important;
            z-index: 1 !important;
            pointer-events: auto !important;
        }
        
        /* --- RADIO BUTTONS — Larger Touch Area --- */
        [data-testid="stRadio"] label,
        [data-testid="stRadio"] [role="radiogroup"] label {
            min-height: 44px !important;
            padding: 10px 12px !important;
            display: flex !important;
            align-items: center !important;
            gap: 8px !important;
            cursor: pointer !important;
            font-size: 15px !important;
        }
        
        /* Radio button circle — bigger hitbox */
        [data-testid="stRadio"] input[type="radio"] {
            width: 22px !important;
            height: 22px !important;
            min-width: 22px !important;
        }
        
        /* --- CHECKBOXES — Larger Touch --- */
        [data-testid="stCheckbox"] label {
            min-height: 44px !important;
            padding: 8px !important;
            display: flex !important;
            align-items: center !important;
            gap: 8px !important;
        }
        
        [data-testid="stCheckbox"] input[type="checkbox"] {
            width: 22px !important;
            height: 22px !important;
            min-width: 22px !important;
        }
        
        /* --- SELECT/DROPDOWN — Touch Friendly --- */
        .stSelectbox > div > div,
        [data-testid="stSelectbox"] > div > div {
            min-height: 48px !important;
        }
        
        .stSelectbox [data-baseweb="select"] {
            min-height: 48px !important;
        }
        
        .stSelectbox [data-baseweb="select"] > div {
            padding: 8px 12px !important;
            font-size: 15px !important;
        }
        
        /* Dropdown menu items — larger */
        [data-baseweb="menu"] [role="option"] {
            min-height: 44px !important;
            padding: 10px 16px !important;
            font-size: 15px !important;
        }
        
        /* --- TEXT INPUTS --- */
        .stTextInput > div > div > input,
        .stTextArea > div > div > textarea {
            min-height: 48px !important;
            font-size: 16px !important;
            padding: 10px 12px !important;
        }
        
        /* Text area — reasonable height for mobile */
        .stTextArea > div > div > textarea {
            min-height: 80px !important;
        }
        
        /* --- SLIDER — Touch Friendly --- */
        [data-testid="stSlider"] [data-baseweb="slider"] [role="slider"] {
            width: 28px !important;
            height: 28px !important;
        }
        
        /* --- FILE UPLOADER --- */
        [data-testid="stFileUploader"] {
            min-height: 100px !important;
        }
        
        [data-testid="stFileUploader"] section {
            padding: 16px !important;
        }
        
        /* --- EXPANDER --- */
        .streamlit-expanderHeader,
        [data-testid="stExpander"] summary {
            min-height: 48px !important;
            padding: 12px 16px !important;
            font-size: 15px !important;
        }
        
        /* --- TABS --- */
        .stTabs [data-baseweb="tab-list"] button {
            min-height: 44px !important;
            padding: 8px 16px !important;
            font-size: 14px !important;
        }
        
        /* --- TYPOGRAPHY --- */
        h1 { font-size: 1.6rem !important; }
        h2 { font-size: 1.35rem !important; }
        h3 { font-size: 1.15rem !important; }
        
        /* --- PROGRESS BAR --- */
        [data-testid="stProgress"] {
            margin: 8px 0 !important;
        }
        
        /* --- METRICS --- */
        [data-testid="stMetricValue"] {
            font-size: 1.4rem !important;
        }
        
        /* --- ALERT/INFO BOXES --- */
        .stAlert, [data-testid="stAlert"] {
            padding: 12px !important;
            font-size: 14px !important;
        }
        
        /* --- Z-INDEX FIX: Prevent invisible overlapping layers --- */
        /* This is the #1 cause of "can't click" on mobile */
        [data-testid="stHorizontalBlock"] {
            position: relative !important;
            z-index: auto !important;
            overflow: visible !important;
        }
        
        [data-testid="column"] {
            position: relative !important;
            z-index: auto !important;
            overflow: visible !important;
        }
        
        /* Ensure nothing blocks interactive elements */
        [data-testid="stVerticalBlock"] {
            overflow: visible !important;
        }
        
        /* Form elements must be above any decorative layers */
        .stForm {
            position: relative !important;
            z-index: 2 !important;
        }
    }
    
    /* ---- Small Phone (≤ 480px) ---- */
    @media (max-width: 480px) {
        /* Full width buttons */
        .stButton > button,
        [data-testid="stBaseButton-primary"],
        [data-testid="stBaseButton-secondary"] {
            min-height: 52px !important;
            width: 100% !important;
            font-size: 16px !important;
        }
        
        /* Even less padding */
        .main .block-container {
            padding-left: 0.5rem !important;
            padding-right: 0.5rem !important;
        }
        
        /* Sidebar — near full width on very small screens */
        [data-testid="stSidebar"] {
            width: 90vw !important;
            max-width: 300px !important;
        }
        
        /* Smaller headings */
        h1 { font-size: 1.4rem !important; }
        h2 { font-size: 1.2rem !important; }
        h3 { font-size: 1.05rem !important; }
        
        /* Compact caption text */
        .stCaption, [data-testid="stCaption"] {
            font-size: 12px !important;
        }
    }
    
    /* ---- Landscape Phone Fix ---- */
    @media (max-height: 500px) and (orientation: landscape) {
        [data-testid="stSidebar"] {
            width: 280px !important;
            max-width: 40vw !important;
        }
        
        .main .block-container {
            padding-top: 1rem !important;
        }
    }
    
    </style>
    """, unsafe_allow_html=True)
