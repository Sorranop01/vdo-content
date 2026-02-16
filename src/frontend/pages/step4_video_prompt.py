"""
Step 4: สร้าง Prompt Vdo (Video Prompt Generation)
Video type selection, Veo 3 prompt generation in English
"""
import streamlit as st
import os

# Imports
from src.core.models import Scene
from src.shared.project_manager import save_project
from src.frontend.utils import show_back_button, auto_save_project, copy_to_clipboard, export_all_prompts, show_step_guard
from src.config.constants import STEP_SCRIPT, STEP_UPLOAD, VIDEO_TYPES

# Try import prompt generator
try:
    from src.core.prompt_generator import VeoPromptGenerator
    PROMPT_GEN_AVAILABLE = True
except ImportError:
    PROMPT_GEN_AVAILABLE = False

# Try import scene splitter
try:
    from src.core.scene_splitter import SceneSplitter
    SCENE_SPLITTER_AVAILABLE = True
except ImportError:
    SCENE_SPLITTER_AVAILABLE = False

# Try import exporter
try:
    from src.core.exporter import ProjectExporter
    EXPORTER_AVAILABLE = True
except ImportError:
    EXPORTER_AVAILABLE = False


def render():
    """Step 4: สร้าง Prompt Vdo"""
    # Back button
    if st.button("← ย้อนกลับ: บทพูด"):
        st.session_state.page = STEP_SCRIPT
        st.rerun()
    
    st.title("4️⃣ สร้าง Prompt Vdo")
    
    if not show_step_guard(3):
        return
    
    project = st.session_state.current_project
    st.caption(f"📁 โปรเจค: **{project.title}**")
    
    st.markdown("---")
    
    # ===== VIDEO TYPE SELECTION =====
    st.subheader("🎬 ประเภทวีดีโอ")
    
    video_type_options = {vt[0]: vt[1] for vt in VIDEO_TYPES}
    
    selected_video_type = st.radio(
        "เลือกประเภทวีดีโอ",
        options=list(video_type_options.keys()),
        format_func=lambda x: video_type_options.get(x, x),
        index=list(video_type_options.keys()).index(project.video_type) if project.video_type in video_type_options else 0,
        horizontal=True,
        key="step4_video_type"
    )
    project.video_type = selected_video_type
    
    # Video type specific settings
    if selected_video_type == "with_person":
        st.info("👤 วีดีโอแบบมีคน - จะเน้น Character Reference เพื่อความสม่ำเสมอ")
        
        character_ref = st.text_area(
            "🧑 Character Reference",
            value=project.character_reference,
            height=80,
            placeholder="เช่น ผู้หญิงไทย อายุ 30 ต้นๆ ผมยาวสีดำ สวมเสื้อสีชมพู...",
            key="step4_character"
        )
        project.character_reference = character_ref
        
    elif selected_video_type == "no_person":
        st.info("📦 วีดีโอแบบไม่มีคน - เน้น Product/B-roll shots")
    else:
        st.info("🔀 Mixed - ผสมผสานทั้งสองแบบ")
    
    st.markdown("---")
    
    # ===== PROMPT GENERATION =====
    st.subheader("✨ สร้าง Veo Prompts")
    
    col_gen, col_options = st.columns([2, 1])
    
    with col_gen:
        # Check if we have audio segments
        if not project.audio_segments:
            # Offer scene splitter as alternative if script exists
            if project.full_script and SCENE_SPLITTER_AVAILABLE:
                st.info("📝 มีบทพูดแล้ว — สามารถซอยเป็นฉากอัตโนมัติได้")
                
                col_split, col_dur = st.columns([2, 1])
                with col_dur:
                    max_dur = st.slider(
                        "⏱️ ความยาว/ฉาก (วินาที)", 
                        min_value=3.0, max_value=15.0, value=8.0, step=0.5,
                        key="step4_max_duration"
                    )
                
                with col_split:
                    if st.button("✂️ ซอย Script เป็นฉาก", type="primary", use_container_width=True):
                        try:
                            splitter = SceneSplitter(max_duration=max_dur, language="th")
                            scenes = splitter.split_script(
                                project.full_script,
                                default_style=project.default_style or "cinematic"
                            )
                            
                            # Convert scenes to audio_segments format for compatibility
                            from src.core.models import AudioSegment
                            segments = []
                            cumulative_time = 0.0
                            for scene in scenes:
                                seg = AudioSegment(
                                    order=scene.order,
                                    text_content=scene.narration_text,
                                    start_time=cumulative_time,
                                    end_time=cumulative_time + scene.estimated_duration,
                                    duration=scene.estimated_duration
                                )
                                segments.append(seg)
                                cumulative_time += scene.estimated_duration
                            
                            project.audio_segments = segments
                            st.session_state.current_project = project
                            auto_save_project()
                            
                            stats = splitter.get_stats(scenes)
                            st.success(f"✅ ซอยสำเร็จ! {stats['total_scenes']} ฉาก (รวม {stats['total_duration']:.1f} วินาที)")
                            st.rerun()
                        except Exception as e:
                            st.error(f"❌ ซอย Script ไม่สำเร็จ: {e}")
                            st.info("💡 ลองปรับความยาวต่อฉากแล้วกดใหม่")
            else:
                st.warning("⚠️ ยังไม่มีฉาก — กรุณาซอยคลิปเสียงใน Step 3 หรือเขียน Script ก่อน")
                
                if st.button("← กลับไป Step 3"):
                    st.session_state.page = STEP_SCRIPT
                    st.rerun()
        else:
            st.success(f"✅ พร้อมสร้าง {len(project.audio_segments)} Prompts")
            
            # Drift verification: compare segment total vs actual audio
            if project.audio_path and os.path.exists(project.audio_path):
                segment_total = sum(seg.duration for seg in project.audio_segments)
                try:
                    from pydub import AudioSegment as PydubCheck
                    actual_audio = PydubCheck.from_file(project.audio_path)
                    actual_length = len(actual_audio) / 1000.0
                    drift = abs(actual_length - segment_total)
                    if drift > 1.0:
                        st.warning(
                            f"⚠️ **Sync Warning:** ฉากรวม {segment_total:.1f}s "
                            f"แต่ไฟล์เสียงยาว {actual_length:.1f}s "
                            f"(ต่างกัน {drift:.1f}s) — ซับไตเติ้ลอาจเลื่อน"
                        )
                    else:
                        st.caption(f"🔄 Sync OK: ฉากรวม {segment_total:.1f}s ≈ เสียง {actual_length:.1f}s")
                except ImportError:
                    st.caption(f"📊 ฉากรวม {segment_total:.1f}s (ติดตั้ง pydub เพื่อตรวจสอบ sync)")
                except Exception:
                    pass
    
    with col_options:
        # Advanced options
        gen_mode = st.selectbox(
            "โหมดสร้าง",
            ["🚀 สร้างทั้งหมดพร้อมกัน", "📝 สร้างทีละ Prompt"],
            key="step4_gen_mode"
        )
        
        enable_qa = st.checkbox("🔍 QA Review (AI ตรวจสอบ)", value=False)
    
    # Generate button
    if project.audio_segments:
        if st.button("🎬 สร้าง Veo Prompts", type="primary", use_container_width=True):
            if not PROMPT_GEN_AVAILABLE:
                st.error("❌ Prompt Generator ไม่พร้อมใช้งาน")
            else:
                try:
                    with st.spinner("🔄 กำลังสร้าง Prompts..."):
                        prompt_gen = VeoPromptGenerator(
                            character_reference=project.character_reference,
                            enable_qa=enable_qa
                        )
                        
                        # Create scenes from audio segments
                        scenes = []
                        for seg in project.audio_segments:
                            scene = Scene(
                                order=seg.order,
                                start_time=seg.start_time,
                                end_time=seg.end_time,
                                narration_text=seg.text_content,
                                visual_style=project.default_style,
                                subject_description=project.character_reference if selected_video_type == "with_person" else "",
                                audio_synced=True
                            )
                            scene.estimated_duration = seg.duration
                            scenes.append(scene)
                        
                        # Project context for prompt generation
                        project_context = {
                            "visual_theme": project.visual_theme,
                            "directors_note": project.directors_note,
                            "aspect_ratio": project.aspect_ratio,
                            "video_type": selected_video_type,
                            "prompt_style_config": project.prompt_style_config
                        }
                        
                        scenes = prompt_gen.generate_all_prompts(
                            scenes,
                            project.character_reference,
                            project_context
                        )
                        
                        project.scenes = scenes
                        st.session_state.current_project = project
                        auto_save_project()
                        
                        st.success(f"✅ สร้างสำเร็จ {len(scenes)} Prompts!")
                        st.rerun()
                        
                except Exception as e:
                    st.error(f"❌ สร้าง Prompt ไม่สำเร็จ: {e}")
                    st.info("💡 ลองตรวจสอบ: 1) มีบทพูดจาก Step 3 2) API Key ถูกต้อง 3) ลองกดใหม่อีกครั้ง")
    
    st.markdown("---")
    
    # ===== DISPLAY PROMPTS =====
    if project.scenes:
        st.subheader(f"📋 Veo Prompts ({len(project.scenes)} ฉาก)")
        
        # Export buttons
        col_export1, col_export2, col_export3 = st.columns(3)
        
        with col_export1:
            if EXPORTER_AVAILABLE:
                exporter = ProjectExporter()
                prompts_text = exporter.export_all_prompts_text(project)
            else:
                prompts_text = "\n\n---\n\n".join([
                    f"Scene {s.order}:\n{s.veo_prompt}"
                    for s in project.scenes
                ])
            
            st.download_button(
                "📥 ดาวน์โหลด Prompts",
                data=prompts_text,
                file_name=f"{project.title}_prompts.txt",
                mime="text/plain",
                use_container_width=True
            )
        
        with col_export2:
            if st.button("📋 คัดลอกทั้งหมด", use_container_width=True):
                copy_to_clipboard(prompts_text, "all_prompts")
        
        with col_export3:
            completed = sum(1 for s in project.scenes if s.video_generated)
            st.metric("ความคืบหน้า", f"{completed}/{len(project.scenes)}")
        
        # Link to Veo 3
        st.link_button(
            "🌟 เปิด Veo 3",
            "https://labs.google/fx/tools/video-fx",
            type="primary",
            use_container_width=True
        )
        
        st.markdown("---")
        
        # Display each scene
        for scene in project.scenes:
            status_icon = "✅" if scene.video_generated else "⬜"
            
            with st.expander(
                f"{status_icon} ฉาก {scene.order}: [{scene.time_range}] - {scene.narration_text[:40]}...",
                expanded=not scene.video_generated
            ):
                # Timing sidebar
                col_main, col_side = st.columns([4, 1])
                
                with col_side:
                    st.markdown("**⏱️ Veo 3: 8 วินาที**")
                    st.caption(f"บทพูด: {scene.audio_duration:.1f}s")
                    st.caption(f"Time: {scene.time_range}")
                    st.markdown("---")
                    scene.video_generated = st.checkbox(
                        "✅ สร้างแล้ว",
                        value=scene.video_generated,
                        key=f"gen_{scene.scene_id}"
                    )
                
                with col_main:
                    # 4 Tabs for the 4 prompt sections
                    tab1, tab2, tab3, tab4 = st.tabs([
                        "🎬 สไตล์วีดีโอ",
                        "🎤 เสียงพากย์ไทย",
                        "🎭 สไตล์การพูด",
                        "📦 รวม Prompt"
                    ])
                    
                    # --- Tab 1: Video Style Prompt ---
                    with tab1:
                        st.markdown("**🎬 Video Style Prompt**")
                        st.caption("สไตล์วีดีโอ · โทนสี · สิ่งที่วีดีโอสื่อ")
                        if scene.veo_prompt:
                            st.code(scene.veo_prompt, language="text")
                            if st.button("📋 คัดลอก Video Style", key=f"copy_veo_{scene.order}", use_container_width=True):
                                copy_to_clipboard(scene.veo_prompt, f"veo_{scene.order}")
                        else:
                            st.warning("ยังไม่มี Video Style Prompt")
                    
                    # --- Tab 2: Thai Voiceover ---
                    with tab2:
                        st.markdown("**🎤 เสียงพากย์ไทย**")
                        st.caption("บทพากย์เสียงภาษาไทย · อ่านตรงๆ ไม่มีอิโมชัน")
                        if scene.voiceover_prompt:
                            st.success(scene.voiceover_prompt)
                            if st.button("📋 คัดลอก เสียงพากย์", key=f"copy_vo_{scene.order}", use_container_width=True):
                                copy_to_clipboard(scene.voiceover_prompt, f"vo_{scene.order}")
                        else:
                            st.warning("ยังไม่มีเสียงพากย์")
                    
                    # --- Tab 3: Speaking Style ---
                    with tab3:
                        st.markdown("**🎭 Speaking Style / สไตล์การพูด**")
                        st.caption("Voice direction ภาษาอังกฤษ · Tone, Pacing, Emotion")
                        if scene.voice_tone:
                            st.code(scene.voice_tone, language="text")
                            if st.button("📋 คัดลอก Speaking Style", key=f"copy_tone_{scene.order}", use_container_width=True):
                                copy_to_clipboard(scene.voice_tone, f"tone_{scene.order}")
                        else:
                            st.warning("ยังไม่มี Speaking Style")
                    
                    # --- Tab 4: Combined Prompt ---
                    with tab4:
                        st.markdown("**📦 รวม Prompt ทั้งหมด**")
                        st.caption("Video Style + เสียงพากย์ + Speaking Style ในที่เดียว")
                        
                        combined_parts = []
                        
                        if scene.veo_prompt:
                            combined_parts.append(f"[🎬 Video Style Prompt]\n{scene.veo_prompt}")
                        
                        if scene.voiceover_prompt:
                            combined_parts.append(f"[🎤 เสียงพากย์ไทย]\n{scene.voiceover_prompt}")
                        
                        if scene.voice_tone:
                            combined_parts.append(f"[🎭 Speaking Style]\n{scene.voice_tone}")
                        
                        combined_text = "\n\n" + ("-" * 40 + "\n\n").join(combined_parts) if combined_parts else ""
                        
                        if combined_text:
                            st.code(combined_text, language="text")
                            if st.button("📋 คัดลอก Prompt ทั้งหมด", key=f"copy_all_{scene.order}", use_container_width=True):
                                copy_to_clipboard(combined_text, f"all_{scene.order}")
                        else:
                            st.warning("ยังไม่มี Prompt")
        
        # Progress bar
        completed = sum(1 for s in project.scenes if s.video_generated)
        st.progress(completed / len(project.scenes) if project.scenes else 0)
    
    st.markdown("---")
    
    # ===== ACTION BUTTONS =====
    col_save, col_next = st.columns(2)
    
    with col_save:
        if st.button("💾 บันทึก Prompt", use_container_width=True):
            project.status = "step4_prompt"
            project.workflow_step = 3
            st.session_state.current_project = project
            save_project(project)
            st.success("✅ บันทึก Prompt สำเร็จ!")
    
    with col_next:
        if st.button("➡️ ถัดไป: อัพโหลดไฟล์", type="primary", use_container_width=True):
            project.status = "step5_upload"
            project.workflow_step = 4
            st.session_state.current_project = project
            save_project(project)
            st.session_state.page = STEP_UPLOAD
            st.rerun()
