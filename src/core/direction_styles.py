"""
Video Direction Styles Database
Defines visual storytelling approaches for Veo 3 generation

ไฟล์นี้เก็บ preset ของ direction styles ต่าง ๆ สำหรับการ generate Veo prompts
แต่ละ style จะมี instructions เฉพาะที่ช่วยให้ AI สร้าง prompts ที่เหมาะสม
"""

from pydantic import BaseModel, Field
from typing import Literal


class VideoDirectionStyle(BaseModel):
    """Video direction/editing style preset"""
    
    style_id: str = Field(description="Unique style identifier")
    name: str = Field(description="Display name (English)")
    description_th: str = Field(description="Thai description for users")
    description_en: str = Field(description="English description")
    
    # Prompt engineering - ส่วนที่จะถูก inject เข้า AI prompt
    veo_instructions: str = Field(description="Specific instructions for Veo 3 prompts")
    camera_guidance: str = Field(description="Camera movement and angle suggestions")
    transition_guidance: str = Field(description="Recommended transition types")
    
    # Examples and metadata
    example_prompt: str = Field(description="Example Veo prompt demonstrating this style")
    keywords: list[str] = Field(description="Keywords to include in prompts")
    
    # UI metadata
    icon: str = Field(default="🎬", description="Emoji icon for UI display")
    difficulty: Literal["beginner", "intermediate", "advanced"] = Field(
        default="intermediate",
        description="Difficulty level for users"
    )


# ============ PRESET DIRECTION STYLES ============

