"""
Prompt Style Database for VDO Content
แนวทางการสร้าง Veo 3 Prompts ตามประเภทเนื้อหา

Categories:
1. Subject Type - ประเภทหัวข้อหลัก (มีคน/ไม่มีคน)
2. Content Genre - ประเภทเนื้อหา (อาหาร/ท่องเที่ยว/เทค)
3. Visual Composition - การจัดองค์ประกอบ
4. Color Mood - โทนสีและอารมณ์
"""

from pydantic import BaseModel, Field
from typing import Literal, Optional


class PromptStyle(BaseModel):
    """Single prompt style definition"""
    
    style_id: str = Field(description="Unique identifier")
    category: Literal["subject_type", "content_genre", "visual_composition", "color_mood"]
    
    name_th: str = Field(description="Thai display name")
    name_en: str = Field(description="English display name")
    description_th: str = Field(description="Thai description")
    description_en: str = Field(description="English description")
    
    prompt_injection: str = Field(description="Text to inject into Veo prompt")
    
    icon: str = Field(default="🎬", description="Emoji icon")
    order_num: int = Field(default=0, description="Display order")


# ============ PRESET PROMPT STYLES ============

PROMPT_STYLES: dict[str, PromptStyle] = {
    
    # ========== SUBJECT TYPE (👤 ประเภทหัวข้อหลัก) ==========
    
    "with_person_presenter": PromptStyle(
        style_id="with_person_presenter",
        category="subject_type",
        name_th="มีคน - พิธีกร/นำเสนอ",
        name_en="With Person (Presenter)",
        description_th="มีผู้นำเสนอพูดต่อกล้อง สบตาผู้ชม",
        description_en="Presenter speaking directly to camera, engaging with viewer",
        prompt_injection="A presenter speaking directly to camera, making eye contact with viewer, engaging and professional appearance, confident posture",
        icon="🎙️",
        order_num=1
    ),
    
    "with_person_lifestyle": PromptStyle(
        style_id="with_person_lifestyle",
        category="subject_type",
        name_th="มีคน - ไลฟ์สไตล์",
        name_en="With Person (Lifestyle)",
        description_th="มีคนทำกิจกรรมอย่างเป็นธรรมชาติ",
        description_en="Person naturally performing activities, candid shots",
        prompt_injection="Person naturally performing activities, candid lifestyle shots, authentic feeling, not looking at camera, immersed in activity",
        icon="🚶",
        order_num=2
    ),
    
    "with_person_testimonial": PromptStyle(
        style_id="with_person_testimonial",
        category="subject_type",
        name_th="มีคน - สัมภาษณ์/ให้การ",
        name_en="With Person (Testimonial)",
        description_th="สไตล์สัมภาษณ์ นั่งพูดเล่าประสบการณ์",
        description_en="Person sharing experience, interview style",
        prompt_injection="Person sharing experience in interview style, seated position, natural lighting, authentic testimonial, slight off-camera eye line",
        icon="💬",
        order_num=3
    ),
    
    "no_person_broll": PromptStyle(
        style_id="no_person_broll",
        category="subject_type",
        name_th="ไม่มีคน - B-Roll วิว",
        name_en="No Person (B-Roll/Scenic)",
        description_th="ภาพประกอบ วิว บรรยากาศ ไม่มีคน",
        description_en="Pure b-roll footage, no human subjects, atmospheric",
        prompt_injection="Pure b-roll footage, no human subjects visible, atmospheric establishing shots, scenic views, environmental visuals only",
        icon="🏞️",
        order_num=4
    ),
    
    "no_person_product": PromptStyle(
        style_id="no_person_product",
        category="subject_type",
        name_th="ไม่มีคน - โฟกัสสินค้า",
        name_en="No Person (Product Focus)",
        description_th="เน้นสินค้า/วัตถุ พื้นหลังสะอาด",
        description_en="Product-focused shots, clean background",
        prompt_injection="Product-focused shots, clean minimal background, detailed product showcase, no human subjects, professional product photography style",
        icon="📦",
        order_num=5
    ),
    
    "hands_only": PromptStyle(
        style_id="hands_only",
        category="subject_type",
        name_th="เฉพาะมือ - สอนทำ",
        name_en="Hands Only (Tutorial)",
        description_th="เห็นเฉพาะมือทำกิจกรรม สไตล์สอน",
        description_en="Close-up of hands performing action, tutorial style",
        prompt_injection="Close-up of hands performing action, tutorial style, step-by-step demonstration, face not visible, focus on hand movements and objects being handled",
        icon="🤲",
        order_num=6
    ),
    
    "silhouette": PromptStyle(
        style_id="silhouette",
        category="subject_type",
        name_th="เงาดำ - ลึกลับ",
        name_en="Silhouette/Anonymous",
        description_th="เห็นเป็นเงา แบคไลท์ ไม่เห็นหน้า",
        description_en="Silhouette of person, backlit, mysterious",
        prompt_injection="Silhouette of person, strongly backlit, mysterious atmosphere, identity hidden, dramatic rim lighting, privacy-focused anonymous appearance",
        icon="👤",
        order_num=7
    ),
    
    # ========== CONTENT GENRE (🎭 ประเภทเนื้อหา) ==========
    
    "food_cooking": PromptStyle(
        style_id="food_cooking",
        category="content_genre",
        name_th="อาหาร - ทำกับข้าว",
        name_en="Food (Cooking Process)",
        description_th="กระบวนการทำอาหาร วัตถุดิบ ไอน้ำ",
        description_en="Cooking process, fresh ingredients, steam",
        prompt_injection="Appetizing food close-ups, cooking process in action, steam rising from hot food, fresh colorful ingredients, kitchen environment, warm lighting",
        icon="🍳",
        order_num=1
    ),
    
    "food_review": PromptStyle(
        style_id="food_review",
        category="content_genre",
        name_th="อาหาร - รีวิว/จานสวย",
        name_en="Food (Review/Beauty Shots)",
        description_th="จัดจานสวย บรรยากาศร้าน",
        description_en="Plated dishes, restaurant ambiance",
        prompt_injection="Food beauty shots, elegantly plated dishes, restaurant ambiance, dining experience, appetizing presentation, shallow depth of field on food",
        icon="🍽️",
        order_num=2
    ),
    
    "travel_scenic": PromptStyle(
        style_id="travel_scenic",
        category="content_genre",
        name_th="ท่องเที่ยว - วิวทิวทัศน์",
        name_en="Travel (Scenic Views)",
        description_th="ภาพวิวสวย สถานที่ท่องเที่ยว ธรรมชาติ",
        description_en="Breathtaking landscape, travel destinations",
        prompt_injection="Breathtaking landscape, scenic vista, natural beauty, travel destination showcase, wide establishing shots, golden hour or blue hour lighting",
        icon="🏔️",
        order_num=3
    ),
    
    "travel_experience": PromptStyle(
        style_id="travel_experience",
        category="content_genre",
        name_th="ท่องเที่ยว - ประสบการณ์",
        name_en="Travel (Experience)",
        description_th="ประสบการณ์การเดินทาง วัฒนธรรม",
        description_en="Travel experience, cultural immersion",
        prompt_injection="Authentic travel experience, cultural immersion, local interaction, exploring new places, adventure and discovery, candid travel moments",
        icon="✈️",
        order_num=4
    ),
    
    "tech_unboxing": PromptStyle(
        style_id="tech_unboxing",
        category="content_genre",
        name_th="เทค - แกะกล่อง",
        name_en="Tech (Unboxing)",
        description_th="แกะกล่องสินค้า เผยสินค้าใหม่",
        description_en="Product unboxing, first impressions",
        prompt_injection="Product unboxing experience, hands revealing item from packaging, packaging details visible, first impressions moment, clean desk setup, anticipation feeling",
        icon="📱",
        order_num=5
    ),
    
    "tech_demo": PromptStyle(
        style_id="tech_demo",
        category="content_genre",
        name_th="เทค - สาธิตใช้งาน",
        name_en="Tech (Demo/Review)",
        description_th="สาธิตการใช้งาน ฟีเจอร์",
        description_en="Technology demonstration, feature showcase",
        prompt_injection="Technology demonstration, hands using device, feature showcase, UI close-ups where relevant, modern tech environment, clean professional setup",
        icon="💻",
        order_num=6
    ),
    
    "fitness_workout": PromptStyle(
        style_id="fitness_workout",
        category="content_genre",
        name_th="ฟิตเนส - ออกกำลังกาย",
        name_en="Fitness (Workout)",
        description_th="ท่าออกกำลังกาย มีพลัง",
        description_en="Exercise movements, energy and motivation",
        prompt_injection="Dynamic exercise movements, gym or outdoor workout environment, energy and motivation, athletic performance, powerful movements, fitness inspiration",
        icon="💪",
        order_num=7
    ),
    
    "beauty_makeup": PromptStyle(
        style_id="beauty_makeup",
        category="content_genre",
        name_th="ความงาม - แต่งหน้า/สกินแคร์",
        name_en="Beauty (Makeup/Skincare)",
        description_th="แต่งหน้า สกินแคร์ ความงาม",
        description_en="Makeup application, beauty tutorial",
        prompt_injection="Makeup application or skincare routine, beauty tutorial style, cosmetic product close-ups, transformation process, soft flattering lighting, mirror reflections",
        icon="💄",
        order_num=8
    ),
    
    "education_lecture": PromptStyle(
        style_id="education_lecture",
        category="content_genre",
        name_th="การศึกษา - บรรยาย/สอน",
        name_en="Education (Lecture)",
        description_th="ให้ความรู้ บรรยาย กระดาน",
        description_en="Educational content, informative",
        prompt_injection="Educational content, whiteboard or presentation visible, informative setting, professional teacher or expert appearance, classroom or studio environment",
        icon="📚",
        order_num=9
    ),
    
    "storytime_drama": PromptStyle(
        style_id="storytime_drama",
        category="content_genre",
        name_th="เล่าเรื่อง - ดราม่า",
        name_en="Storytelling (Drama)",
        description_th="เล่าเรื่อง มีอารมณ์ ดราม่า",
        description_en="Dramatic storytelling, emotional moments",
        prompt_injection="Dramatic storytelling visuals, emotional moments, cinematic narrative feeling, expressive facial expressions, moody atmospheric lighting",
        icon="🎭",
        order_num=10
    ),
    
    # ========== VISUAL COMPOSITION (📐 การจัดองค์ประกอบ) ==========
    
    "centered_subject": PromptStyle(
        style_id="centered_subject",
        category="visual_composition",
        name_th="วัตถุตรงกลาง",
        name_en="Centered Subject",
        description_th="วัตถุหลักอยู่ตรงกลางเฟรม สมมาตร",
        description_en="Subject perfectly centered in frame",
        prompt_injection="Subject perfectly centered in frame, symmetrical composition, balanced visual weight, focus draws to center",
        icon="⬜",
        order_num=1
    ),
    
    "rule_of_thirds": PromptStyle(
        style_id="rule_of_thirds",
        category="visual_composition",
        name_th="กฎสามส่วน",
        name_en="Rule of Thirds",
        description_th="วัตถุอยู่บนเส้นแบ่งสาม ไดนามิก",
        description_en="Subject positioned on rule of thirds",
        prompt_injection="Subject positioned on rule of thirds intersection, dynamic composition, visual tension, professional framing",
        icon="📐",
        order_num=2
    ),
    
    "negative_space": PromptStyle(
        style_id="negative_space",
        category="visual_composition",
        name_th="พื้นที่ว่างเยอะ",
        name_en="Negative Space",
        description_th="มินิมอล พื้นที่ว่างเยอะ โปร่ง",
        description_en="Minimalist with abundant negative space",
        prompt_injection="Minimalist composition with abundant negative space, breathing room around subject, clean and uncluttered, modern aesthetic",
        icon="⬜",
        order_num=3
    ),
    
    "layered_depth": PromptStyle(
        style_id="layered_depth",
        category="visual_composition",
        name_th="หลายชั้น (มีความลึก)",
        name_en="Layered Depth",
        description_th="มีฉากหน้า ฉากหลัง สร้างความลึก",
        description_en="Foreground and background creating depth",
        prompt_injection="Foreground and background elements creating depth, layered composition, shallow depth of field, dimensional visual, leading lines",
        icon="🎚️",
        order_num=4
    ),
    
    "symmetrical": PromptStyle(
        style_id="symmetrical",
        category="visual_composition",
        name_th="สมมาตรสมบูรณ์",
        name_en="Perfect Symmetry",
        description_th="สมมาตรซ้าย-ขวาสมบูรณ์แบบ",
        description_en="Perfect symmetry, mirror-like composition",
        prompt_injection="Perfect symmetry, balanced visual, mirror-like composition, architectural or geometric precision, satisfying visual balance",
        icon="🪞",
        order_num=5
    ),
    
    "dynamic_diagonal": PromptStyle(
        style_id="dynamic_diagonal",
        category="visual_composition",
        name_th="แนวทแยง/ไดนามิก",
        name_en="Dynamic Diagonal",
        description_th="เส้นทแยง สร้างความเคลื่อนไหว",
        description_en="Diagonal lines creating movement",
        prompt_injection="Diagonal lines creating movement and energy, dynamic composition, visual tension through angles, energetic framing",
        icon="↗️",
        order_num=6
    ),
    
    # ========== COLOR & MOOD (🌈 โทนสีและอารมณ์) ==========
    
    "warm_inviting": PromptStyle(
        style_id="warm_inviting",
        category="color_mood",
        name_th="อบอุ่น น่าเข้าใกล้",
        name_en="Warm & Inviting",
        description_th="โทนส้ม เหลือง อบอุ่น เป็นมิตร",
        description_en="Warm orange/yellow tones, cozy",
        prompt_injection="Warm color palette, orange and golden tones, cozy and welcoming atmosphere, inviting feeling, sunset-like warmth",
        icon="🔥",
        order_num=1
    ),
    
    "cool_professional": PromptStyle(
        style_id="cool_professional",
        category="color_mood",
        name_th="เย็น มืออาชีพ",
        name_en="Cool & Professional",
        description_th="โทนฟ้า เทา ดูน่าเชื่อถือ",
        description_en="Cool blue/gray tones, corporate",
        prompt_injection="Cool color tones, blue and gray palette, corporate and trustworthy appearance, professional atmosphere, clean modern look",
        icon="❄️",
        order_num=2
    ),
    
    "vibrant_energetic": PromptStyle(
        style_id="vibrant_energetic",
        category="color_mood",
        name_th="สดใส มีพลัง",
        name_en="Vibrant & Energetic",
        description_th="สีจัด คอนทราสต์สูง มีพลัง",
        description_en="Saturated vibrant colors, high contrast",
        prompt_injection="Saturated vibrant colors, high contrast, energetic and youthful feeling, bold color choices, dynamic and lively atmosphere",
        icon="🌈",
        order_num=3
    ),
    
    "muted_elegant": PromptStyle(
        style_id="muted_elegant",
        category="color_mood",
        name_th="เอิร์ธโทน หรูหรา",
        name_en="Muted & Elegant",
        description_th="สีกลั้ว เอิร์ธโทน พรีเมียม",
        description_en="Desaturated earth tones, sophisticated",
        prompt_injection="Desaturated earth tones, muted sophisticated palette, premium elegant feel, understated luxury, refined aesthetic",
        icon="🤎",
        order_num=4
    ),
    
    "monochrome": PromptStyle(
        style_id="monochrome",
        category="color_mood",
        name_th="ขาวดำ ไทม์เลส",
        name_en="Monochrome",
        description_th="ขาวดำ คอนทราสต์สูง คลาสสิก",
        description_en="Black and white, artistic, timeless",
        prompt_injection="Black and white, high contrast monochrome, artistic and timeless, classic film aesthetic, dramatic shadows and highlights",
        icon="⬛",
        order_num=5
    ),
    
    "pastel_soft": PromptStyle(
        style_id="pastel_soft",
        category="color_mood",
        name_th="พาสเทล นุ่มนวล",
        name_en="Pastel & Soft",
        description_th="สีพาสเทล นุ่มนวล ผ่อนคลาย",
        description_en="Soft pastel colors, gentle and calming",
        prompt_injection="Soft pastel colors, gentle and calming palette, feminine aesthetic, dreamy atmosphere, light and airy feeling",
        icon="🩷",
        order_num=6
    ),
    
    "neon_cyber": PromptStyle(
        style_id="neon_cyber",
        category="color_mood",
        name_th="นีออน ไซเบอร์พังค์",
        name_en="Neon & Cyber",
        description_th="นีออน ยามค่ำ ล้ำอนาคต",
        description_en="Neon lights, cyberpunk, futuristic",
        prompt_injection="Neon lights, cyberpunk aesthetic, futuristic urban night, glowing colors, high-tech atmosphere, purple and cyan accents",
        icon="💜",
        order_num=7
    ),
}


