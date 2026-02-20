"""
Application Constants
Centralized constant values for VDO Content
"""
from pathlib import Path

# Version
# Version — Single Source of Truth (must match package.json)
VERSION = "2.2.0"
APP_NAME = "VDO Content"

# ============ NEW 5-STEP WORKFLOW ============
# Step 1: สร้างโปรเจค
STEP_PROJECT = 0
# Step 2: กำหนดคอนเทนต์
STEP_CONTENT = 1
# Step 3: บทพูด
STEP_SCRIPT = 2
# Step 4: สร้าง Prompt Vdo
STEP_VIDEO_PROMPT = 3
# Step 5: อัพโหลดไฟล์
STEP_UPLOAD = 4
# Settings & Database
STEP_SETTINGS = 7
STEP_DATABASE = 6

# Legacy Page Constants (for backwards compatibility)
PAGE_HOME = STEP_PROJECT
PAGE_IDEATION = STEP_CONTENT
PAGE_SCRIPT = STEP_SCRIPT
PAGE_AUDIO_SYNC = STEP_SCRIPT
PAGE_VEO_PROMPTS = STEP_VIDEO_PROMPT
PAGE_ARCHIVE = STEP_UPLOAD
PAGE_DATABASE = STEP_DATABASE

# ============ CONTENT CATEGORIES ============
CONTENT_CATEGORIES = [
    ("food", "🍜 Food & Cooking"),
    ("lifestyle", "🏠 Lifestyle"),
    ("education", "📚 Education"),
    ("entertainment", "🎬 Entertainment"),
    ("business", "💼 Business"),
    ("tech", "💻 Technology"),
    ("travel", "✈️ Travel"),
    ("health", "🏃 Health & Fitness"),
    ("fashion", "👗 Fashion & Beauty"),
    ("news", "📰 News & Current Events"),
]

# ============ PLATFORMS ============
PLATFORMS = [
    ("youtube", "📺 YouTube"),
    ("tiktok", "🎵 TikTok"),
    ("instagram", "📸 Instagram"),
    ("facebook", "📘 Facebook"),
    ("x", "𝕏 X (Twitter)"),
    ("line", "💚 LINE"),
]

# ============ VIDEO FORMATS ============
VIDEO_FORMATS = [
    ("shorts", "⚡ Shorts (<60s)"),
    ("standard", "🎬 Standard (1-5min)"),
    ("longform", "📹 Long-form (>5min)"),
]

# ============ VIDEO TYPES ============
VIDEO_TYPES = [
    ("with_person", "👤 มีคน (Person-based)"),
    ("no_person", "📦 ไม่มีคน (B-roll/Product)"),
    ("mixed", "🔀 Mixed"),
]

# ============ VIDEO STYLES (Visual Theme) ============
VIDEO_STYLES = [
    ("", "🎨 ไม่ระบุ (AI เลือกเอง)"),
    ("minimal_clean", "🤍 Minimal & Clean — เรียบง่าย โทนสะอาดตา พื้นหลังว่าง"),
    ("nature_organic", "🌿 Nature & Organic — ธรรมชาติ โทนเขียว อบอุ่น"),
    ("cinematic_dark", "🎬 Cinematic Dark — โทนมืด ดราม่า แสงเลเซอร์/แสงริม"),
    ("warm_cozy", "☕ Warm & Cozy — อบอุ่น นุ่มนวล แสงนวลๆ"),
    ("neon_urban", "🌃 Neon & Urban — เมืองยามค่ำ แสงนีออน ไซเบอร์พังก์"),
    ("pastel_soft", "🧁 Pastel & Soft — สีพาสเทล หวานๆ สไตล์เกาหลี"),
    ("luxury_premium", "💎 Luxury & Premium — หรูหรา ทองคำ คลาสสิก"),
    ("vintage_retro", "📷 Vintage & Retro — ย้อนยุค ฟิล์ม สีจาง"),
    ("bright_energetic", "⚡ Bright & Energetic — สดใส มีพลัง สีสันจัด"),
    ("monochrome_bw", "🖤 Monochrome B&W — ขาวดำ คลาสสิก อาร์ต"),
    ("tropical_thai", "🌴 Tropical Thai — สไตล์ไทย สีสดใส วัฒนธรรมไทย"),
    ("futuristic_tech", "🤖 Futuristic & Tech — ไฮเทค ล้ำสมัย โฮโลแกรม"),
]

