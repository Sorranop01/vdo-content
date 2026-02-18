"""
Step 2: กำหนดคอนเทนต์ (Define Content)
Content planning with profile, goals, categories, audience, platforms
"""
import streamlit as st

# Imports
from src.core.models import Project
from src.shared.project_manager import save_project
from src.frontend.utils import show_back_button, auto_save_project, show_step_guard
from src.config.constants import (
    STEP_PROJECT, STEP_SCRIPT,
    CONTENT_CATEGORIES, PLATFORMS, VIDEO_FORMATS
)

# Try import AI generators
try:
    # Lazy import in render() to avoid heavy startup
    AI_AVAILABLE = True
except ImportError:
    AI_AVAILABLE = False

try:
    from src.frontend.data_cache import (
        get_cached_video_profiles as get_video_profiles,
        get_cached_content_goals as get_content_goals,
        get_cached_target_audiences as get_target_audiences
    )
    DB_AVAILABLE = True
except ImportError:
    DB_AVAILABLE = False
    get_video_profiles = lambda: []
    get_content_goals = lambda: []
    get_target_audiences = lambda: []


def render():
    """Step 2: กำหนดคอนเทนต์"""
    # Back button
    if st.button("← ย้อนกลับ: สร้างโปรเจค"):
        st.session_state.page = STEP_PROJECT
        st.rerun()
    
    st.title("2️⃣ กำหนดคอนเทนต์")
    
    if not show_step_guard(1):
        return
    
    project = st.session_state.current_project
    st.caption(f"📁 โปรเจค: **{project.title}**")
    
    st.markdown("---")
    
    # ===== PROFILE SELECTION =====
    st.subheader("👤 เลือก Profile")
    
    video_profiles = get_video_profiles() if DB_AVAILABLE else []
    
    if video_profiles:
        profile_options = {
            p["id"]: f"{p.get('icon', '🎬')} {p.get('name_th', p.get('name_en', 'Unknown'))}"
            for p in video_profiles
        }
        
        selected_profile = st.selectbox(
            "Profile",
            options=list(profile_options.keys()),
            format_func=lambda x: profile_options.get(x, x),
            index=0,
            key="step2_profile"
        )
        project.video_profile_id = selected_profile
    else:
        st.info("💡 ยังไม่มี Profile (ไปตั้งค่าที่ Database & Tags)")
    
    st.markdown("---")
    
    # ===== CONTENT PLANNING =====
    st.subheader("📋 วางแผนเนื้อหา")
    
    col1, col2 = st.columns(2)
    
    # --- Load dropdown data from DB ---
    content_goals = get_content_goals() if DB_AVAILABLE else []
    target_audiences = get_target_audiences() if DB_AVAILABLE else []
    
    with col1:
        # Content Goal — Dropdown
        if content_goals:
            goal_options = {
                g["id"]: f"{g.get('icon', '🎯')} {g['name_th']}"
                for g in content_goals
            }
            
            # Find current index
            current_goal_idx = 0
            if project.content_goal_id and project.content_goal_id in goal_options:
                current_goal_idx = list(goal_options.keys()).index(project.content_goal_id)
            
            selected_goal_id = st.selectbox(
                "🎯 เป้าหมายเนื้อหา",
                options=list(goal_options.keys()),
                format_func=lambda x: goal_options.get(x, x),
                index=current_goal_idx,
                key="step2_goal"
            )
            project.content_goal_id = selected_goal_id
            
            # Set display name for legacy compatibility
            selected_goal_data = next((g for g in content_goals if g["id"] == selected_goal_id), None)
            if selected_goal_data:
                project.content_goal = selected_goal_data["name_th"]
                # Show description as caption
                st.caption(f"💡 {selected_goal_data.get('description', '')}")
        else:
            # Fallback to text input
            content_goal = st.text_input(
                "🎯 เป้าหมายเนื้อหา",
                value=project.content_goal,
                placeholder="เช่น สอนทำอาหาร, รีวิวสินค้า, ให้ความรู้",
                key="step2_goal"
            )
            project.content_goal = content_goal
        
        # Target Audience — Dropdown
        if target_audiences:
            audience_options = {
                a["id"]: f"👥 {a['name_th']} ({a.get('age_range', '')})"
                for a in target_audiences
            }
            
            # Find current index
            current_aud_idx = 0
            if project.target_audience_id and project.target_audience_id in audience_options:
                current_aud_idx = list(audience_options.keys()).index(project.target_audience_id)
            
            selected_aud_id = st.selectbox(
                "👥 กลุ่มเป้าหมาย",
                options=list(audience_options.keys()),
                format_func=lambda x: audience_options.get(x, x),
                index=current_aud_idx,
                key="step2_audience"
            )
            project.target_audience_id = selected_aud_id
            
            # Set display name for legacy compatibility
            selected_aud_data = next((a for a in target_audiences if a["id"] == selected_aud_id), None)
            if selected_aud_data:
                project.target_audience = selected_aud_data["name_th"]
                st.caption(f"💡 {selected_aud_data.get('description', '')}")
        else:
            # Fallback to text input
            target_audience = st.text_input(
                "👥 กลุ่มเป้าหมาย",
                value=project.target_audience,
                placeholder="เช่น วัยรุ่น 18-25, แม่บ้าน, นักธุรกิจ",
                key="step2_audience"
            )
            project.target_audience = target_audience
    
    with col2:
        # Content Category
        category_options = {cat[0]: cat[1] for cat in CONTENT_CATEGORIES}
        selected_category = st.selectbox(
            "📂 หมวดหมู่เนื้อหา",
            options=list(category_options.keys()),
            format_func=lambda x: category_options.get(x, x),
            index=list(category_options.keys()).index(project.content_category) if project.content_category in category_options else 0,
            key="step2_category"
        )
        project.content_category = selected_category
        
        # Video Format
        format_options = {fmt[0]: fmt[1] for fmt in VIDEO_FORMATS}
        selected_format = st.selectbox(
            "📹 รูปแบบวีดีโอ",
            options=list(format_options.keys()),
            format_func=lambda x: format_options.get(x, x),
            index=list(format_options.keys()).index(project.video_format) if project.video_format in format_options else 0,
            key="step2_format"
        )
        project.video_format = selected_format
    
    # Platforms (Multi-select)
    st.markdown("**🌐 ช่องทางแพลตฟอร์ม**")
    platform_options = {p[0]: p[1] for p in PLATFORMS}
    
    # Create checkbox columns
    cols = st.columns(3)
    selected_platforms = []
    for i, (key, label) in enumerate(platform_options.items()):
        with cols[i % 3]:
            if st.checkbox(label, value=key in project.platforms, key=f"platform_{key}"):
                selected_platforms.append(key)
    project.platforms = selected_platforms
    
    st.markdown("---")
    
    # ===== CONTENT DESCRIPTION =====
    st.subheader("📝 รายละเอียดเนื้อหา")
    
    content_description = st.text_area(
        "อธิบายเนื้อหาที่ต้องการสร้าง",
        value=project.content_description or project.topic,
        height=150,
        placeholder="อธิบายรายละเอียดเนื้อหาที่ต้องการ เช่น จุดเด่น, สิ่งที่ต้องพูดถึง, tone ที่ต้องการ...",
        key="step2_content_desc"
    )
    project.content_description = content_description
    project.topic = content_description  # Sync with legacy topic field
    
    st.markdown("---")
    
    # ===== AI CONTENT GENERATION =====
    st.subheader("🤖 สร้างเนื้อหาด้วย AI")
    
    # --- Model selector ---
    import os
    
    AI_MODELS = {
        "🧠 DeepSeek": {
            "key": "deepseek",
            "model": "deepseek-chat",
            "base_url": "https://api.deepseek.com",
            "api_key_env": "DEEPSEEK_API_KEY",
        },
        "🌙 Kimi K2.5": {
            "key": "kimi",
            "model": "kimi-k2.5",
            "base_url": "https://api.moonshot.ai/v1",
            "api_key_env": "KIMI_API_KEY",
        },
    }
    
    selected_model_label = st.radio(
        "เลือก AI Model",
        list(AI_MODELS.keys()),
        index=0,
        horizontal=True,
        key="content_ai_model",
    )
    model_cfg = AI_MODELS[selected_model_label]
    
    # Resolve API key for selected model
    selected_api_key = os.getenv(model_cfg["api_key_env"], "") or st.session_state.get("api_key", "")
    
    col_gen, col_result = st.columns([1, 2])
    
    with col_gen:
        if st.button("✨ สร้างเนื้อหา", type="secondary", use_container_width=True, disabled=not content_description):
            if not AI_AVAILABLE:
                st.error("❌ AI ไม่พร้อมใช้งาน (ต้องติดตั้ง openai package)")
            elif not selected_api_key:
                st.error(f"❌ ไม่พบ {model_cfg['api_key_env']} กรุณาตั้งค่าใน .env")
            else:
                try:
                    with st.spinner(f"🔄 กำลังสร้างเนื้อหาด้วย {selected_model_label}..."):
                        # Build context from content planning
                        category_name = dict(CONTENT_CATEGORIES).get(project.content_category, project.content_category)
                        format_name = dict(VIDEO_FORMATS).get(project.video_format, project.video_format)
                        platform_names = [dict(PLATFORMS).get(p, p) for p in project.platforms]
                        
                        # --- Enrich context from DB data ---
                        goal_context = project.content_goal or 'ไม่ระบุ'
                        goal_hint = ""
                        if content_goals and project.content_goal_id:
                            goal_data = next((g for g in content_goals if g["id"] == project.content_goal_id), None)
                            if goal_data:
                                goal_context = f"{goal_data['name_th']} — {goal_data.get('description', '')}"
                                goal_hint = goal_data.get("prompt_hint", "")
                        
                        audience_context = project.target_audience or 'ทั่วไป'
                        if target_audiences and project.target_audience_id:
                            aud_data = next((a for a in target_audiences if a["id"] == project.target_audience_id), None)
                            if aud_data:
                                audience_context = f"{aud_data['name_th']} ({aud_data.get('age_range', '')}) — {aud_data.get('description', '')}"
                        
                        # Create rich context prompt with enriched data
                        context = f"""
📌 หัวข้อ: {content_description}
🎯 เป้าหมาย: {goal_context}
📂 หมวดหมู่: {category_name}
👥 กลุ่มเป้าหมาย: {audience_context}
🌐 แพลตฟอร์ม: {', '.join(platform_names) if platform_names else 'ทั่วไป'}
📹 รูปแบบ: {format_name}
⏱️ ความยาว: {project.target_duration} วินาที
"""
                        # Add goal-specific prompt hints for LLM
                        if goal_hint:
                            context += f"\n💡 แนวทางการสร้างเนื้อหา: {goal_hint}\n"
                        
                        from src.core.story_analyzer import StoryAnalyzer
                        analyzer = StoryAnalyzer(
                            api_key=selected_api_key,
                            model=model_cfg["model"],
                            base_url=model_cfg["base_url"],
                        )
                        
                        # Check if API is available
                        if not analyzer.is_available():
                            st.error(f"❌ {selected_model_label} API ไม่พร้อม - ตรวจสอบ API Key")
                        else:
                            proposal = analyzer.analyze_topic(
                                topic=context,  # Use full enriched context
                                style=project.video_profile_id or "documentary",
                                target_duration=project.target_duration
                            )
                            
                            # Format generated content in Thai
                            generated = f"📋 **การวิเคราะห์:**\n{proposal.analysis}\n\n"
                            generated += "📝 **โครงเรื่อง:**\n"
                            for i, item in enumerate(proposal.outline, 1):
                                generated += f"{i}. {item}\n"
                            
                            if proposal.key_points:
                                generated += "\n💡 **จุดสำคัญ:**\n"
                                for point in proposal.key_points:
                                    generated += f"- {point}\n"
                            
                            project.generated_content = generated
                            project.proposal = proposal
                            st.session_state.current_project = project
                            auto_save_project()
                            st.success(f"✅ สร้างเนื้อหาสำเร็จ! ({selected_model_label})")
                            st.rerun()
                        
                except Exception as e:
                    st.error(f"❌ สร้างเนื้อหาไม่สำเร็จ: {e}")
                    st.info(f"💡 ลองตรวจสอบ: 1) {model_cfg['api_key_env']} ถูกต้อง 2) มีอินเทอร์เน็ต 3) ลองกดใหม่อีกครั้ง")
    
    with col_result:
        if project.generated_content:
            st.markdown("**📄 เนื้อหาที่สร้าง:**")
            st.markdown(project.generated_content)
    
    st.markdown("---")
    
    # ===== ACTION BUTTONS =====
    col_save, col_next = st.columns(2)
    
    with col_save:
        if st.button("💾 บันทึกคอนเทนต์", use_container_width=True):
            project.status = "step2_content"
            project.workflow_step = 1
            st.session_state.current_project = project
            save_project(project)
            st.success("✅ บันทึกคอนเทนต์สำเร็จ!")
    
    with col_next:
        if st.button("➡️ ถัดไป: บทพูด", type="primary", use_container_width=True):
            project.status = "step3_script"
            project.workflow_step = 2
            st.session_state.current_project = project
            save_project(project)
            st.session_state.page = STEP_SCRIPT
            st.rerun()