# ============ HELPER FUNCTIONS ============

def get_styles_by_category(category: str) -> list[PromptStyle]:
    """Get all styles in a specific category, sorted by order_num"""
    styles = [s for s in PROMPT_STYLES.values() if s.category == category]
    return sorted(styles, key=lambda x: x.order_num)


def get_all_categories() -> list[str]:
    """Get list of all category IDs"""
    return ["subject_type", "content_genre", "visual_composition", "color_mood"]


def get_category_display_name(category: str) -> tuple[str, str, str]:
    """Get (icon, thai_name, english_name) for a category"""
    names = {
        "subject_type": ("👤", "ประเภทหัวข้อหลัก", "Subject Type"),
        "content_genre": ("🎭", "ประเภทเนื้อหา", "Content Genre"),
        "visual_composition": ("📐", "การจัดองค์ประกอบ", "Visual Composition"),
        "color_mood": ("🌈", "โทนสีและอารมณ์", "Color & Mood"),
    }
    return names.get(category, ("🎬", category, category))


def get_style_by_id(style_id: str) -> PromptStyle | None:
    """Get a specific style by ID"""
    return PROMPT_STYLES.get(style_id)


def build_style_prompt_injection(selected_styles: dict[str, str]) -> str:
    """
    Build combined prompt injection text from selected styles
    
    Args:
        selected_styles: Dict mapping category to style_id
                        e.g. {"subject_type": "with_person_presenter", "color_mood": "warm_inviting"}
    
    Returns:
        Combined prompt injection text
    """
    injections = []
    
    for category in get_all_categories():
        style_id = selected_styles.get(category)
        if style_id:
            style = get_style_by_id(style_id)
            if style:
                injections.append(style.prompt_injection)
    
    if not injections:
        return ""
    
    return " | ".join(injections)


