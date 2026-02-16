"""
Database & Tags Page - Manage Projects and Tags
Database management interface for organizing projects
"""
import streamlit as st

# Core imports
from src.core.database import (
    db_get_all_projects,
    db_delete_project,
    db_update_project_metadata
)
from src.frontend.utils import show_back_button


def render():
    """Page 6: Database & Tags management"""
    show_back_button()
    
    st.title("6️⃣ Database & Tags - Project Management")
    
    st.markdown("""
    **🗄️ Manage your video content database**
    - View all projects
    - Update tags and metadata
    - Bulk operations
    """)
    
    st.markdown("---")
    
    # Database stats
    try:
        all_projects = db_get_all_projects()
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Projects", len(all_projects))
        with col2:
            completed = len([p for p in all_projects if p.get("status") == "completed"])
            st.metric("Completed", completed)
        with col3:
            drafts = len([p for p in all_projects if p.get("status") == "draft"])
            st.metric("Drafts", drafts)
        with col4:
            editing = len([p for p in all_projects if p.get("status") == "editing"])
            st.metric("Editing", editing)
        
        st.markdown("---")
        
        # Tag Manager Section
        st.subheader("🏷️ Tag Manager")
        
        # Extract all unique tags
        all_tags = set()
        for proj in all_projects:
            tags = proj.get("tags", [])
            if tags:
                all_tags.update(tags)
        
        if all_tags:
            st.markdown(f"**Available Tags:** {', '.join(sorted(all_tags))}")
        else:
            st.info("No tags found. Add tags to projects to organize them.")
        
        st.markdown("---")
        
        # Project List with Tag Editing
        st.subheader("📋 Project List")
        
        if not all_projects:
            st.info("No projects in database.")
            return
        
        for proj_data in all_projects:
            with st.expander(f"📁 {proj_data.get('title', 'Untitled')}"):
                col1, col2 = st.columns([2, 1])
                
                with col1:
                    # Use 'id' not 'project_id' from db_list_projects
                    project_id = proj_data.get('id') or proj_data.get('project_id', 'N/A')
                    st.markdown(f"**ID:** `{project_id}`")
                    st.markdown(f"**Status:** {proj_data.get('status', 'unknown')}")
                    # Use 'created' not 'created_at'
                    created = proj_data.get('created') or proj_data.get('created_at', 'Unknown')
                    created_str = str(created)[:10] if created else 'Unknown'
                    st.markdown(f"**Created:** {created_str}")
                    
                    # Current tags
                    current_tags = proj_data.get("tags", [])
                    st.markdown(f"**Current Tags:** {', '.join(current_tags) if current_tags else 'None'}")
                    
                    # Tag editor
                    new_tags_input = st.text_input(
                        "Add/Edit Tags (comma-separated)",
                        value=", ".join(current_tags) if current_tags else "",
                        key=f"tags_{project_id}"
                    )
                    
                    if st.button("💾 Save Tags", key=f"save_tags_{project_id}"):
                        # Parse new tags
                        new_tags = [t.strip() for t in new_tags_input.split(",") if t.strip()]
                        
                        try:
                            # Update in database
                            db_update_project_metadata(
                                project_id,
                                {"tags": new_tags}
                            )
                            st.success("✅ Tags updated!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Failed to update tags: {e}")
                
                with col2:
                    # Quick stats - scenes is already int from db_list_projects
                    scenes_count = proj_data.get("scenes", 0)
                    if isinstance(scenes_count, list):
                        scenes_count = len(scenes_count)
                    st.metric("Scenes", scenes_count)
                    
                    # Delete button
                    if st.button("🗑️ Delete Project", key=f"del_db_{project_id}", type="secondary"):
                        try:
                            db_delete_project(project_id)
                            st.success("Deleted!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Failed to delete: {e}")
        
        st.markdown("---")
        
        # Bulk Operations
        st.subheader("🔧 Bulk Operations")
        
        with st.expander("⚠️ Danger Zone"):
            st.warning("**Warning:** These operations cannot be undone!")
            
            if st.button("🗑️ Delete All Drafts", type="secondary"):
                drafts = [p for p in all_projects if p.get("status") == "draft"]
                for draft in drafts:
                    try:
                        db_delete_project(draft["project_id"])
                    except Exception:
                        continue  # Skip failed deletions in bulk op
                st.success(f"Deleted {len(drafts)} drafts")
                st.rerun()
        
    except Exception as e:
        st.error(f"Database error: {e}")
        st.info("Make sure database is properly configured.")
