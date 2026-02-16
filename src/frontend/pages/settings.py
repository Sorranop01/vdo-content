"""
Settings Page - Manage Database and Presets
Configure visual library, style presets, and video profiles
"""
import streamlit as st

# Core imports
from src.core.database import (
    get_all_tags_raw,
    add_tag,
    delete_tag,
    get_all_style_presets,
    save_style_preset,
    delete_style_preset
)
from src.frontend.utils import show_back_button

# Check database availability
try:
    from src.core.database import DATABASE_AVAILABLE
except ImportError:
    DATABASE_AVAILABLE = False


def render():
    """Page 7: Settings & Database Management"""
    show_back_button()
    
    st.title("⚙️ Settings & Database")
    
    if not DATABASE_AVAILABLE:
        st.error("❌ Database not available")
        st.info("Database features require proper configuration. Please check your database connection.")
        return

    tab1, tab2, tab3 = st.tabs(["🏷️ Visual Library", "💾 Style Presets (Saved Styles)", "🎬 Master Video Profiles"])
    
    # --- Tab 1: Visual Tags Manager ---
    with tab1:
        st.caption("Manage options that appear in Visual Builder page (editable like Excel)")
        
        try:
            # 1. Fetch all data
            all_tags = get_all_tags_raw()
            
            # 2. Category Filter
            categories = sorted(list(set(t["category"] for t in all_tags)))
            # Map nice names
            cat_map = {
                "mood": "🎨 Mood",
                "lighting": "💡 Lighting",
                "camera_angle": "🎥 Camera Angle",
                "movement": "🎬 Movement",
                "shot_size": "📐 Shot Size",
                "style": "🖌️ Style"
            }
            
            selected_cat = st.radio(
                "Category",
                categories,
                format_func=lambda x: cat_map.get(x, x.title()),
                horizontal=True
            )
            
            # 3. Display current tags
            current_tags = [t for t in all_tags if t["category"] == selected_cat]
            
            st.subheader(f"Tags in {cat_map.get(selected_cat, selected_cat)}")
            
            if current_tags:
                # Display as simple list with delete buttons
                for tag in current_tags:
                    col1, col2 = st.columns([4, 1])
                    with col1:
                        st.text(f"• {tag.get('tag_name', 'N/A')}")
                    with col2:
                        if st.button("🗑️", key=f"del_{tag.get('id')}", help="Delete tag"):
                            try:
                                delete_tag(tag["id"])
                                st.success("Deleted!")
                                st.rerun()
                            except Exception as e:
                                st.error(f"Error: {e}")
            else:
                st.info("No tags in this category yet.")
            
            # 4. Add new tag
            st.markdown("---")
            st.subheader("Add New Tag")
            
            new_tag_name = st.text_input("Tag Name", key="new_tag")
            if st.button("➕ Add Tag", type="primary"):
                if new_tag_name.strip():
                    try:
                        add_tag(selected_cat, new_tag_name.strip())
                        st.success(f"Added: {new_tag_name}")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error: {e}")
                else:
                    st.warning("Please enter a tag name")
        
        except Exception as e:
            st.error(f"Error loading tags: {e}")
    
    # --- Tab 2: Style Presets ---
    with tab2:
        st.caption("Saved style combinations for quick reuse")
        
        try:
            presets = get_all_style_presets()
            
            if presets:
                st.subheader("Saved Presets")
                for preset in presets:
                    with st.expander(f"📋 {preset.get('preset_name', 'Unnamed')}"):
                        st.json(preset.get('preset_data', {}))
                        
                        if st.button("🗑️ Delete", key=f"del_preset_{preset.get('id')}"):
                            try:
                                delete_style_preset(preset['id'])
                                st.success("Deleted!")
                                st.rerun()
                            except Exception as e:
                                st.error(f"Error: {e}")
            else:
                st.info("No saved presets yet. Create one from the Visual Builder page!")
            
        except Exception as e:
            st.error(f"Error loading presets: {e}")
    
    # --- Tab 3: Master Video Profiles ---
    with tab3:
        st.caption("Master video profile configurations")
        
        st.info("🚧 Video Profiles management coming soon!")
        st.markdown("""
        **Future features:**
        - Manage AI Studio voice profiles
        - Configure video generation settings
        - Set default aspect ratios and durations
        """)
