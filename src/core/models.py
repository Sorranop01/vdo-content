"""
Data Models for VDO Content V2
SSOT (Single Source of Truth) for all data structures
"""

from pydantic import BaseModel, Field
from typing import Optional, Literal
from datetime import datetime
import uuid


# ============ Story Proposal (NEW) ============

class StoryProposal(BaseModel):
    """Story proposal with approval workflow"""
    
    proposal_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    topic: str
    
    # AI Analysis
    analysis: str = ""  # AI วิเคราะห์โจทย์
    outline: list[str] = []  # โครงเรื่อง
    key_points: list[str] = []  # จุดสำคัญ
    
    # Approval workflow
    status: Literal["pending", "approved", "rejected"] = "pending"
    feedback: str = ""  # User feedback if rejected
    version: int = 1  # 1-3 (max 3 revisions)
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.now)


# ============ Audio Segment (NEW) ============

class AudioSegment(BaseModel):
    """Audio segment with timing info"""
    
    order: int
    start_time: float  # seconds
    end_time: float
    duration: float
    
    # Content mapping
    text_content: str = ""  # Mapped narration text
    is_edited: bool = False  # User manually edited
    
    @property
    def time_range(self) -> str:
        """Format as MM:SS - MM:SS"""
        def fmt(t: float) -> str:
            mins = int(t // 60)
            secs = t % 60
            return f"{mins}:{secs:05.2f}"
        return f"{fmt(self.start_time)} - {fmt(self.end_time)}"


# ============ Scene (Updated) ============

class Scene(BaseModel):
    """Single Source of Truth for each scene"""
    
    # Identity
    scene_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    order: int
    
    # Audio timing (NEW)
    start_time: float = 0.0  # seconds from audio start
    end_time: float = 0.0
    
    # Narration
    narration_text: str
    word_count: int = 0
    estimated_duration: float = Field(default=0.0, description="seconds, should be ≤8")
    
    # Visual
    veo_prompt: str = ""
    voiceover_prompt: str = ""  # Thai voiceover text (pure narration, no emotion)
    voice_tone: str = ""  # English voice tone direction (tone, pacing, emotion)
    visual_style: Literal["realistic", "cinematic", "animated", "documentary", "minimalist", "energetic"] = "documentary"
    camera_movement: Optional[str] = None
    subject_description: str = ""
    
    # Sync helpers
    emotion: str = "neutral"
    transition: Literal["cut", "fade", "dissolve"] = "cut"
    
    # Status tracking
    prompt_copied: bool = False
    video_generated: bool = False
    stock_video_url: str = ""  # For stock video selection
    audio_synced: bool = False
    notes: str = ""
    
    # Quality scoring (Phase 2)
    quality_score: float = 0.0
    quality_suggestions: list[str] = []
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: Optional[datetime] = None
    

    @property
    def audio_duration(self) -> float:
        """Duration from audio timing"""
        return round(self.end_time - self.start_time, 2)
    
    @property
    def time_range(self) -> str:
        """Format as MM:SS - MM:SS"""
        def fmt(t: float) -> str:
            mins = int(t // 60)
            secs = t % 60
            return f"{mins}:{secs:04.1f}"
        return f"{fmt(self.start_time)} - {fmt(self.end_time)}"
    
    def model_post_init(self, __context) -> None:
        """Calculate word count and duration after init"""
        if self.narration_text and self.word_count == 0:
            self.word_count = len(self.narration_text.split())
        if self.word_count > 0 and self.estimated_duration == 0:
            self.estimated_duration = round(self.word_count / 2.5, 1)


# ============ Project (Updated for 5-Step Workflow) ============

class Project(BaseModel):
    """Content project containing multiple scenes"""
    
    project_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    topic: str = ""
    description: str = ""
    project_date: Optional[datetime] = Field(default_factory=datetime.now)
    
    # ============ STEP 2: Content Planning ============
    content_goal: str = ""              # เป้าหมายเนื้อหา
    content_category: str = ""          # หมวดหมู่เนื้อหา (legacy)
    target_audience: str = ""           # กลุ่มเป้าหมาย (legacy)
    
    # NEW: Database references
    content_category_id: Optional[str] = None  # UUID reference to content_categories table
    target_audience_id: Optional[str] = None   # UUID reference to target_audiences table
    content_goal_id: Optional[str] = None      # UUID reference to content_goals table
    
    platforms: list[str] = []           # ช่องทางแพลตฟอร์ม
    video_format: str = ""              # รูปแบบวีดีโอ (shorts, standard, longform)
    content_description: str = ""       # รายละเอียดเนื้อหา
    generated_content: str = ""         # เนื้อหาที่ AI สร้าง
    
    # Story proposal
    proposal: Optional[StoryProposal] = None
    
    # ============ STEP 3: Script/Audio ============
    voice_personality: str = ""         # บุคลิกน้ำเสียง
    full_script: str = ""
    target_duration: int = 60
    style_instructions: str = ""
    script_text: str = ""
    audio_path: Optional[str] = None
    audio_duration: float = 0.0
    audio_segments: list[AudioSegment] = []
    
    # ============ STEP 4: Video Prompts ============
    video_type: str = ""                # ประเภทวีดีโอ (with_person, no_person, mixed)
    scenes: list[Scene] = []
    
    # Visual Settings
    default_style: Literal["realistic", "cinematic", "animated", "documentary", "minimalist", "energetic"] = "documentary"
    video_profile_id: Optional[str] = None
    character_reference: str = ""
    visual_theme: str = ""
    directors_note: str = ""
    aspect_ratio: str = "16:9"
    direction_style: Optional[str] = None
    direction_custom_notes: str = ""
    prompt_style_config: Optional[dict] = None
    
    # ============ STEP 5: Upload ============
    upload_folder: str = ""             # โฟลเดอร์ที่สร้าง (YYYYMMDD-project_name)
    uploaded_files: list[str] = []      # รายการไฟล์ที่อัพโหลด
    final_video_path: Optional[str] = None
    drive_folder_link: str = ""
    
    # ============ Metadata ============
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: Optional[datetime] = None
    # Updated status to match 5-step workflow
    status: Literal["step1_project", "step2_content", "step3_script", "step4_prompt", "step5_upload", "completed"] = "step1_project"
    # Legacy status mapping
    workflow_step: int = 0              # Current step (0-4)
    
    @property
    def total_duration(self) -> float:
        """Use audio_duration when available, fall back to estimated_duration"""
        return sum(
            scene.audio_duration if scene.audio_duration > 0 else scene.estimated_duration
            for scene in self.scenes
        )
    
    @property
    def scene_count(self) -> int:
        return len(self.scenes)
    
    @property
    def completed_scenes(self) -> int:
        return sum(1 for s in self.scenes if s.video_generated)


# ============ Style Presets ============

class StylePreset(BaseModel):
    """Preset styling options for video generation"""
    
    name: str
    description: str
    lighting: str
    color_grade: str
    quality_tags: list[str] = ["high quality", "4K", "professional"]
    default_camera: str = "medium shot"
    prompt_suffix: str = ""
    
    # AI Studio voice settings (NEW)
    voice_speed: float = 1.0
    voice_style: str = "neutral"


STYLE_PRESETS: dict[str, StylePreset] = {
    "documentary": StylePreset(
        name="Documentary",
        description="สารคดี ให้ความรู้",
        lighting="natural",
        color_grade="neutral",
        quality_tags=["documentary style", "informative", "professional"],
        prompt_suffix="documentary style, informative, professional videography",
        voice_speed=0.9,
        voice_style="calm, informative"
    ),
    "realistic": StylePreset(
        name="Realistic",
        description="สมจริง เหมือนถ่ายจริง",
        lighting="natural",
        color_grade="neutral",
        quality_tags=["photorealistic", "high quality", "4K", "natural lighting"],
        prompt_suffix="photorealistic, natural lighting, high quality 4K video",
        voice_speed=1.0,
        voice_style="natural"
    ),
    "cinematic": StylePreset(
        name="Cinematic",
        description="สไตล์หนัง dramatic",
        lighting="dramatic",
        color_grade="warm",
        quality_tags=["cinematic", "4K", "professional color grading", "film look"],
        prompt_suffix="cinematic lighting, professional color grading, film look, 4K quality",
        voice_speed=0.95,
        voice_style="dramatic, engaging"
    ),
    "animated": StylePreset(
        name="Animated",
        description="การ์ตูน/แอนิเมชัน",
        lighting="soft",
        color_grade="vibrant",
        quality_tags=["animated", "colorful", "smooth animation"],
        prompt_suffix="animated style, colorful, smooth animation, vibrant colors",
        voice_speed=1.1,
        voice_style="energetic, friendly"
    ),
    "minimalist": StylePreset(
        name="Minimalist",
        description="เรียบง่าย สะอาดตา",
        lighting="soft",
        color_grade="muted",
        quality_tags=["minimalist", "clean", "modern"],
        prompt_suffix="minimalist style, clean composition, modern aesthetic",
        voice_speed=0.9,
        voice_style="calm, measured"
    ),
    "energetic": StylePreset(
        name="Energetic",
        description="มีพลัง กระตุ้น",
        lighting="bright",
        color_grade="vibrant",
        quality_tags=["dynamic", "energetic", "vibrant"],
        prompt_suffix="dynamic, energetic, vibrant colors, fast-paced",
        voice_speed=1.15,
        voice_style="enthusiastic, motivating"
    )
}


EMOTION_VISUALS: dict[str, dict] = {
    "motivational": {
        "lighting": "bright, uplifting",
        "colors": "warm, energetic",
        "expression": "determined, confident"
    },
    "calm": {
        "lighting": "soft, peaceful",
        "colors": "cool, muted",
        "expression": "relaxed, serene"
    },
    "urgent": {
        "lighting": "dramatic, high contrast",
        "colors": "bold, impactful",
        "expression": "focused, intense"
    },
    "happy": {
        "lighting": "bright, warm",
        "colors": "vibrant, cheerful",
        "expression": "smiling, joyful"
    },
    "neutral": {
        "lighting": "natural",
        "colors": "balanced",
        "expression": "natural"
    }
}
