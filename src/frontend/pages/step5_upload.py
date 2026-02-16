"""
Step 5: อัพโหลดไฟล์ (File Upload)
Create folder with date-project name format, upload multiple files
"""
import streamlit as st
import os
from pathlib import Path
from datetime import datetime

# Imports
from src.shared.project_manager import save_project
from src.frontend.utils import show_back_button, auto_save_project, show_step_guard
from src.config.constants import STEP_VIDEO_PROMPT, STEP_PROJECT, UPLOAD_DIR, DATA_DIR


def _create_upload_folder(project) -> str:
    """Create upload folder with format: YYYYMMDD-project_name"""
    # Format date
    project_date = project.project_date or project.created_at or datetime.now()
    if hasattr(project_date, 'strftime'):
        date_str = project_date.strftime("%Y%m%d")
    else:
        date_str = datetime.now().strftime("%Y%m%d")
    
    # Sanitize project name
    safe_name = "".join(c for c in project.title if c.isalnum() or c in (' ', '-', '_'))
    safe_name = safe_name.strip().replace(' ', '_')[:50]  # Limit length
    
    folder_name = f"{date_str}-{safe_name}"
    
    # Create folder
    upload_path = UPLOAD_DIR / folder_name
    upload_path.mkdir(parents=True, exist_ok=True)
    
    return str(upload_path), folder_name