# ============ HOOK TYPES (วิธีเปิดคลิป) ============
HOOK_TYPES = [
    ("auto", "🤖 AI เลือกให้ — ให้ AI เลือกแบบที่เหมาะสมที่สุด"),
    ("question", "❓ คำถาม — ตั้งคำถามที่คนดูอยากรู้คำตอบ"),
    ("shocking_fact", "😱 Fact น่าตกใจ — เริ่มด้วยข้อมูลที่เซอร์ไพรส์"),
    ("pain_point", "😤 Pain Point — พูดถึงปัญหาที่คนดูเจอ"),
    ("story", "📖 เรื่องเล่า — เริ่มด้วยเรื่องราวที่ดึงดูด"),
    ("bold_claim", "💥 Bold Claim — เปิดด้วยคำกล่าวที่กล้าหาญ"),
]

# ============ CLOSING TYPES (วิธีปิดคลิป) ============
CLOSING_TYPES = [
    ("auto", "🤖 AI เลือกให้ — ให้ AI เลือกแบบที่เหมาะสมที่สุด"),
    ("cta_follow", "👆 CTA กดติดตาม — ชวนกดติดตามช่อง"),
    ("cta_share", "🔄 CTA แชร์ — ชวนแชร์ให้เพื่อน"),
    ("cta_comment", "💬 CTA คอมเม้นท์ — ถามคำถามให้คอมเม้นท์"),
    ("tease_next", "🔮 Tease ตอนต่อไป — สร้างความอยากรู้ตอนต่อไป"),
    ("summary_cta", "📋 สรุป + CTA — สรุปเนื้อหา + ชวนมีส่วนร่วม"),
]

# ============ DURATION TIERS (โครงสร้างตามความยาวคลิป) ============
DURATION_TIERS = {
    "short": {
        "range": (15, 60),
        "label": "⚡ สั้น (15-60 วินาที)",
        "structure": "Hook (1-2 ประโยค) → Main Point กระชับ (1-2 ข้อ) → CTA สั้น (1 ประโยค)",
        "structure_en": "Hook (1-2 sentences) → Main Point concise (1-2 points) → Short CTA (1 sentence)",
        "density": "สั้น กระชับ ตรงประเด็น เน้นสิ่งที่สำคัญที่สุด 1-2 ข้อเท่านั้น ไม่ต้องอธิบายลึก",
        "density_en": "Short, concise, straight to the point. Focus on 1-2 most important points only. No deep explanation needed.",
        "hook_guidance": "ใช้คำถามสั้น 1 ประโยค หรือ fact ที่น่าตกใจ 1 ข้อ — ต้องจบภายใน 3 วินาที",
        "hook_guidance_en": "Use a short 1-sentence question or 1 shocking fact — must finish within 3 seconds",
        "closing_guidance": "CTA สั้นกระชับ 1 ประโยค เช่น 'กดติดตามเลย!' หรือ 'ลองดูสิ!'",
        "closing_guidance_en": "Short 1-sentence CTA like 'Follow now!' or 'Try it!'",
        "max_points": 2,
        "num_scenes_hint": "3-8 ฉาก",
    },
    "medium": {
        "range": (61, 180),
        "label": "🎬 กลาง (1-3 นาที)",
        "structure": "Hook (2-3 ประโยค) → ปูพื้น/Context → Main Points (3-4 ข้อ) → สรุป → CTA",
        "structure_en": "Hook (2-3 sentences) → Context setup → Main Points (3-4 points) → Summary → CTA",
        "density": "ขยายรายละเอียดพอประมาณ มีตัวอย่างประกอบสั้นๆ อธิบายแต่ละประเด็นมากขึ้น",
        "density_en": "Moderate detail with brief examples. Explain each point more. Include supporting examples.",
        "hook_guidance": "ใช้เรื่องเล่าสั้นๆ 2-3 ประโยค หรือ สถิติที่น่าสนใจ + ตามด้วยคำถาม",
        "hook_guidance_en": "Use a short 2-3 sentence story or interesting statistic + follow with a question",
        "closing_guidance": "สรุปสั้นๆ + CTA ชวนติดตาม/แชร์/คอมเม้นท์",
        "closing_guidance_en": "Brief summary + CTA to follow/share/comment",
        "max_points": 4,
        "num_scenes_hint": "8-22 ฉาก",
    },
    "long": {
        "range": (181, 600),
        "label": "📹 ยาว (3-10 นาที)",
        "structure": "Hook (3-5 ประโยค) → ปัญหา/บริบท → Deep Dive (5-8 ข้อ + ตัวอย่าง) → Case Study/เปรียบเทียบ → สรุป → CTA + Tease ตอนต่อไป",
        "structure_en": "Hook (3-5 sentences) → Problem/Context → Deep Dive (5-8 points + examples) → Case Study/Comparison → Summary → CTA + Tease next",
        "density": "ลงรายละเอียดลึก มีตัวอย่างจริง มีข้อมูลสนับสนุน มี case study เปรียบเทียบ ใช้เวลาอธิบายแต่ละข้อ",
        "density_en": "Deep detail with real examples, supporting data, case studies, comparisons. Take time to explain each point thoroughly.",
        "hook_guidance": "ใช้เรื่องเล่าที่ดึงดูดอารมณ์ 3-5 ประโยค หรือ ปัญหาที่คนดูเผชิญอยู่จริงๆ + preview สิ่งที่จะได้เรียนรู้",
        "hook_guidance_en": "Use an emotionally engaging story 3-5 sentences or a real problem viewers face + preview what they'll learn",
        "closing_guidance": "สรุปครบจบทุกประเด็น + CTA ที่แข็งแรง + Tease เนื้อหาตอนต่อไป ให้คนดูอยากกลับมาดู",
        "closing_guidance_en": "Comprehensive summary + strong CTA + tease next episode to make viewers want to come back",
        "max_points": 8,
        "num_scenes_hint": "22-75 ฉาก",
    },
}


