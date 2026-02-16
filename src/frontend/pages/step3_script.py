"""
Step 3: บทพูด (Script & Audio)
Voice personality, script text, AI Studio integration, audio upload and segmentation
"""
import streamlit as st
import os
import re
import unicodedata
from pathlib import Path

# Imports
from src.core.models import AudioSegment
from src.shared.project_manager import save_project
from src.frontend.utils import show_back_button, auto_save_project, show_step_guard
from src.config.constants import (
    STEP_CONTENT, STEP_VIDEO_PROMPT, STEP_SCRIPT,
    VOICE_PERSONALITIES, DATA_DIR,
    CONTENT_CATEGORIES, VIDEO_FORMATS, PLATFORMS
)


def extract_voiceover_text(raw_script: str) -> str:
    """Extract only spoken narration, removing stage directions, scene markers, and non-spoken elements.
    
    This is the single source of truth for cleaning AI-generated scripts.
    It strips everything that isn't actual spoken narration text.
    """
    if not raw_script:
        return ""
    lines = raw_script.split("\n")
    spoken = []
    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue
        # Skip lines that are entirely in parentheses (stage directions)
        # e.g. (ฉากเปิดด้วยตัวละครผู้หญิง...), (บรรยากาศสีพาสเทลอ่อนๆ...)
        if stripped.startswith("(") and stripped.endswith(")"):
            continue
        # Skip Thai visual/scene directions that START with ( + Thai direction keyword
        # e.g. (ภาพเปิดตัว: ...), (ฉากเปิดด้วย...), (ตัวละครยืน...), (บรรยากาศ...)
        # These may not end with ) if the AI truncates or wraps them
        if re.match(r'^\((?:ภาพ|ฉาก|ตัวละคร|บรรยากาศ|เสียง|แสง|กล้อง|มุมกล้อง|ซูม|แพน|ทันใดนั้น|สลิต|คัท|โคลสอัพ|ไวด์ช็อต)', stripped):
            continue
        # Skip lines in square brackets [Scene 1], [ฉาก 1] etc.
        if stripped.startswith("[") and stripped.endswith("]"):
            continue
        # Skip scene/marker headers: "Scene 1:", "ฉากที่ 1:", "ฉาก 1:"
        if re.match(r'^(scene|ฉาก|ฉากที่)\s*\d+', stripped, re.IGNORECASE):
            continue
        # Skip separator lines (---, ===, ***)
        if re.match(r'^[-=*]{3,}$', stripped):
            continue
        # Skip markdown bold headers like **ฉากที่ 1:** or **เปิดเรื่อง**
        if re.match(r'^\*\*[^*]+\*\*:?\s*$', stripped):
            continue
        # Skip emoji-prefixed headers like 🎬 ฉากเปิด, 📌 หมายเหตุ
        if re.match(r'^[\U0001F300-\U0001FAFFぁ-ヶ]', stripped):
            continue
        # Skip numbered outline markers like "1.", "1)", "ข้อ 1."
        if re.match(r'^(\d+[.):]|ข้อ\s*\d+)', stripped):
            continue
        # Skip lines that are entirely stage direction keywords
        direction_keywords = (
            'ฉากเปิด', 'ฉากปิด', 'ตัดฉาก', 'เฟดอิน', 'เฟดเอาท์',
            'fade in', 'fade out', 'cut to', 'dissolve',
        )
        if stripped.lower() in direction_keywords:
            continue
        # Remove inline parenthetical directions from the line
        cleaned = re.sub(r'\([^)]*\)', '', stripped).strip()
        # Remove inline markdown bold markers
        cleaned = re.sub(r'\*\*([^*]+)\*\*', r'\1', cleaned).strip()
        if cleaned:
            spoken.append(cleaned)
    return "\n".join(spoken)

# Try import DB functions for enriched context
try:
    from src.core.database import get_content_goals, get_target_audiences, get_video_profile
    DB_AVAILABLE = True
except ImportError:
    DB_AVAILABLE = False

# Try import transcription
try:
    from src.core.transcriber import AudioTranscriber
    TRANSCRIPTION_AVAILABLE = True
except ImportError:
    TRANSCRIPTION_AVAILABLE = False

