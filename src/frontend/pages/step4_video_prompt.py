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
from src.config.constants import STEP_SCRIPT, STEP_UPLOAD, VIDEO_TYPES, VIDEO_STYLES
from src.core.llm_config import LLM_PROVIDERS

# Try import prompt generator
try:
    # Lazy imports to speed up app load
    PROMPT_GEN_AVAILABLE = True
except ImportError:
    PROMPT_GEN_AVAILABLE = False

# Try import scene splitter
try:
    SCENE_SPLITTER_AVAILABLE = True
except ImportError:
    SCENE_SPLITTER_AVAILABLE = False

# Try import exporter
try:
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
    
    def _on_video_type_change():
        project.video_type = st.session_state.step4_video_type
        st.session_state.current_project = project
        auto_save_project()
    
    selected_video_type = st.radio(
        "เลือกประเภทวีดีโอ",
        options=list(video_type_options.keys()),
        format_func=lambda x: video_type_options.get(x, x),
        index=list(video_type_options.keys()).index(project.video_type) if project.video_type in video_type_options else 0,
        horizontal=True,
        key="step4_video_type",
        on_change=_on_video_type_change
    )
    project.video_type = selected_video_type
    
    # Video type specific settings
    if selected_video_type == "with_person":
        st.info("👤 วีดีโอแบบมีคน - จะเน้น Character Reference เพื่อความสม่ำเสมอ")
        
        def _on_character_change():
            project.character_reference = st.session_state.step4_character
            st.session_state.current_project = project
            auto_save_project()
        
        character_ref = st.text_area(
            "🧑 Character Reference",
            value=project.character_reference,
            height=80,
            placeholder="เช่น ผู้หญิงไทย อายุ 30 ต้นๆ ผมยาวสีดำ สวมเสื้อสีชมพู...",
            key="step4_character",
            on_change=_on_character_change
        )
        project.character_reference = character_ref
        
    elif selected_video_type == "no_person":
        st.info("📦 วีดีโอแบบไม่มีคน - เน้น Product/B-roll shots")
    else:
        st.info("🔀 Mixed - ผสมผสานทั้งสองแบบ")
    
    st.markdown("---")
    
    # ===== VIDEO STYLE SELECTION =====
    st.subheader("🎨 สไตล์วีดีโอ")
    st.caption("เลือกสไตล์ภาพที่ต้องการ — AI จะสร้าง prompt ตามสไตล์นี้")
    
    # Style descriptions for AI prompt generation (English)
    VIDEO_STYLE_DESCRIPTIONS = {
        "": "",
        "minimal_clean": "Minimal and clean aesthetic. White or neutral backgrounds, simple compositions, lots of negative space, soft shadows, modern and uncluttered look.",
        "nature_organic": "Natural and organic feel. Lush greenery, earth tones, warm sunlight filtering through leaves, wooden textures, outdoor settings with natural elements.",
        "cinematic_dark": "Cinematic dark mood. Deep shadows, rim lighting, dramatic contrast, moody atmosphere, dark backgrounds with selective lighting, film noir influence.",
        "warm_cozy": "Warm and cozy atmosphere. Soft golden lighting, warm color temperature, comfortable indoor settings, candles or warm lamps, intimate close-ups.",
        "neon_urban": "Neon urban nightscape. Vibrant neon lights, rain-slicked streets, cyberpunk influence, blue and pink color palette, city at night, reflective surfaces.",
        "pastel_soft": "Soft pastel aesthetic. Light pink, mint, lavender colors, dreamy soft focus, Korean-style flat lay, gentle gradients, airy and delicate mood.",
        "luxury_premium": "Luxury premium look. Gold accents, marble textures, rich deep colors, elegant lighting, high-end product photography style, sophisticated composition.",
        "vintage_retro": "Vintage retro style. Film grain, faded colors, warm sepia tones, 70s-80s aesthetic, analog photography look, nostalgic atmosphere.",
        "bright_energetic": "Bright and energetic. Vivid saturated colors, dynamic angles, high-key lighting, bold compositions, pop art influence, youthful energy.",
        "monochrome_bw": "Monochrome black and white. High contrast, dramatic shadows, artistic composition, classic photography, timeless and elegant, strong silhouettes.",
        "tropical_thai": "Tropical Thai aesthetic. Vibrant tropical colors, Thai cultural elements, ornate patterns, golden temple tones, lush tropical vegetation, warm exotic atmosphere.",
        "futuristic_tech": "Futuristic and high-tech. Holographic effects, clean lines, blue-white color scheme, digital interfaces, sleek surfaces, sci-fi atmosphere, glass and metal.",
    }
    
    style_options = {vs[0]: vs[1] for vs in VIDEO_STYLES}
    
    def _on_style_change():
        project.visual_theme = VIDEO_STYLE_DESCRIPTIONS.get(st.session_state.step4_video_style, "")
        st.session_state.current_project = project
        auto_save_project()
    
    # Find current index by matching description
    current_style_idx = 0
    for i, (key, _) in enumerate(VIDEO_STYLES):
        if VIDEO_STYLE_DESCRIPTIONS.get(key, "") == project.visual_theme:
            current_style_idx = i
            break
    
    selected_style = st.selectbox(
        "เลือกสไตล์ภาพ",
        options=list(style_options.keys()),
        format_func=lambda x: style_options.get(x, x),
        index=current_style_idx,
        key="step4_video_style",
        on_change=_on_style_change
    )
    project.visual_theme = VIDEO_STYLE_DESCRIPTIONS.get(selected_style, "")
    
    # Show preview of selected style
    if selected_style:
        st.info(f"🎯 AI จะสร้าง prompt ตามสไตล์: **{VIDEO_STYLE_DESCRIPTIONS[selected_style][:80]}...**")
    
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
                            from src.core.scene_splitter import SceneSplitter
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
        
        # Resume / Force-regenerate toggle
        force_regen = st.checkbox(
            "🔄 สร้างใหม่ทั้งหมด",
            value=False,
            key="step4_force_regen",
            help="ปิด = Resume ต่อจากฉากที่ค้าง | เปิด = สร้างใหม่ทั้งหมดตั้งแต่ต้น"
        )
        
        # Show resume status
        if project.scenes:
            done_count = sum(1 for s in project.scenes if s.veo_prompt and s.voice_tone)
            total_count_info = len(project.scenes)
            if done_count > 0 and done_count < total_count_info and not force_regen:
                st.info(f"⏩ Resume: {done_count}/{total_count_info} ฉากสำเร็จแล้ว")
        
        # ===== LLM PROVIDER SELECTOR =====
        st.markdown("---")
        st.markdown("**🤖 AI Model**")
        
        # Build provider options (available first, then unavailable)
        available_keys = [k for k, p in LLM_PROVIDERS.items() if p.is_available]
        unavailable_keys = [k for k, p in LLM_PROVIDERS.items() if not p.is_available]
        all_provider_keys = available_keys + unavailable_keys
        
        provider_labels = {}
        for key in all_provider_keys:
            p = LLM_PROVIDERS[key]
            if p.is_available:
                cost = p.models[0].cost_per_1k
                cost_label = "ฟรี" if cost == 0.0 else f"${cost}/1K"
                provider_labels[key] = f"✅ {p.name} ({cost_label})"
            else:
                provider_labels[key] = f"🔒 {p.name} (ไม่มี key)"
        
        default_idx = all_provider_keys.index("deepseek") if "deepseek" in all_provider_keys else 0
        
        selected_provider = st.selectbox(
            "เลือก Provider",
            options=all_provider_keys,
            format_func=lambda x: provider_labels.get(x, x),
            index=default_idx,
            key="step4_llm_provider"
        )
        
        # Model sub-selector
        provider_obj = LLM_PROVIDERS.get(selected_provider)
        selected_model = None
        if provider_obj:
            model_options = [(m.id, m.name) for m in provider_obj.models]
            selected_model = st.selectbox(
                "Model",
                options=[m[0] for m in model_options],
                format_func=lambda x: next((m[1] for m in model_options if m[0] == x), x),
                key="step4_llm_model"
            )
            st.caption(f"💪 {', '.join(provider_obj.strengths)}")
            if not provider_obj.is_available:
                st.warning(f"⚠️ ต้องตั้งค่า `{provider_obj.env_key}` ใน .env")
    
    # ===== HELPER: Build project context dict =====
    def _build_project_context():
        return {
            "visual_theme": project.visual_theme,
            "directors_note": project.directors_note,
            "aspect_ratio": project.aspect_ratio,
            "video_type": selected_video_type,
            "prompt_style_config": project.prompt_style_config,
            "platforms": getattr(project, 'platforms', []),
            "topic": project.topic or project.content_description or "",
            "content_category": getattr(project, 'content_category', ''),
            "video_format": getattr(project, 'video_format', ''),
            "content_goal": getattr(project, 'content_goal', ''),
            "target_audience": getattr(project, 'target_audience', ''),
        }
    
    # ===== HELPER: Create scenes from audio segments =====
    def _create_scenes_from_segments():
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
        return scenes
    
    # Determine mode
    is_per_prompt_mode = gen_mode == "📝 สร้างทีละ Prompt"
    
    # Generate button
    if project.audio_segments:
        if is_per_prompt_mode:
            # === PER-PROMPT MODE: Generate ONE scene at a time ===
            
            # Auto-prepare scenes if they don't exist
            if not project.scenes or len(project.scenes) != len(project.audio_segments):
                project.scenes = _create_scenes_from_segments()
                st.session_state.current_project = project
                auto_save_project()
            
            # Find next ungenerated scene
            next_scene_idx = None
            for i, s in enumerate(project.scenes):
                if not s.veo_prompt:
                    next_scene_idx = i
                    break
            
            generated_count = sum(1 for s in project.scenes if s.veo_prompt)
            total_count = len(project.scenes)
            
            if next_scene_idx is not None:
                next_scene = project.scenes[next_scene_idx]
                st.info(f"📝 สร้างทีละ Prompt — สร้างแล้ว **{generated_count}/{total_count}** ฉาก")
                
                # Show preview of next scene to generate
                st.caption(f"🎯 ฉากถัดไป: **ฉาก {next_scene.order}** — {next_scene.narration_text[:60]}...")
                
                if st.button(f"✨ สร้าง Prompt ฉาก {next_scene.order}", type="primary", use_container_width=True):
                    if provider_obj and not provider_obj.is_available:
                        st.error(f"❌ {provider_obj.name} ยังไม่มี API Key — กรุณาตั้งค่า `{provider_obj.env_key}` ใน .env")
                    else:
                        try:
                            prov_name = provider_obj.name if provider_obj else 'AI'
                            with st.spinner(f"🔄 กำลังสร้าง Prompt ฉาก {next_scene.order} ด้วย {prov_name}..."):
                                from src.core.prompt_generator import VeoPromptGenerator
                                prompt_gen = VeoPromptGenerator(
                                    character_reference=project.character_reference,
                                    enable_qa=enable_qa,
                                    provider=selected_provider,
                                    model=selected_model,
                                )
                                project_context = _build_project_context()

                                # Build continuity context from previous scene (if any)
                                prev_summary = ""
                                prev_narration = ""
                                nxt_narration = ""
                                if next_scene_idx > 0:
                                    prev = project.scenes[next_scene_idx - 1]
                                    if prev.veo_prompt:
                                        prev_summary = prev.veo_prompt[:250]
                                    prev_narration = prev.narration_text
                                if next_scene_idx < len(project.scenes) - 1:
                                    nxt_narration = project.scenes[next_scene_idx + 1].narration_text

                                # Generate ONLY this single scene — uses dedicated method, nothing else touched
                                prompt_gen.generate_single_scene(
                                    scene=next_scene,
                                    scene_index=next_scene_idx,
                                    total_scenes=len(project.scenes),
                                    character=project.character_reference,
                                    project_context=project_context,
                                    previous_scene_summary=prev_summary,
                                    previous_narration=prev_narration,
                                    next_narration=nxt_narration,
                                )

                                st.session_state.current_project = project
                                auto_save_project()
                                st.success(f"✅ สร้างฉาก {next_scene.order} สำเร็จ! ({generated_count + 1}/{total_count})")
                                st.rerun()
                        except Exception as e:
                            st.error(f"❌ สร้าง Prompt ไม่สำเร็จ: {e}")
                            st.info("💡 ลองตรวจสอบ API Key หรือลองเปลี่ยน Provider")
            else:
                st.success(f"🎉 สร้างครบทั้ง {total_count} ฉากแล้ว!")
        else:
            # === ALL-AT-ONCE MODE ===
            if st.button("🎬 สร้าง Veo Prompts ทั้งหมด", type="primary", use_container_width=True):
                if not PROMPT_GEN_AVAILABLE:
                    st.error("❌ Prompt Generator ไม่พร้อมใช้งาน")
                elif provider_obj and not provider_obj.is_available:
                    st.error(f"❌ {provider_obj.name} ยังไม่มี API Key — กรุณาตั้งค่า `{provider_obj.env_key}` ใน .env")
                else:
                    try:
                        prov_name = provider_obj.name if provider_obj else 'AI'
                        with st.spinner(f"🔄 กำลังสร้าง Prompts ด้วย {prov_name}..."):
                            from src.core.prompt_generator import VeoPromptGenerator
                            prompt_gen = VeoPromptGenerator(
                                character_reference=project.character_reference,
                                enable_qa=enable_qa,
                                provider=selected_provider,
                                model=selected_model,
                            )
                            
                            scenes = _create_scenes_from_segments()
                            
                            # Merge existing prompts into new scene list if resuming
                            if not force_regen and project.scenes:
                                scene_map = {s.order: s for s in project.scenes}
                                for s in scenes:
                                    existing = scene_map.get(s.order)
                                    if existing:
                                        s.veo_prompt = existing.veo_prompt
                                        s.voiceover_prompt = existing.voiceover_prompt
                                        s.voice_tone = existing.voice_tone
                                        s.quality_score = existing.quality_score
                                        s.quality_suggestions = existing.quality_suggestions
                                        s.video_generated = existing.video_generated
                            
                            project_context = _build_project_context()
                            
                            # Progress tracking
                            progress_bar = st.progress(0.0)
                            status_text = st.empty()
                            
                            generated_scenes = []
                            
                            generator = prompt_gen.generate_all_prompts_generator(
                                scenes,
                                project.character_reference,
                                project_context,
                                force_regenerate=force_regen
                            )
                            
                            for idx, total, scene in generator:
                                percentage = idx / total
                                progress_bar.progress(min(percentage, 1.0))
                                status_text.text(f"⏳ กำลังสร้างฉากที่ {idx}/{total} ({project_context.get('video_type', '')})...")
                                generated_scenes.append(scene)
                            
                            status_text.empty()
                            progress_bar.empty()
                            
                            project.scenes = generated_scenes
                            st.session_state.current_project = project
                            auto_save_project()
                            
                            st.success(f"✅ สร้างสำเร็จ {len(generated_scenes)} Prompts! (ใช้ {prompt_gen.provider_name}/{prompt_gen.active_model})")
                            st.rerun()
                            
                    except Exception as e:
                        st.error(f"❌ สร้าง Prompt ไม่สำเร็จ: {e}")
                        st.info("💡 ลองตรวจสอบ: 1) มีบทพูดจาก Step 3 2) API Key ถูกต้อง 3) ลองเปลี่ยน Provider 4) ลองกดใหม่อีกครั้ง")
    
    st.markdown("---")
    
    # ===== DISPLAY PROMPTS =====
    if project.scenes:
        st.subheader(f"📋 Veo Prompts ({len(project.scenes)} ฉาก)")
        
        # Export buttons
        col_export1, col_export2, col_export3 = st.columns(3)
        
        with col_export1:
            if EXPORTER_AVAILABLE:
                from src.core.exporter import ProjectExporter
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
                st.toast("💡 กดไอคอน 📋 มุมขวาบนของกล่องข้อความ หรือกดดาวน์โหลด", icon="💡")
        
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
                    
                    # Per-prompt mode: individual generate button
                    if is_per_prompt_mode:
                        st.markdown("---")
                        has_prompt = bool(scene.veo_prompt)
                        btn_label = "🔄 สร้างใหม่" if has_prompt else "✨ สร้าง Prompt"
                        btn_type = "secondary" if has_prompt else "primary"
                        
                        if st.button(btn_label, key=f"gen_single_{scene.scene_id}", type=btn_type, use_container_width=True):
                            if provider_obj and not provider_obj.is_available:
                                st.error(f"❌ ไม่มี API Key")
                            else:
                                try:
                                    with st.spinner(f"🔄 สร้าง Prompt ฉาก {scene.order}..."):
                                        from src.core.prompt_generator import VeoPromptGenerator
                                        prompt_gen = VeoPromptGenerator(
                                            character_reference=project.character_reference,
                                            enable_qa=enable_qa,
                                            provider=selected_provider,
                                            model=selected_model,
                                        )
                                        project_context = _build_project_context()

                                        # Get scene index for continuity context
                                        scene_idx = next((i for i, s in enumerate(project.scenes) if s.scene_id == scene.scene_id), 0)
                                        total_scenes = len(project.scenes)

                                        # Build context from neighboring scenes
                                        prev_summary = ""
                                        prev_narration = ""
                                        nxt_narration = ""
                                        if scene_idx > 0:
                                            prev_scene = project.scenes[scene_idx - 1]
                                            if prev_scene.veo_prompt:
                                                prev_summary = prev_scene.veo_prompt[:250]
                                            prev_narration = prev_scene.narration_text
                                        if scene_idx < total_scenes - 1:
                                            nxt_narration = project.scenes[scene_idx + 1].narration_text

                                        # Generate ONLY this single scene — uses dedicated method, nothing else touched
                                        prompt_gen.generate_single_scene(
                                            scene=scene,
                                            scene_index=scene_idx,
                                            total_scenes=total_scenes,
                                            character=project.character_reference,
                                            project_context=project_context,
                                            previous_scene_summary=prev_summary,
                                            previous_narration=prev_narration,
                                            next_narration=nxt_narration,
                                        )

                                        st.session_state.current_project = project
                                        auto_save_project()
                                        st.success(f"✅ สร้างฉาก {scene.order} สำเร็จ!")
                                        st.rerun()
                                except Exception as e:
                                    st.error(f"❌ ไม่สำเร็จ: {e}")
                
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
                            col_copy, col_dl = st.columns(2)
                            with col_copy:
                                if st.button("📋 คัดลอก Video Style", key=f"copy_veo_{scene.order}", use_container_width=True):
                                    copy_to_clipboard(scene.veo_prompt, f"veo_{scene.order}")
                            with col_dl:
                                st.download_button("💾 ดาวน์โหลด", data=scene.veo_prompt, file_name=f"scene{scene.order}_video_style.txt", mime="text/plain", key=f"dl_veo_{scene.order}", use_container_width=True)
                        else:
                            st.warning("ยังไม่มี Video Style Prompt")
                    
                    # --- Tab 2: Thai Voiceover ---
                    with tab2:
                        st.markdown("**🎤 เสียงพากย์ไทย**")
                        st.caption("บทพากย์เสียงภาษาไทย · อ่านตรงๆ ไม่มีอิโมชัน")
                        if scene.voiceover_prompt:
                            st.success(scene.voiceover_prompt)
                            col_copy, col_dl = st.columns(2)
                            with col_copy:
                                if st.button("📋 คัดลอก เสียงพากย์", key=f"copy_vo_{scene.order}", use_container_width=True):
                                    copy_to_clipboard(scene.voiceover_prompt, f"vo_{scene.order}")
                            with col_dl:
                                st.download_button("💾 ดาวน์โหลด", data=scene.voiceover_prompt, file_name=f"scene{scene.order}_voiceover.txt", mime="text/plain", key=f"dl_vo_{scene.order}", use_container_width=True)
                        else:
                            st.warning("ยังไม่มีเสียงพากย์")
                    
                    # --- Tab 3: Speaking Style ---
                    with tab3:
                        st.markdown("**🎭 Speaking Style / สไตล์การพูด**")
                        st.caption("Voice direction ภาษาอังกฤษ · Tone, Pacing, Emotion")
                        if scene.voice_tone:
                            st.code(scene.voice_tone, language="text")
                            col_copy, col_dl = st.columns(2)
                            with col_copy:
                                if st.button("📋 คัดลอก Speaking Style", key=f"copy_tone_{scene.order}", use_container_width=True):
                                    copy_to_clipboard(scene.voice_tone, f"tone_{scene.order}")
                            with col_dl:
                                st.download_button("💾 ดาวน์โหลด", data=scene.voice_tone, file_name=f"scene{scene.order}_speaking_style.txt", mime="text/plain", key=f"dl_tone_{scene.order}", use_container_width=True)
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
                        
                        combined_text = "\n\n".join(combined_parts) if combined_parts else ""
                        
                        if combined_text:
                            st.code(combined_text, language="text")
                            col_copy, col_dl = st.columns(2)
                            with col_copy:
                                if st.button("📋 คัดลอก Prompt ทั้งหมด", key=f"copy_all_{scene.order}", use_container_width=True):
                                    copy_to_clipboard(combined_text, f"all_{scene.order}")
                            with col_dl:
                                st.download_button("💾 ดาวน์โหลด", data=combined_text, file_name=f"scene{scene.order}_full_prompt.txt", mime="text/plain", key=f"dl_all_{scene.order}", use_container_width=True)
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