def get_duration_tier(target_duration: int) -> dict:
    """Get the appropriate duration tier for a given target duration."""
    for tier_key, tier in DURATION_TIERS.items():
        low, high = tier["range"]
        if low <= target_duration <= high:
            return {"tier_key": tier_key, **tier}
    # Default to medium if out of range
    if target_duration < 15:
        return {"tier_key": "short", **DURATION_TIERS["short"]}
    return {"tier_key": "long", **DURATION_TIERS["long"]}


# ============ VOICE PERSONALITIES ============
VOICE_PERSONALITIES = [
    ("warm_friendly", "😊 Warm & Friendly"),
    ("professional", "💼 Professional & Clear"),
    ("excited", "🎉 Excited & Energetic"),
    ("calm", "😌 Calm & Soothing"),
    ("authoritative", "🎯 Serious & Authoritative"),
    ("cheerful", "☀️ Bright & Cheerful"),
]

# Style Presets (from core.models)
STYLE_PRESETS = [
    "realistic",
    "cinematic",
    "animated",
    "documentary",
    "minimalist",
    "energetic"
]

# Supported Languages
LANGUAGES = {
    "th": "Thai (ไทย)",
    "en": "English"
}

# Voice Tones (legacy)
VOICE_TONES = [
    "professional",
    "casual",
    "energetic",
    "calm",
    "educational"
]

# File Extensions
SUPPORTED_AUDIO_FORMATS = [".mp3", ".wav", ".webm", ".m4a", ".ogg", ".flac"]
SUPPORTED_VIDEO_FORMATS = [".mp4", ".webm", ".mov", ".avi"]

# Cache TTL (seconds)
CACHE_TTL_SHORT = 60  # 1 minute
CACHE_TTL_MEDIUM = 300  # 5 minutes
CACHE_TTL_LONG = 3600  # 1 hour

# Workflow Limits
MAX_REVISIONS = 3  # Maximum proposal revision attempts
MIN_CHARACTER_LENGTH = 40  # Minimum character reference length

# Paths
DATA_DIR = Path(__file__).parent.parent.parent / "data" / "projects"
UPLOAD_DIR = Path(__file__).parent.parent.parent / "data" / "uploads"