# Try import AI generators
try:
    from src.core.script_generator import ScriptGenerator
    SCRIPT_GEN_AVAILABLE = True
except ImportError:
    SCRIPT_GEN_AVAILABLE = False

try:
    from src.core.aistudio_generator import generate_ai_studio_output
    AISTUDIO_AVAILABLE = True
except ImportError:
    AISTUDIO_AVAILABLE = False


def _show_step2_context(project):
    """Display Step 2 data summary at the top of Step 3"""
    has_data = any([
        project.content_description or project.topic,
        project.content_goal,
        project.target_audience,
        getattr(project, 'content_category', ''),
        getattr(project, 'platforms', []),
        getattr(project, 'video_format', ''),
    ])
    
    if not has_data:
        st.info("💡 ยังไม่มีข้อมูลจาก Step 2 — กลับไปกำหนดคอนเทนต์ก่อนเพื่อให้ AI สร้างบทได้ดีขึ้น")
        return
    
    with st.expander("📋 ข้อมูลจาก Step 2 (กำหนดคอนเทนต์)", expanded=False):
        col1, col2 = st.columns(2)
        with col1:
            desc = project.content_description or project.topic or "–"
            st.markdown(f"**📌 หัวข้อ:** {desc[:100]}{'...' if len(desc) > 100 else ''}")
            st.markdown(f"**🎯 เป้าหมาย:** {project.content_goal or '–'}")
            st.markdown(f"**👥 กลุ่มเป้าหมาย:** {project.target_audience or '–'}")
        with col2:
            category = getattr(project, 'content_category', '')
            category_name = dict(CONTENT_CATEGORIES).get(category, category) if category else '–'
            st.markdown(f"**📂 หมวดหมู่:** {category_name}")
            
            video_format = getattr(project, 'video_format', '')
            format_name = dict(VIDEO_FORMATS).get(video_format, video_format) if video_format else '–'
            st.markdown(f"**📹 รูปแบบ:** {format_name}")
            
            platforms = getattr(project, 'platforms', [])
            if platforms:
                platform_names = [dict(PLATFORMS).get(p, p) for p in platforms]
                st.markdown(f"**🌐 แพลตฟอร์ม:** {', '.join(platform_names)}")
            else:
                st.markdown("**🌐 แพลตฟอร์ม:** –")
        
        st.markdown(f"**⏱️ ความยาวเป้าหมาย:** {project.target_duration} วินาที")
        
        if project.generated_content:
            st.markdown("---")
            st.markdown("**🤖 เนื้อหาที่ AI สร้าง (Step 2):**")
            st.markdown(project.generated_content)


def _build_script_context(project) -> str:
    """Build enriched topic context from Step 2 data for script generation"""
    parts = []
    
    # Base topic/description
    base_topic = project.content_description or project.topic or ""
    parts.append(f"📌 หัวข้อ: {base_topic}")
    
    # Video Profile (enriched from DB)
    profile_id = getattr(project, 'video_profile_id', None)
    if DB_AVAILABLE and profile_id:
        try:
            profile_data = get_video_profile(profile_id)
            if profile_data:
                parts.append(f"🎬 Profile: {profile_data.get('name_th', '')} ({profile_data.get('name_en', '')})")
        except Exception:
            pass
    
    # Content Goal (enriched from DB)
    goal_text = project.content_goal or ""
    goal_hint = ""
    if DB_AVAILABLE and getattr(project, 'content_goal_id', None):
        try:
            goals = get_content_goals()
            goal_data = next((g for g in goals if g["id"] == project.content_goal_id), None)
            if goal_data:
                goal_text = f"{goal_data['name_th']} — {goal_data.get('description', '')}"
                goal_hint = goal_data.get("prompt_hint", "")
        except Exception:
            pass
    if goal_text:
        parts.append(f"🎯 เป้าหมาย: {goal_text}")
    
    # Target Audience (enriched from DB)
    audience_text = project.target_audience or ""
    if DB_AVAILABLE and getattr(project, 'target_audience_id', None):
        try:
            audiences = get_target_audiences()
            aud_data = next((a for a in audiences if a["id"] == project.target_audience_id), None)
            if aud_data:
                audience_text = f"{aud_data['name_th']} ({aud_data.get('age_range', '')}) — {aud_data.get('description', '')}"
        except Exception:
            pass
    if audience_text:
        parts.append(f"👥 กลุ่มเป้าหมาย: {audience_text}")
    
    # Category
    category = getattr(project, 'content_category', '')
    if category:
        category_name = dict(CONTENT_CATEGORIES).get(category, category)
        parts.append(f"📂 หมวดหมู่: {category_name}")
    
    # Platforms
    platforms = getattr(project, 'platforms', [])
    if platforms:
        platform_names = [dict(PLATFORMS).get(p, p) for p in platforms]
        parts.append(f"🌐 แพลตฟอร์ม: {', '.join(platform_names)}")
    
    # Video Format
    video_format = getattr(project, 'video_format', '')
    if video_format:
        format_name = dict(VIDEO_FORMATS).get(video_format, video_format)
        parts.append(f"📹 รูปแบบ: {format_name}")
    
    # Duration
    parts.append(f"⏱️ ความยาว: {project.target_duration} วินาที")
    
    # Goal-specific prompt hint for LLM
    if goal_hint:
        parts.append(f"\n💡 แนวทางการสร้างเนื้อหา: {goal_hint}")
    
    # Generated content from Step 2 (AI analysis)
    generated = getattr(project, 'generated_content', '')
    if generated:
        parts.append(f"\n📋 ข้อมูลจากการวิเคราะห์เนื้อหา:\n{generated}")
    
    return "\n".join(parts)


