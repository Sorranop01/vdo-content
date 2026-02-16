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
