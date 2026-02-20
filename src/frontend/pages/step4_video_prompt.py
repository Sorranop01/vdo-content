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
    st.subheader("📹 เลือกประเภทวิดีโอ")
    
    video_type_options = {vt[0]: vt[1] for vt in VIDEO_TYPES}
    
    def _on_video_type_change():
        project.video_type = st.session_state.step4_video_type
        st.session_state.current_project = project
        auto_save_project()
    
    selected_video_type = st.radio(
        "ประเภทวิดีโอที่ต้องการสร้าง",
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
        st.info("👤 แบบมีตัวละครดำเนินเรื่อง - กรุณาระบุ Character Reference เพื่อความต่อเนื่องของตัวละคร")
        
        def _on_character_change():
            project.character_reference = st.session_state.step4_character
            st.session_state.current_project = project
            auto_save_project()
        
        character_ref = st.text_area(
            "📝 Character Reference",
            value=project.character_reference,
            height=80,
            placeholder="เช่น ผู้หญิงไทย อายุ 30 ปี ผมยาวสีดำ ใส่เสื้อยืดสีขาว ยืนอยู่ในห้องครัวสไตล์โมเดิร์น...",
            key="step4_character",
            on_change=_on_character_change
        )
        project.character_reference = character_ref
        
    elif selected_video_type == "no_person":
        st.info("🏞️ แบบไม่มีคน - เน้นภาพบรรยากาศ สินค้า หรือ B-roll")
    else:
        st.info("🔄 แบบผสม - ให้ AI ตัดสินใจตามความเหมาะสมของแต่ละฉาก")
    
    st.markdown("---")
    
    # ===== VIDEO STYLE SELECTION =====
    st.subheader("🎨 เลือกสไตล์ภาพ")
    st.caption("เลือกสไตล์ภาพที่ต้องการ เพื่อให้ AI สร้าง prompt ได้ตรงตามอารมณ์ของวิดีโอ")
    
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
        "สไตล์ภาพ (Visual Style)",
        options=list(style_options.keys()),
        format_func=lambda x: style_options.get(x, x),
        index=current_style_idx,
        key="step4_video_style",
        on_change=_on_style_change
    )
    project.visual_theme = VIDEO_STYLE_DESCRIPTIONS.get(selected_style, "")
    
    # Show preview of selected style
    if selected_style:
        st.info(f"💡 AI จะสร้าง prompt โดยอิงจากสไตล์: **{VIDEO_STYLE_DESCRIPTIONS[selected_style][:80]}...**")
    
    st.markdown("---")
    
    # ===== PROMPT GENERATION =====
    st.subheader("🤖 สร้าง Veo Prompts")
    
    col_gen, col_options = st.columns([2, 1])
    
    with col_gen:
        # Check if we have audio segments
        if not project.audio_segments:
            # Offer scene splitter as alternative if script exists
            if project.full_script and SCENE_SPLITTER_AVAILABLE:
                st.info("⚠️ ยังไม่ได้แบ่งฉาก (Scene Splitting) แต่มีบทพูดอยู่ คุณต้องการแบ่งฉากตอนนี้เลยหรือไม่?")
                
                col_split, col_dur = st.columns([2, 1])
                with col_dur:
                    max_dur = st.slider(
                        "ความยาวสูงสุดต่อฉาก (วินาที)", 
                        min_value=3.0, max_value=15.0, value=8.0, step=0.5,
                        key="step4_max_duration"
                    )
                
                with col_split:
                    if st.button("✂️ แบ่งฉากจาก Script อัตโนมัติ", type="primary", use_container_width=True):
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
                            st.success(f"✅ แบ่งฉากสำเร็จ! {stats['total_scenes']} ฉาก (รวม {stats['total_duration']:.1f} วินาที)")
                            st.rerun()
                        except Exception as e:
                            st.error(f"❌ แบ่งฉากจาก Script ไม่สำเร็จ: {e}")
                            st.info("💡 ลองกลับไปทำ Step 3 เพื่อตรวจสอบบทพูดอีกครั้ง")
            else:
                st.warning("⚠️ ยังไม่มีข้อมูลฉากเสียง กรุณากลับไป Step 3 เพื่อสร้าง Script หรืออัพโหลดไฟล์เสียงก่อน")
                
                if st.button("← กลับไป Step 3"):
                    st.session_state.page = STEP_SCRIPT
                    st.rerun()
        else:
            st.success(f"✅ พร้อมสร้าง Prompt สำหรับ {len(project.audio_segments)} ฉาก")
            
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
                            f"⚠️ **Sync Warning:** ความยาวรวม {segment_total:.1f}s "
                            f"ไม่ตรงกับไฟล์เสียงจริง {actual_length:.1f}s "
                            f"(ต่างกัน {drift:.1f}s) อาจทำให้ซับไตเติลไม่ตรงกับเสียง"
                        )
                    else:
                        st.caption(f"✅ Sync OK: ความยาวรวม {segment_total:.1f}s ≈ ไฟล์เสียง {actual_length:.1f}s")
                except ImportError:
                    st.caption(f"ℹ️ ความยาวรวม {segment_total:.1f}s (ติดตั้ง pydub เพื่อตรวจสอบ sync)")
                except Exception:
                    pass
    
    with col_options:
        # Advanced options
        gen_mode = st.selectbox(
            "โหมดการสร้าง",
            ["⚡ สร้างทีละฉาก (แนะนำ)", "🚀 สร้างรวดเดียวทุกฉาก"],
            key="step4_gen_mode"
        )
        
        enable_qa = st.checkbox("✨ QA Review (AI ตรวจสอบคุณภาพ)", value=False)
        
        # Resume / Force-regenerate toggle
        force_regen = st.checkbox(
            "🔄 สร้างใหม่ทับของเดิมทั้งหมด",
            value=False,
            key="step4_force_regen",
            help="ไม่เลือก = Resume สร้างต่อจากที่ค้างไว้ | เลือก = สร้างใหม่ทั้งหมดทับของเดิม"
        )
        
        # Show resume status
        if project.scenes:
            done_count = sum(1 for s in project.scenes if s.veo_prompt and s.voice_tone)
            total_count_info = len(project.scenes)
            if done_count > 0 and done_count < total_count_info and not force_regen:
                st.info(f"ℹ️ Resume: {done_count}/{total_count_info} ฉากสร้างเสร็จแล้ว")
        
        # ===== LLM PROVIDER SELECTOR =====
        st.markdown("---")
        st.markdown("**🧠 AI Model**")
        
        # Build provider options (available first, then unavailable)
        available_keys = [k for k, p in LLM_PROVIDERS.items() if p.is_available]
        unavailable_keys = [k for k, p in LLM_PROVIDERS.items() if not p.is_available]
        all_provider_keys = available_keys + unavailable_keys
        
        provider_labels = {}
        for key in all_provider_keys:
            p = LLM_PROVIDERS[key]
            if p.is_available:
                cost = p.models[0].cost_per_1k
                cost_label = "Free/Low" if cost == 0.0 else f"${cost}/1K"
                provider_labels[key] = f"✅ {p.name} ({cost_label})"
            else:
                provider_labels[key] = f"❌ {p.name} (ไม่มี API Key)"
        
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
            st.caption(f"ℹ️ {', '.join(provider_obj.strengths)}")
            if not provider_obj.is_available:
                st.warning(f"⚠️ กรุณาใส่ `{provider_obj.env_key}` ในไฟล์ .env")
    
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
    is_per_prompt_mode = gen_mode == "⚡ สร้างทีละฉาก (แนะนำ)"
    
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
                st.info(f"⏳ กำลังสร้าง Prompt สำหรับฉากถัดไป **{generated_count}/{total_count}** ฉาก")
                
                # Show preview of next scene to generate
                st.caption(f"🎬 ฉากต่อไป: **ฉากที่ {next_scene.order}** - {next_scene.narration_text[:60]}...")
                
                if st.button(f"✨ สร้าง Prompt ฉากที่ {next_scene.order}", type="primary", use_container_width=True):
                    if provider_obj and not provider_obj.is_available:
                        st.error(f"❌ {provider_obj.name} ไม่พร้อมใช้งาน (ขาด API Key) กรุณาตรวจสอบ `{provider_obj.env_key}` ใน .env")
                    else:
                        try:
                            prov_name = provider_obj.name if provider_obj else 'AI'
                            with st.spinner(f"🔄 กำลังสร้าง Prompt ฉากที่ {next_scene.order} ด้วย {prov_name}..."):
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

                                # Generate ONLY this single scene
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
                                st.success(f"✅ สร้าง Prompt ฉากที่ {next_scene.order} สำเร็จ! ({generated_count + 1}/{total_count})")
                                st.rerun()
                        except Exception as e:
                            st.error(f"❌ สร้าง Prompt ไม่สำเร็จ: {e}")
                            st.info("💡 ลองตรวจสอบ API Key หรือลองเปลี่ยน Provider")
            else:
                st.success(f"🎉 สร้าง Prompt ครบทั้ง {total_count} ฉากแล้ว!")
        else:
            # === ALL-AT-ONCE MODE ===
            if st.button("🚀 สร้าง Veo Prompts ทั้งหมดรวดเดียว", type="primary", use_container_width=True):
                if not PROMPT_GEN_AVAILABLE:
                    st.error("❌ Prompt Generator ไม่พร้อมใช้งาน")
                elif provider_obj and not provider_obj.is_available:
                    st.error(f"❌ {provider_obj.name} ไม่พร้อมใช้งาน (ขาด API Key)")
                else:
                    try:
                        prov_name = provider_obj.name if provider_obj else 'AI'
                        with st.spinner(f"🔄 กำลังสร้าง Prompts ทั้งหมดด้วย {prov_name}..."):
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
                            
                            st.success(f"✅ สร้างสำเร็จ {len(generated_scenes)} Prompts! ({prompt_gen.provider_name}/{prompt_gen.active_model})")
                            st.rerun()
                            
                    except Exception as e:
                        st.error(f"❌ สร้าง Prompt ไม่สำเร็จ: {e}")
                        st.info("💡 คำแนะนำ: 1) ตรวจสอบ Step 3 2) API Key 3) เปลี่ยน Provider 4) ลองสร้างทีละฉาก")
    
    st.markdown("---")
    
    # ===== DISPLAY PROMPTS =====
    if project.scenes:
        st.subheader(f"📋 รายการ Veo Prompts ({len(project.scenes)} ฉาก)")
        
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
                "💾 ดาวน์โหลด Prompts ทั้งหมด",
                data=prompts_text,
                file_name=f"{project.title}_prompts.txt",
                mime="text/plain",
                use_container_width=True
            )
        
        with col_export2:
            if st.button("📋 คัดลอกทั้งหมด", use_container_width=True):
                copy_to_clipboard(prompts_text, "all_prompts")
                st.toast("✅ คัดลอก Prompts ทั้งหมดแล้ว!", icon="📋")
        
        with col_export3:
            completed = sum(1 for s in project.scenes if s.video_generated)
            st.metric("ความคืบหน้าการสร้างวิดีโอ", f"{completed}/{len(project.scenes)}")
        
        # Link to Veo 3
        st.link_button(
            "🌟 ไปที่ Veo 3",
            "https://labs.google/fx/tools/video-fx",
            type="primary",
            use_container_width=True
        )

        st.markdown("---")

        # Visual Consistency Checker
        st.subheader("🔍 Visual Consistency Checker")
        st.caption("ตรวจสอบความต่อเนื่องของตัวละครและสไตล์ภาพระหว่างฉาก")

        col_cons, col_cons_opt = st.columns([3, 1])
        with col_cons_opt:
            auto_fix = st.checkbox("🔧 Auto-fix Critical", value=True, key="step4_autofix",
                                   help="ให้ AI แก้ไขปัญหา critical (เช่น สีผมเปลี่ยน) โดยอัตโนมัติ")
        with col_cons:
            if st.button("🕵️ ตรวจสอบ Consistency", use_container_width=True, key="step4_check_consistency"):
                try:
                    from src.core.prompt_generator import VeoPromptGenerator
                    with st.spinner("⏳ กำลังตรวจสอบ consistency..."):
                        pg = VeoPromptGenerator(
                            character_reference=project.character_reference,
                            provider=st.session_state.get("step4_llm_provider", "deepseek"),
                            model=st.session_state.get("step4_llm_model"),
                        )
                        report = pg.run_consistency_pass(
                            scenes=project.scenes,
                            character_reference=project.character_reference,
                            video_type=selected_video_type,
                            auto_fix_critical=auto_fix,
                        )
                    if report:
                        st.session_state["consistency_report"] = report
                        st.session_state.current_project = project
                        auto_save_project()
                        if report.status == "ok":
                            st.success(report.summary)
                        elif report.status == "critical":
                            st.error(report.summary)
                        else:
                            st.warning(report.summary)
                    else:
                        st.info("ตรวจสอบแล้ว ไม่พบปัญหาที่ชัดเจน")
                except Exception as e:
                    st.error(f"❌ เกิดข้อผิดพลาดในการตรวจสอบ: {e}")

        # Display last consistency report
        if "consistency_report" in st.session_state:
            report = st.session_state["consistency_report"]
            if report.issues:
                with st.expander(f"⚠️ พบปัญหา Consistency ({len(report.issues)} จุด)", expanded=False):
                    for issue in report.issues:
                        st.markdown(str(issue))

        st.markdown("---")

        # Platform Variants
        st.subheader("🌐 Multi-platform Variants")
        st.caption("สร้าง prompt ที่ปรับให้เข้ากับสไตล์ของแต่ละแพลตฟอร์ม")

        try:
            from src.core.platform_adapter import PLATFORM_CONFIGS, format_platform_label, generate_platform_variants

            selected_platforms = st.multiselect(
                "เลือก Platform",
                options=list(PLATFORM_CONFIGS.keys()),
                default=["tiktok", "youtube"],
                format_func=format_platform_label,
                key="step4_platforms",
            )

            if st.button("✨ สร้าง Platform Variants", use_container_width=True, key="step4_gen_platform"):
                if not selected_platforms:
                    st.warning("กรุณาเลือกอย่างน้อย 1 Platform")
                else:
                    with st.spinner(f"⏳ กำลังสร้าง variants สำหรับ {len(selected_platforms)} platforms..."):
                        for scene in project.scenes:
                            if scene.veo_prompt:
                                variants = generate_platform_variants(
                                    scene.veo_prompt,
                                    platforms=selected_platforms,
                                    video_type=selected_video_type,
                                )
                                scene.platform_variants = variants
                        st.session_state.current_project = project
                        auto_save_project()
                        st.success(f"✅ สร้าง variants สำเร็จสำหรับ {len(project.scenes)} ฉาก!")
                        st.rerun()
        except ImportError:
            st.info("Platform adapter ยังไม่เปิดใช้งาน")

        st.markdown("---")

        # A/B Testing
        st.subheader("🧪 A/B Prompt Testing")
        st.caption("สร้าง 3 variants เพื่อทดสอบว่า prompt ไหนให้ผลลัพธ์ดีที่สุด")

        ab_scene_idx = st.selectbox(
            "เลือกฉากที่ต้องการทำ A/B Test",
            options=list(range(len(project.scenes))),
            format_func=lambda i: f"ฉากที่ {project.scenes[i].order}: {project.scenes[i].narration_text[:40]}...",
            key="step4_ab_scene",
        ) if project.scenes else None

        if ab_scene_idx is not None:
            ab_scene = project.scenes[ab_scene_idx]
            n_variants = st.slider("จำนวน Variants", min_value=2, max_value=3, value=3, key="step4_ab_n")

            if st.button(f"🧪 สร้าง {n_variants} Variants สำหรับฉากที่ {ab_scene.order}", key="step4_gen_ab"):
                try:
                    from src.core.prompt_generator import VeoPromptGenerator
                    with st.spinner(f"⏳ กำลังสร้าง {n_variants} variants..."):
                        pg = VeoPromptGenerator(
                            character_reference=project.character_reference,
                            provider=st.session_state.get("step4_llm_provider", "deepseek"),
                            model=st.session_state.get("step4_llm_model"),
                        )
                        project_context = _build_project_context()
                        variants_with_scores = pg.generate_variants(
                            scene=ab_scene,
                            n=n_variants,
                            character_override=project.character_reference,
                            visual_theme=project_context.get("visual_theme", ""),
                            video_type=selected_video_type,
                        )
                    if variants_with_scores:
                        ab_scene.prompt_variants = [v[0] for v in variants_with_scores]
                        # Best variant becomes the main prompt
                        ab_scene.veo_prompt = variants_with_scores[0][0]
                        ab_scene.quality_score = variants_with_scores[0][1]
                        st.session_state.current_project = project
                        auto_save_project()
                        st.success(f"✅ สร้าง {len(variants_with_scores)} variants สำเร็จ!")
                        st.rerun()
                    else:
                        st.error("ไม่สามารถสร้าง variants ได้")
                except Exception as e:
                    st.error(f"❌ A/B Testing ผิดพลาด: {e}")

            # Show existing variants for selection
            if ab_scene.prompt_variants:
                st.markdown("**👉 เลือก Variant ที่ต้องการใช้:**")
                for vi, variant_prompt in enumerate(ab_scene.prompt_variants):
                    col_vr, col_vs = st.columns([4, 1])
                    with col_vr:
                        label = "🏆 Best" if vi == 0 else f"#{vi+1}"
                        with st.expander(f"{label} Variant {vi+1}", expanded=(vi == 0)):
                            st.code(variant_prompt[:300], language="text")
                    with col_vs:
                        if st.button(f"เลือกใช้ #{vi+1}", key=f"use_variant_{ab_scene.scene_id}_{vi}"):
                            ab_scene.veo_prompt = variant_prompt
                            ab_scene.selected_variant = vi
                            st.session_state.current_project = project
                            auto_save_project()
                            st.success(f"✅ เลือกใช้ Variant #{vi+1} แล้ว!")
                            st.rerun()

        st.markdown("---")


        for i, scene in enumerate(project.scenes):
            status_icon = "✅" if scene.video_generated else "⬜"
            
            with st.expander(
                f"{status_icon} ฉากที่ {scene.order}: [{scene.time_range}] - {scene.narration_text[:40]}...",
                expanded=not scene.video_generated
            ):
                # Timing sidebar
                col_main, col_side = st.columns([4, 1])
                
                with col_side:
                    st.markdown("**⏱️ Veo 3: 8 วินาที**")
                    st.caption(f"เสียงพากย์: {scene.audio_duration:.1f}s")
                    st.caption(f"Time: {scene.time_range}")
                    st.markdown("---")
                    scene.video_generated = st.checkbox(
                        "✅ สร้างวิดีโอแล้ว",
                        value=scene.video_generated,
                        key=f"gen_{scene.scene_id}_{i}"
                    )
                    
                    # Per-prompt mode: individual generate button
                    if is_per_prompt_mode:
                        st.markdown("---")
                        has_prompt = bool(scene.veo_prompt)
                        btn_label = "🔄 สร้างใหม่" if has_prompt else "✨ สร้าง Prompt"
                        btn_type = "secondary" if has_prompt else "primary"
                        
                        if st.button(btn_label, key=f"gen_single_{scene.scene_id}_{i}", type=btn_type, use_container_width=True):
                            if provider_obj and not provider_obj.is_available:
                                st.error(f"❌ ขาด API Key")
                            else:
                                try:
                                    with st.spinner(f"⏳ กำลังสร้าง Prompt ฉากที่ {scene.order}..."):
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

                                        # Generate ONLY this single scene
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
                                        st.success(f"✅ สร้าง Prompt ฉากที่ {scene.order} สำเร็จ!")
                                        st.rerun()
                                except Exception as e:
                                    st.error(f"❌ เกิดข้อผิดพลาด: {e}")
                
                with col_main:
                    # 4 Tabs for the 4 prompt sections
                    tab1, tab2, tab3, tab4 = st.tabs([
                        "🎥 Video Style Prompt",
                        "🗣️ Thai Voiceover",
                        "🎙️ Speaking Style",
                        "📑 Combined Prompt"
                    ])
                    
                    # --- Tab 1: Video Style Prompt ---
                    with tab1:
                        st.markdown("**🎥 Video Style Prompt**")
                        st.caption("Prompt ภาษาอังกฤษสำหรับสร้างวิดีโอใน Veo 3 (Visual Only)")
                        if scene.veo_prompt:
                            st.code(scene.veo_prompt, language="text")
                            col_copy, col_dl = st.columns(2)
                            with col_copy:
                                if st.button("📋 คัดลอก Video Style", key=f"copy_veo_{scene.order}_{i}", use_container_width=True):
                                    copy_to_clipboard(scene.veo_prompt, f"veo_{scene.order}_{i}")
                            with col_dl:
                                st.download_button("💾 ดาวน์โหลด", data=scene.veo_prompt, file_name=f"scene{scene.order}_video_style.txt", mime="text/plain", key=f"dl_veo_{scene.order}_{i}", use_container_width=True)
                        else:
                            st.warning("ยังไม่มี Video Style Prompt")
                    
                    # --- Tab 2: Thai Voiceover ---
                    with tab2:
                        st.markdown("**🗣️ Thai Voiceover**")
                        st.caption("บทพากย์เสียงภาษาไทยสำหรับฉากนี้")
                        if scene.voiceover_prompt:
                            st.success(scene.voiceover_prompt)
                            col_copy, col_dl = st.columns(2)
                            with col_copy:
                                if st.button("📋 คัดลอกบทพากย์", key=f"copy_vo_{scene.order}_{i}", use_container_width=True):
                                    copy_to_clipboard(scene.voiceover_prompt, f"vo_{scene.order}_{i}")
                            with col_dl:
                                st.download_button("💾 ดาวน์โหลด", data=scene.voiceover_prompt, file_name=f"scene{scene.order}_voiceover.txt", mime="text/plain", key=f"dl_vo_{scene.order}_{i}", use_container_width=True)
                        else:
                            st.warning("ยังไม่มีบทพากย์")
                    
                    # --- Tab 3: Speaking Style ---
                    with tab3:
                        st.markdown("**🎙️ Speaking Style / Voice Direction**")
                        st.caption("คำแนะนำสำหรับ AI Voice (Tone, Pacing, Emotion)")
                        if scene.voice_tone:
                            st.code(scene.voice_tone, language="text")
                            col_copy, col_dl = st.columns(2)
                            with col_copy:
                                if st.button("📋 คัดลอก Speaking Style", key=f"copy_tone_{scene.order}_{i}", use_container_width=True):
                                    copy_to_clipboard(scene.voice_tone, f"tone_{scene.order}_{i}")
                            with col_dl:
                                st.download_button("💾 ดาวน์โหลด", data=scene.voice_tone, file_name=f"scene{scene.order}_speaking_style.txt", mime="text/plain", key=f"dl_tone_{scene.order}_{i}", use_container_width=True)
                        else:
                            st.warning("ยังไม่มี Speaking Style")
                    
                    # --- Tab 4: Combined Prompt ---
                    with tab4:
                        st.markdown("**📑 Combined Prompt (All-in-One)**")
                        st.caption("รวมทุกส่วนไว้ในที่เดียว")
                        
                        combined_parts = []
                        
                        if scene.veo_prompt:
                            combined_parts.append(f"[🎥 Video Style Prompt]\n{scene.veo_prompt}")
                        
                        if scene.voiceover_prompt:
                            combined_parts.append(f"[🗣️ Thai Voiceover]\n{scene.voiceover_prompt}")
                        
                        if scene.voice_tone:
                            combined_parts.append(f"[🎙️ Speaking Style]\n{scene.voice_tone}")
                        
                        combined_text = "\n\n".join(combined_parts) if combined_parts else ""
                        
                        if combined_text:
                            st.code(combined_text, language="text")
                            col_copy, col_dl = st.columns(2)
                            with col_copy:
                                if st.button("📋 คัดลอกทั้งหมด", key=f"copy_all_{scene.order}_{i}", use_container_width=True):
                                    copy_to_clipboard(combined_text, f"all_{scene.order}_{i}")
                            with col_dl:
                                st.download_button("💾 ดาวน์โหลด", data=combined_text, file_name=f"scene{scene.order}_full_prompt.txt", mime="text/plain", key=f"dl_all_{scene.order}_{i}", use_container_width=True)
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
            st.success("✅ บันทึก Prompt เรียบร้อย!")
    
    with col_next:
        if st.button("➡️ ถัดไป: อัพโหลดไฟล์", type="primary", use_container_width=True):
            project.status = "step5_upload"
            project.workflow_step = 4
            st.session_state.current_project = project
            save_project(project)
            st.session_state.page = STEP_UPLOAD
            st.rerun()