DIRECTION_STYLES: dict[str, VideoDirectionStyle] = {
    # Match Cut / Seamless Transition
    "match_cut": VideoDirectionStyle(
        style_id="match_cut",
        name="Match Cut / Seamless Transition",
        description_th="การตัดต่อที่ลื่นไหล ภาพต่อเนื่องกัน องค์ประกอบคล้ายกัน เหมาะสำหรับเนื้อหาที่ต้องการความต่อเนื่อง",
        description_en="Seamless transitions where visual elements match between scenes for narrative continuity",
        
        veo_instructions="""Create smooth visual continuity between scenes. Match composition, subject position, or visual elements across cuts. Maintain consistent framing and visual flow. Use similar color palettes and lighting to create seamless transitions. The viewer should feel a continuous visual journey.""",
        
        camera_guidance="Keep camera angles and distances consistent between scenes. Maintain eye-line matches. Use similar shot compositions (e.g., if scene ends with medium shot, next scene starts with medium shot). Avoid jarring camera movement changes.",
        
        transition_guidance="cut, match dissolve, wipe with matching elements",
        
        example_prompt="Thai woman, early 30s, wearing casual pink t-shirt, standing in modern bedroom with arms folded, natural window lighting from left side, medium shot at eye level. Next scene: Same woman, same clothing, same lighting direction, now in kitchen with similar arm position, seamless visual continuity, photorealistic, 4K quality.",
        
        keywords=["seamless", "continuous flow", "matched composition", "consistent framing", "visual continuity"],
        
        icon="🔄",
        difficulty="advanced"
    ),
    
    # Stop Motion
    "stop_motion": VideoDirectionStyle(
        style_id="stop_motion",
        name="Stop Motion",
        description_th="ภาพเคลื่อนไหวแบบหยุดนิ่ง สไตล์ frame-by-frame มีเอกลักษณ์เฉพาะ เหมาะกับเนื้อหาสร้างสรรค์",
        description_en="Frame-by-frame animation style with visible incremental movements and stop-motion aesthetic",
        
        veo_instructions="""Create stop-motion animation aesthetic. Objects or subjects should appear to move in small, discrete incremental steps rather than smooth continuous motion. Add subtle position changes between frames. Include slight jitter or jerky movements characteristic of stop-motion. Maintain consistent lighting throughout. Think claymation or paper cutout animation style.""",
        
        camera_guidance="STATIC camera position only - absolutely no smooth camera movements. Camera should be locked on tripod. No pans, tilts, or zooms during the shot. The movement comes from the subject, not the camera.",
        
        transition_guidance="jump cut, hard cut, direct transition",
        
        example_prompt="Small coffee cup on wooden table, positioned slightly to the left. In the next frame, same cup moved 2 inches to the right with visible incremental position change. Static camera, overhead view, consistent warm interior lighting, stop-motion animation style, frame-by-frame aesthetic, slight jitter, handcrafted feel.",
        
        keywords=["frame-by-frame", "incremental movement", "stepped motion", "claymation style", "static camera", "handcrafted"],
        
        icon="📹",
        difficulty="advanced"
    ),
    
    # Cinematic B-Roll
    "cinematic_broll": VideoDirectionStyle(
        style_id="cinematic_broll",
        name="Cinematic B-Roll",
        description_th="ภาพประกอบสไตล์ภาพยนตร์ เน้นบรรยากาศและรายละเอียด เหมาะสำหรับเนื้อหาที่ต้องการความสวยงาม",
        description_en="Atmospheric supplementary footage with film-like quality, focusing on mood and environmental details",
        
        veo_instructions="""Create cinematic b-roll footage with film-like quality. Focus on atmospheric shots, environmental details, and emotional context rather than direct literal translation. Use dramatic lighting, shallow depth of field, and film grain. Emphasize mood and feeling. Include detail shots (hands, objects, textures) and establishing shots (wide environmental views). Think documentary or film supplementary footage.""",
        
        camera_guidance="Slow, deliberate, professional camera movements only: smooth dolly shots, slider movements, or gimbal stabilized shots. Use rack focus to shift attention between foreground and background. Include reveal shots and slow pans. Avoid handheld shakiness unless intentional for mood. Use cinematic angles (low angles, Dutch angles, over-the-shoulder).",
        
        transition_guidance="dissolve, fade to black, slow crossfade",
        
        example_prompt="Close-up of hands pouring coffee into ceramic mug, steam rising with dramatic backlight creating rim lighting effect, shallow depth of field with blurred cafe background, warm golden hour lighting through window, slow dolly in movement, cinematic film grain, 24fps feel, film look color grading, professional cinematography, establishing emotional mood.",
        
        keywords=["atmospheric", "establishing shot", "detail shot", "shallow depth of field", "cinematic quality", "film grain", "moody lighting", "professional cinematography"],
        
        icon="🎥",
        difficulty="intermediate"
    ),
    
    # Time-lapse
    "timelapse": VideoDirectionStyle(
        style_id="timelapse",
        name="Time-lapse",
        description_th="ภาพเคลื่อนไหวเร็ว แสดงการเปลี่ยนแปลงตามเวลา เหมาะสำหรับแสดงกระบวนการที่ใช้เวลานาน",
        description_en="Accelerated time showing changes over extended periods in compressed duration",
        
        veo_instructions="""Show passage of time through accelerated fast-motion photography. Demonstrate gradual changes happening over minutes, hours, or days compressed into seconds. Common subjects: clouds moving rapidly across sky, shadows shifting and rotating, sun moving across horizon, crowds flowing through spaces, plants growing, construction progressing, traffic streaming. Emphasize the transformation and temporal change.""",
        
        camera_guidance="COMPLETELY STATIC camera on sturdy tripod - absolutely essential for time-lapse. No camera movement whatsoever. Locked-off shot. The magic comes from temporal changes, not camera motion. Use wide or medium shots to show full context of change.",
        
        transition_guidance="cut, direct transition",
        
        example_prompt="Wide shot of city skyline at dawn, camera locked on tripod, clouds racing rapidly across sky, sun arcing quickly from horizon to midday position, shadows shortening and shifting dramatically, light changing from golden hour to harsh midday in seconds, time-lapse photography, accelerated motion, temporal compression, 4K quality.",
        
        keywords=["accelerated motion", "time passage", "temporal change", "fast motion", "transformation", "static camera", "locked-off shot"],
        
        icon="⏩",
        difficulty="beginner"
    ),
    
    # Slow Motion
    "slow_motion": VideoDirectionStyle(
        style_id="slow_motion",
        name="Slow Motion",
        description_th="ภาพเคลื่อนไหวช้า เน้นความดราม่าและรายละเอียด เหมาะสำหรับ highlight จังหวะสำคัญ",
        description_en="Dramatic slow-motion for emphasis, emotional impact, and revealing details normally missed",
        
        veo_instructions="""Create dramatic slow-motion footage to emphasize key moments and reveal hidden details. Capture graceful movements, emotional expressions, and action sequences at reduced speed. Show details normally missed at regular speed: water droplets, fabric movement, facial micro-expressions, hair flowing. Use slow-motion for emotional emphasis, dramatic effect, or to highlight important actions. Think high-speed camera cinematography.""",
        
        camera_guidance="Smooth camera movements that complement the slowed action. Can use dramatic camera angles (low angle for power, high angle for vulnerability). Slow pans or tilts work well. Consider orbiting movements around subject. Floating, dreamlike camera motion enhances the slow-motion feel.",
        
        transition_guidance="fade, slow dissolve, gradual transition",
        
        example_prompt="Thai woman, 30s, turning head toward camera in extreme slow motion, hair flowing gracefully through air, subtle smile forming gradually, individual strands of hair visible, water droplets from hair falling slowly, dramatic side lighting creating highlights, soft focus background, dreamy atmosphere, high-speed camera cinematography, 120fps slow motion, cinematic quality.",
        
        keywords=["slow motion", "dramatic emphasis", "graceful movement", "high-speed camera", "detailed capture", "emotional impact", "dreamlike"],
        
        icon="🐌",
        difficulty="intermediate"
    ),
}


# Helper function to get style by ID
def get_direction_style(style_id: str) -> VideoDirectionStyle | None:
    """Get direction style by ID, returns None if not found"""
    return DIRECTION_STYLES.get(style_id)


# Helper function to list all styles
def list_all_direction_styles() -> list[VideoDirectionStyle]:
    """Get list of all available direction styles"""
    return list(DIRECTION_STYLES.values())


# Helper function to get style IDs
def get_style_ids() -> list[str]:
    """Get list of all style IDs"""
    return list(DIRECTION_STYLES.keys())