def render():
    """Step 5: อัพโหลดไฟล์"""
    # Back button
    if st.button("← ย้อนกลับ: สร้าง Prompt"):
        st.session_state.page = STEP_VIDEO_PROMPT
        st.rerun()
    
    st.title("5️⃣ อัพโหลดไฟล์")
    
    if not show_step_guard(4):
        return
    
    project = st.session_state.current_project
    st.caption(f"📁 โปรเจค: **{project.title}**")
    
    st.markdown("---")
    
    # ===== FOLDER CREATION =====
    st.subheader("📂 โฟลเดอร์โปรเจค")
    
    # Create or get upload folder
    if not project.upload_folder:
        upload_path, folder_name = _create_upload_folder(project)
        project.upload_folder = folder_name
        project.final_video_path = upload_path
        st.session_state.current_project = project
        auto_save_project()
    
    folder_display = project.upload_folder or "ยังไม่ได้สร้าง"
    full_path = UPLOAD_DIR / folder_display if project.upload_folder else None
    
    col_folder, col_action = st.columns([3, 1])
    
    with col_folder:
        st.success(f"✅ โฟลเดอร์: **{folder_display}**")
        if full_path:
            st.caption(f"📍 Path: `{full_path}`")
    
    with col_action:
        if st.button("🔄 สร้างโฟลเดอร์ใหม่"):
            upload_path, folder_name = _create_upload_folder(project)
            project.upload_folder = folder_name
            project.final_video_path = upload_path
            st.session_state.current_project = project
            auto_save_project()
            st.rerun()
    
    st.markdown("---")
    
    # ===== FILE UPLOAD =====
    st.subheader("📤 อัพโหลดไฟล์")
    
    st.info("💡 สามารถอัพโหลดหลายไฟล์พร้อมกันได้")
    
    uploaded_files = st.file_uploader(
        "เลือกไฟล์วีดีโอ",
        type=["mp4", "webm", "mov", "avi", "mkv"],
        accept_multiple_files=True,
        key="step5_upload"
    )
    
    if uploaded_files:
        # Ensure folder exists
        if not full_path or not full_path.exists():
            upload_path, folder_name = _create_upload_folder(project)
            project.upload_folder = folder_name
            full_path = Path(upload_path)
        
        st.markdown("**📥 กำลังอัพโหลด...**")
        progress_bar = st.progress(0)
        
        saved_files = []
        for i, uploaded_file in enumerate(uploaded_files):
            # Save file
            file_path = full_path / uploaded_file.name
            
            with open(file_path, "wb") as f:
                f.write(uploaded_file.getvalue())
            
            saved_files.append(str(file_path))
            
            # Update progress
            progress_bar.progress((i + 1) / len(uploaded_files))
        
        # Update project
        if not project.uploaded_files:
            project.uploaded_files = []
        project.uploaded_files.extend(saved_files)
        project.uploaded_files = list(set(project.uploaded_files))  # Remove duplicates
        
        st.session_state.current_project = project
        auto_save_project()
        
        st.success(f"✅ อัพโหลดสำเร็จ {len(uploaded_files)} ไฟล์!")
    
    st.markdown("---")
    
    # ===== UPLOADED FILES LIST =====
    st.subheader("📋 ไฟล์ที่อัพโหลดแล้ว")
    
    if project.uploaded_files:
        for i, file_path in enumerate(project.uploaded_files):
            file_name = Path(file_path).name
            file_exists = os.path.exists(file_path)
            
            col_file, col_status, col_delete = st.columns([4, 1, 1])
            
            with col_file:
                icon = "✅" if file_exists else "❌"
                st.markdown(f"{icon} **{file_name}**")
            
            with col_status:
                if file_exists:
                    file_size = os.path.getsize(file_path) / (1024 * 1024)  # MB
                    st.caption(f"{file_size:.1f} MB")
                else:
                    st.caption("ไม่พบไฟล์")
            
            with col_delete:
                if st.button("🗑️", key=f"del_file_{i}"):
                    if file_exists:
                        os.remove(file_path)
                    project.uploaded_files.remove(file_path)
                    st.session_state.current_project = project
                    auto_save_project()
                    st.rerun()
        
        st.markdown("---")
        st.metric("📊 ไฟล์ทั้งหมด", len(project.uploaded_files))
    else:
        st.info("📭 ยังไม่มีไฟล์ที่อัพโหลด")
    
    # ===== FOLDER CONTENTS =====
    if full_path and full_path.exists():
        with st.expander("📂 ดูไฟล์ทั้งหมดในโฟลเดอร์"):
            all_files = list(full_path.iterdir())
            if all_files:
                for f in all_files:
                    if f.is_file():
                        size_mb = f.stat().st_size / (1024 * 1024)
                        st.caption(f"📄 {f.name} - {size_mb:.1f} MB")
            else:
                st.caption("(ว่างเปล่า)")
    
    st.markdown("---")
    
    # ===== GOOGLE DRIVE LINK =====
    st.subheader("☁️ Google Drive (Optional)")
    
    drive_link = st.text_input(
        "🔗 ลิงก์ Google Drive Folder",
        value=project.drive_folder_link,
        placeholder="https://drive.google.com/drive/folders/...",
        key="step5_drive_link"
    )
    project.drive_folder_link = drive_link
    
    if drive_link:
        st.link_button("🌐 เปิด Google Drive", drive_link)
    
    st.markdown("---")
    
    # ===== ACTION BUTTONS =====
    col_save, col_complete = st.columns(2)
    
    with col_save:
        if st.button("💾 บันทึก", use_container_width=True):
            project.status = "step5_upload"
            project.workflow_step = 4
            st.session_state.current_project = project
            save_project(project)
            st.success("✅ บันทึกสำเร็จ!")
    
    with col_complete:
        if st.button("🎉 เสร็จสิ้นโปรเจค", type="primary", use_container_width=True):
            project.status = "completed"
            project.workflow_step = 5
            project.updated_at = datetime.now()
            st.session_state.current_project = project
            save_project(project)
            
            st.balloons()
            st.success("🎉 เย้! โปรเจคเสร็จสมบูรณ์!")
            
            # Option to create new project
            if st.button("➕ สร้างโปรเจคใหม่"):
                st.session_state.current_project = None
                st.session_state.page = STEP_PROJECT
                st.rerun()
    
    # Show completion summary
    if project.status == "completed":
        st.markdown("---")
        st.subheader("📊 สรุปโปรเจค")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("🎬 ฉากทั้งหมด", len(project.scenes) if project.scenes else 0)
        
        with col2:
            st.metric("📥 ไฟล์อัพโหลด", len(project.uploaded_files) if project.uploaded_files else 0)
        
        with col3:
            duration = sum(s.audio_duration for s in project.scenes) if project.scenes else 0
            st.metric("⏱️ ความยาวรวม", f"{duration:.1f}s")