def get_style_summary(selected_styles: dict[str, str], lang: str = "th") -> str:
    """
    Get human-readable summary of selected styles
    
    Args:
        selected_styles: Dict mapping category to style_id
        lang: "th" for Thai, "en" for English
    
    Returns:
        Summary string like "มีคน-พิธีกร / อาหาร / อบอุ่น"
    """
    parts = []
    
    for category in get_all_categories():
        style_id = selected_styles.get(category)
        if style_id:
            style = get_style_by_id(style_id)
            if style:
                name = style.name_th if lang == "th" else style.name_en
                parts.append(f"{style.icon} {name}")
    
    return " / ".join(parts) if parts else "Default (No style selected)"


# ============ STREAMLIT UI HELPERS ============

def render_style_selector(category: str, current_value: str = None) -> str | None:
    """
    Render a Streamlit selectbox for a style category
    Must be called within Streamlit context
    
    Args:
        category: Category ID (e.g., "subject_type")
        current_value: Currently selected style_id
    
    Returns:
        Selected style_id or None
    """
    import streamlit as st
    
    icon, name_th, name_en = get_category_display_name(category)
    styles = get_styles_by_category(category)
    
    # Build options: [None, style1, style2, ...]
    options = [None] + [s.style_id for s in styles]
    
    def format_option(style_id):
        if style_id is None:
            return "— ไม่เลือก (Default) —"
        style = get_style_by_id(style_id)
        return f"{style.icon} {style.name_th}" if style else style_id
    
    # Find current index
    current_index = 0
    if current_value in options:
        current_index = options.index(current_value)
    
    selected = st.selectbox(
        f"{icon} {name_th}",
        options=options,
        index=current_index,
        format_func=format_option,
        key=f"prompt_style_{category}",
        help=name_en
    )
    
    return selected