def render():
    """Step 3: บทพูด"""
    # Back button
    if st.button("← ย้อนกลับ: กำหนดคอนเทนต์"):
        st.session_state.page = STEP_CONTENT
        st.rerun()
    
    st.title("3️⃣ บทพูด")
    
    if not show_step_guard(2):
        return
    
    project = st.session_state.current_project
    st.caption(f"📁 โปรเจค: **{project.title}**")
    
    # Show Step 2 context summary
    _show_step2_context(project)
    
    st.markdown("---")
    
    # ===== STEP A: VOICE PERSONALITY =====
    st.subheader("🎭 A. บุคลิกน้ำเสียง")
    
    personality_options = {p[0]: p[1] for p in VOICE_PERSONALITIES}
    selected_personality = st.selectbox(
        "เลือกบุคลิกน้ำเสียง",
        options=list(personality_options.keys()),
        format_func=lambda x: personality_options.get(x, x),
        index=list(personality_options.keys()).index(project.voice_personality) if project.voice_personality in personality_options else 0,
        key="step3_personality"
    )
    project.voice_personality = selected_personality
    
    st.markdown("---")
    
    # ===== STEP B: SCRIPT =====
    st.subheader("📝 B. บทพูด")
    
    # Check if AI just generated a script (stored in separate key before rerun)
    if "_generated_script" in st.session_state and st.session_state._generated_script:
        # Clean the generated script before applying
        clean_generated = extract_voiceover_text(st.session_state._generated_script)
        project.full_script = clean_generated
        # CRITICAL: Also set the widget's own session state key so the text_area
        # picks up the new value on this render cycle (Streamlit widget state fix)
        st.session_state.step3_script = clean_generated
        st.session_state.current_project = project
        del st.session_state._generated_script  # Clear after applying
    
    # Clean any existing dirty script (from older AI generations before the filter existed)
    display_script = extract_voiceover_text(project.full_script) if project.full_script else ""
    
    # Script text area (single source — only show actual script, not Step 2 description)
    script_text = st.text_area(
        "บทพูด (ภาษาไทย)",
        value=display_script,
        height=200,
        placeholder="กดปุ่ม 'สร้างบทด้วย AI' เพื่อสร้างบทพูดอัตโนมัติ หรือพิมพ์บทเอง...",
        key="step3_script"
    )
    project.full_script = script_text
    st.session_state.current_project = project
    auto_save_project()
    
    if not script_text.strip():
        st.info("💡 ยังไม่มีบทพูด — กดปุ่ม **สร้างบทด้วย AI** ด้านล่างเพื่อสร้างจากข้อมูล Step 2")
    
    col_info, col_ai = st.columns([2, 1])
    with col_info:
        st.caption(f"📊 {len(script_text)} ตัวอักษร | ประมาณ {len(script_text) // 10:.0f} วินาที")
    
    # --- Model selector for script generation ---
    AI_SCRIPT_MODELS = {
        "🧠 DeepSeek": {
            "provider": "deepseek",
            "api_key_env": "DEEPSEEK_API_KEY",
        },
        "🌙 Kimi K2.5": {
            "provider": "kimi",
            "api_key_env": "KIMI_API_KEY",
        },
    }
    
    selected_script_model = st.radio(
        "เลือก AI Model สำหรับสร้างบท",
        list(AI_SCRIPT_MODELS.keys()),
        horizontal=True,
        key="step3_model_select"
    )
    model_cfg = AI_SCRIPT_MODELS[selected_script_model]
    
    with col_ai:
        if st.button("🤖 สร้างบทด้วย AI", use_container_width=True):
            script_api_key = os.getenv(model_cfg["api_key_env"], "")
            if SCRIPT_GEN_AVAILABLE and script_api_key:
                try:
                    with st.spinner(f"🔄 กำลังสร้างบทด้วย {selected_script_model}..."):
                        generator = ScriptGenerator(
                            api_key=script_api_key,
                            provider=model_cfg["provider"],
                        )
                        
                        enriched_topic = _build_script_context(project)
                        
                        script = generator.generate_script(
                            topic=enriched_topic,
                            style=project.voice_personality or "documentary",
                            target_duration=project.target_duration,
                            language="th",
                            story_proposal=getattr(project, 'proposal', None),
                        )
                        # Store in separate key (NOT widget key) to avoid Streamlit error
                        st.session_state._generated_script = extract_voiceover_text(script)
                        st.rerun()
                except Exception as e:
                    st.error(f"❌ สร้างบทพูดไม่สำเร็จ: {e}")
                    st.info("💡 ลองตรวจสอบ: 1) API Key ถูกต้อง 2) มีอินเทอร์เน็ต 3) ลองกดใหม่อีกครั้ง")
            else:
                st.warning(f"⚠️ ต้องใส่ {model_cfg['api_key_env']} ในไฟล์ .env")
    
    st.markdown("---")
    
    # ===== STEP C: VOICE GENERATION (AI Studio Helper) =====
    st.subheader("🎙️ C. สร้างเสียงพากย์")
    st.caption("เมื่อบทพร้อมแล้ว → Copy ข้อมูลด้านล่างไปใช้กับ Google AI Studio")
    
    # Auto-generate style from voice personality (no separate button needed)
    default_style = f"Tone: {personality_options.get(selected_personality, 'Warm & Friendly')}. Read in a natural, conversational way."
    if not project.style_instructions:
        project.style_instructions = default_style
    
    with st.expander("📋 ข้อมูลสำหรับ AI Studio", expanded=False):
        # Style instructions (editable)
        style_box = st.text_area(
            "Style Instructions (ปรับแต่งได้)",
            value=project.style_instructions or default_style,
            height=80,
            key="step3_style"
        )
        project.style_instructions = style_box
        
        # Copy Style button
        col_copy_style, col_copy_script = st.columns(2)
        with col_copy_style:
            st.code(style_box, language=None)
            st.caption("👆 เลือก copy ข้อความด้านบน")
        
        # Script preview with copy — ONLY spoken narration (strip stage directions)
        with col_copy_script:
            vo_text = extract_voiceover_text(script_text)
            st.code(vo_text or "(ยังไม่มีบทพูด)", language=None)
            st.caption("👆 เลือก copy บทพูดด้านบน")
        
        # Action buttons
        st.markdown("---")
        col_link, col_help = st.columns([1, 1])
        with col_link:
            st.link_button(
                "🌟 เปิด AI Studio",
                "https://aistudio.google.com/generate-speech",
                type="primary",
                use_container_width=True
            )
        with col_help:
            st.markdown("""**วิธีใช้:**
1. Copy **Style** (ซ้าย) → Paste ใน AI Studio
2. Copy **Script** (ขวา) → Paste ใน AI Studio
3. กด **Generate** → **Download**
4. กลับมาอัพโหลดไฟล์เสียงด้านล่าง""")
    
    st.markdown("---")
    
    # ===== STEP D: AUDIO UPLOAD =====
    st.subheader("🎤 D. อัพโหลดคลิปเสียง")
    
    # Show existing audio if available
    if project.audio_path and os.path.exists(project.audio_path):
        st.success(f"✅ มีไฟล์เสียง: {Path(project.audio_path).name}")
        st.audio(project.audio_path)
        
        if st.button("🗑️ ลบไฟล์เสียง"):
            project.audio_path = None
            project.audio_segments = []
            st.session_state.current_project = project
            auto_save_project()
            st.session_state.page = STEP_SCRIPT
            st.rerun()
    
    # Upload audio
    uploaded_audio = st.file_uploader(
        "อัพโหลดไฟล์เสียง (MP3, WAV, M4A)",
        type=["mp3", "wav", "m4a", "ogg", "flac"],
        key="step3_audio_upload"
    )
    
    if uploaded_audio:
        # Save to project folder
        project_dir = DATA_DIR / project.project_id
        audio_filename = f"audio_{uploaded_audio.name}"
        audio_path = project_dir / audio_filename
        
        # Check if this file is already processed to prevent infinite loop
        # Compare filenames to avoid absolute/relative path mismatch issues
        should_process = True
        if project.audio_path:
            try:
                # Normalize strings to handle Thai characters (NFC)
                current_name = unicodedata.normalize('NFC', Path(project.audio_path).name)
                new_name = unicodedata.normalize('NFC', audio_filename)
                
                # Check 1: Valid previous path and file exists
                if current_name == new_name and os.path.exists(project.audio_path):
                    should_process = False
            except Exception:
                # Fallback to simple comparison if normalization fails
                if Path(project.audio_path).name == audio_filename:
                    should_process = False

        if should_process:
            project_dir.mkdir(parents=True, exist_ok=True)
            
            with open(audio_path, "wb") as f:
                f.write(uploaded_audio.getvalue())
            
            project.audio_path = str(audio_path)
            st.session_state.current_project = project
            auto_save_project()
            
            st.success(f"✅ อัพโหลดสำเร็จ: {uploaded_audio.name}")
            st.rerun()
    
    st.markdown("---")
    
    # ===== AUDIO SEGMENTATION =====
    if project.audio_path and os.path.exists(project.audio_path):
        st.subheader("✂️ E. ซอยย่อยคลิปเสียง")
        
        # --- Model & quality settings ---
        col_model, col_ai = st.columns(2)
        with col_model:
            whisper_model = st.radio(
                "🧠 Whisper Model",
                options=["large-v3", "small"],
                index=0,
                horizontal=True,
                help="large-v3 แม่นกว่ามาก แต่ใช้เวลานานกว่า ~3x"
            )
        with col_ai:
            ai_correct = st.checkbox(
                "✨ ตรวจทานด้วย AI (DeepSeek)",
                value=True,
                help="ใช้ LLM แก้คำสะกดผิดหลังถอดเสียง เช่น ตั้งเบาหมาย → ตั้งเป้าหมาย"
            )
        
        if whisper_model == "large-v3":
            st.caption("🔵 large-v3: แม่นภาษาไทยมาก ใช้ RAM ~3GB ใช้เวลาประมาณ 2-5 นาที")
        else:
            st.caption("🟢 small: เร็วกว่า ใช้ RAM ~1GB แต่อาจมีคำผิดบ้าง")
        
        if st.button("🎙️ เริ่มซอยคลิปเสียง (Whisper AI)", type="primary", use_container_width=True):
            if not TRANSCRIPTION_AVAILABLE:
                st.error("❌ Whisper ยังไม่ติดตั้ง")
                st.code("pip install faster-whisper")
            else:
                try:
                    model_label = "Large-V3" if whisper_model == "large-v3" else "Small"
                    with st.spinner(f"🔄 กำลังโหลด AI model ({model_label})..."):
                        transcriber = AudioTranscriber(model_size=whisper_model, device="cpu", compute_type="int8")
                
                    # Context prompt to guide Whisper for better Thai transcription
                    thai_prompt = (
                        "ประโยคต่อไปนี้เป็นบทพูดภาษาไทยที่ชัดเจน เรื่องราวเกี่ยวกับ "
                        f"{project.topic or 'เนื้อหาทั่วไป'} "
                        "สามารถใช้คำทับศัพท์ภาษาอังกฤษได้ตามความเหมาะสม โดยเฉพาะคำเฉพาะทาง เช่น AI, Technology"
                    )
                    
                    with st.spinner("🎧 กำลังฟังเสียงและซอยฉาก (≤8 วินาที)..."):
                        result = transcriber.transcribe_with_summary(
                            project.audio_path, 
                            language="th",
                            initial_prompt=thai_prompt
                        )
                    
                    raw_segments = result["segments"]
                    
                    # LLM Post-Correction (DeepSeek)
                    if ai_correct and raw_segments:
                        deepseek_key = os.environ.get("DEEPSEEK_API_KEY", "")
                        if deepseek_key:
                            with st.spinner("✨ กำลังตรวจทานคำสะกดด้วย DeepSeek..."):
                                reference = project.full_script or ""
                                raw_segments = AudioTranscriber.correct_with_llm(
                                    segments=raw_segments,
                                    reference_script=reference,
                                    api_key=deepseek_key,
                                    provider="deepseek",
                                )
                            st.toast("✅ ตรวจทานคำสะกดเสร็จ!", icon="✨")
                        else:
                            st.warning("⚠️ ไม่พบ DEEPSEEK_API_KEY — ข้ามขั้นตอนตรวจทาน")
                    
                    # Convert to AudioSegment
                    segments = []
                    for i, seg in enumerate(raw_segments, 1):
                        segments.append(AudioSegment(
                            order=i,
                            start_time=seg.start,
                            end_time=seg.end,
                            duration=round(seg.end - seg.start, 2),
                            text_content=seg.text
                        ))
                    
                    project.audio_segments = segments
                    project.audio_duration = result["total_duration"]
                    project.full_script = result["full_text"]  # Update script with actual transcription
                    
                    st.session_state.current_project = project
                    auto_save_project()
                    
                    model_info = f"model={model_label}"
                    ai_info = " + AI ตรวจทาน" if ai_correct else ""
                    st.success(f"✅ ซอยสำเร็จ! ได้ {len(segments)} ฉาก (รวม {result['total_duration']:.1f}s, {model_info}{ai_info})")
                    st.rerun()
                    
                except Exception as e:
                    st.error(f"❌ ซอยเสียงไม่สำเร็จ: {e}")
                    st.info("💡 ตรวจสอบว่าไฟล์เสียงอยู่ในรูปแบบที่รองรับ (.mp3, .wav, .m4a)")
        
        # Display segments
        if project.audio_segments:
            st.markdown("**📊 ฉากที่ซอยแล้ว:**")
            
            for i, seg in enumerate(project.audio_segments):
                status = "🔴" if seg.duration > 8.0 else "🟢"
                with st.expander(f"{status} ฉาก {seg.order}: {seg.time_range} ({seg.duration:.1f}s)"):
                    col1, col2 = st.columns([3, 1])
                    
                    with col1:
                        new_text = st.text_area(
                            "บทพูด",
                            value=seg.text_content,
                            key=f"seg_{i}",
                            height=80
                        )
                        seg.text_content = new_text
                    
                    with col2:
                        st.metric("Duration", f"{seg.duration:.1f}s")
                        if seg.duration > 8.0:
                            st.warning("⚠️ เกิน 8 วินาที!")
    
    st.markdown("---")
    
    # ===== ACTION BUTTONS =====
    col_save, col_next = st.columns(2)
    
    with col_save:
        if st.button("💾 บันทึกบทพูด", use_container_width=True):
            project.status = "step3_script"
            project.workflow_step = 2
            st.session_state.current_project = project
            save_project(project)
            st.success("✅ บันทึกบทพูดสำเร็จ!")
    
    with col_next:
        if st.button("➡️ ถัดไป: สร้าง Prompt Vdo", type="primary", use_container_width=True):
            project.status = "step4_prompt"
            project.workflow_step = 3
            st.session_state.current_project = project
            save_project(project)
            st.session_state.page = STEP_VIDEO_PROMPT
            st.rerun()
