"""
Database Seed Data and Migrations
Initial data seeding and schema migration functions.
"""

import logging

from sqlalchemy import text, inspect

from .db_engine import engine, DATABASE_URL, get_db
from .db_models import (
    VisualTagDB, VideoProfileDB, StyleProfileDB,
    ContentCategoryDB, TargetAudienceDB, ContentGoalDB
)

logger = logging.getLogger("vdo_content.database")


# ============ Migrations ============

def migrate_add_video_profile_id():
    """Add video_profile_id column to projects table if it doesn't exist"""
    inspector = inspect(engine)
    columns = [col['name'] for col in inspector.get_columns('projects')]
    
    if 'video_profile_id' not in columns:
        with engine.connect() as conn:
            conn.execute(text("ALTER TABLE projects ADD COLUMN video_profile_id VARCHAR(50)"))
            conn.commit()
            logger.info("Migration: Added video_profile_id column to projects")


def migrate_add_direction_style():
    """Add direction_style and direction_custom_notes columns to projects table"""
    inspector = inspect(engine)
    columns = [col['name'] for col in inspector.get_columns('projects')]
    
    with engine.connect() as conn:
        if 'direction_style' not in columns:
            conn.execute(text("ALTER TABLE projects ADD COLUMN direction_style VARCHAR(50)"))
            logger.info("Migration: Added direction_style column to projects")
        
        if 'direction_custom_notes' not in columns:
            conn.execute(text("ALTER TABLE projects ADD COLUMN direction_custom_notes TEXT"))
            logger.info("Migration: Added direction_custom_notes column to projects")
        
        conn.commit()


def migrate_add_prompt_style_config():
    """Add prompt_style_config JSON column to projects table"""
    inspector = inspect(engine)
    columns = [col['name'] for col in inspector.get_columns('projects')]
    
    if 'prompt_style_config' not in columns:
        with engine.connect() as conn:
            conn.execute(text("ALTER TABLE projects ADD COLUMN prompt_style_config JSON"))
            conn.commit()
            logger.info("Migration: Added prompt_style_config column to projects")


def migrate_add_category_audience():
    """Add content_category_id and target_audience_id columns to projects table"""
    inspector = inspect(engine)
    columns = [col['name'] for col in inspector.get_columns('projects')]
    
    with engine.connect() as conn:
        if 'content_category_id' not in columns:
            if "sqlite" in DATABASE_URL:
                conn.execute(text("ALTER TABLE projects ADD COLUMN content_category_id TEXT"))
            else:
                conn.execute(text("ALTER TABLE projects ADD COLUMN content_category_id UUID"))
            logger.info("Migration: Added content_category_id column to projects")
        
        if 'target_audience_id' not in columns:
            if "sqlite" in DATABASE_URL:
                conn.execute(text("ALTER TABLE projects ADD COLUMN target_audience_id TEXT"))
            else:
                conn.execute(text("ALTER TABLE projects ADD COLUMN target_audience_id UUID"))
            logger.info("Migration: Added target_audience_id column to projects")
        
        conn.commit()


def migrate_add_content_goal_id():
    """Add content_goal_id column to projects table"""
    inspector = inspect(engine)
    columns = [col['name'] for col in inspector.get_columns('projects')]
    
    if 'content_goal_id' not in columns:
        with engine.connect() as conn:
            if "sqlite" in DATABASE_URL:
                conn.execute(text("ALTER TABLE projects ADD COLUMN content_goal_id TEXT"))
            else:
                conn.execute(text("ALTER TABLE projects ADD COLUMN content_goal_id UUID"))
            conn.commit()
            logger.info("Migration: Added content_goal_id column to projects")


def migrate_add_generated_content():
    """Add generated_content column to projects table"""
    inspector = inspect(engine)
    columns = [col['name'] for col in inspector.get_columns('projects')]
    
    if 'generated_content' not in columns:
        with engine.connect() as conn:
            conn.execute(text("ALTER TABLE projects ADD COLUMN generated_content TEXT"))
            conn.commit()
            logger.info("Migration: Added generated_content column to projects")


# ============ Seed Functions ============

def init_style_profiles(db):
    """Seed master style profiles (8 presets matching Video Profiles)"""
    logger.info("Seeding style profiles...")
    
    profiles = [
        {
            "name": "Vlog สบายๆ (Casual Vlog)",
            "description": "สไตล์ vlog ท่องเที่ยว ไลฟ์สไตล์",
            "config": {
                "mood": ["Bright & Airy (สว่างสดใส)"],
                "lighting": ["Natural Light (แสงธรรมชาติ)"],
                "camera_angle": ["Eye Level (ระดับสายตา)"],
                "shot_size": ["Medium Shot (ครึ่งตัว)"],
                "movement": "Handheld (Vlog/สมจริง)",
                "style": "Realistic (สมจริง)"
            }
        },
        {
            "name": "สาระให้ความรู้ (Educational)",
            "description": "การนำเสนอความรู้แบบมืออาชีพ",
            "config": {
                "mood": ["Professional (ทางการ)", "Calm & Peaceful (สงบ)"],
                "lighting": ["Studio Lighting (จัดแสง)", "Softbox (นุ่มนวล)"],
                "camera_angle": ["Eye Level (ระดับสายตา)"],
                "shot_size": ["Medium Shot (ครึ่งตัว)", "Close-up (ใบหน้า/วัตถุ)"],
                "movement": "Static (นิ่ง)",
                "style": "Documentary (สารคดี)"
            }
        },
        {
            "name": "โปรโมทสินค้า (Product Showcase)",
            "description": "นำเสนอผลิตภัณฑ์แบบหรูหรา",
            "config": {
                "mood": ["Luxury (หรูหรา)", "Professional (ทางการ)"],
                "lighting": ["Studio Lighting (จัดแสง)", "High Key (ไฮคีย์)"],
                "camera_angle": ["Eye Level (ระดับสายตา)", "Low Angle (มุมเสย)"],
                "shot_size": ["Close-up (ใบหน้า/วัตถุ)", "Macro (ระยะประชิด)"],
                "movement": "Slow Pan (แพนช้าๆ)",
                "style": "Product (สินค้า)"
            }
        },
        {
            "name": "อาหาร/ทำอาหาร (Cooking & Food)",
            "description": "ถ่ายทำอาหารสวยงามน่ารับประทาน",
            "config": {
                "mood": ["Warm & Cozy (อบอุ่น)"],
                "lighting": ["Natural Light (แสงธรรมชาติ)", "Golden Hour (แสงเช้า/เย็น)"],
                "camera_angle": ["High Angle (มุมกด)", "Eye Level (ระดับสายตา)"],
                "shot_size": ["Close-up (ใบหน้า/วัตถุ)", "Macro (ระยะประชิด)"],
                "movement": "Dolly In (ซูมเข้า)",
                "style": "Food (อาหาร)"
            }
        },
        {
            "name": "รีวิวเทคโนโลยี (Tech Review)",
            "description": "รีวิวสินค้าเทคโนโลยีแบบมืออาชีพ",
            "config": {
                "mood": ["Professional (ทางการ)", "Futuristic (ล้ำยุค)"],
                "lighting": ["Studio Lighting (จัดแสง)", "Cinematic Lighting (ดรามาติก)"],
                "camera_angle": ["Eye Level (ระดับสายตา)"],
                "shot_size": ["Medium Shot (ครึ่งตัว)", "Close-up (ใบหน้า/วัตถุ)"],
                "movement": "Static (นิ่ง)",
                "style": "Realistic (สมจริง)"
            }
        },
        {
            "name": "เล่าเรื่อง/Drama (Storytelling)",
            "description": "เล่าเรื่องแบบมีอารมณ์และดราม่า",
            "config": {
                "mood": ["Cinematic (หนัง)", "Dramatic (ดราม่า)", "Mysterious (ลึกลับ)"],
                "lighting": ["Cinematic Lighting (ดรามาติก)", "Moody/Low Key (โลว์คีย์)"],
                "camera_angle": ["Eye Level (ระดับสายตา)", "Low Angle (มุมเสย)"],
                "shot_size": ["Medium Shot (ครึ่งตัว)", "Close-up (ใบหน้า/วัตถุ)"],
                "movement": "Slow Pan (แพนช้าๆ)",
                "style": "Realistic (สมจริง)"
            }
        },
        {
            "name": "ออกกำลังกาย/สุขภาพ (Fitness & Health)",
            "description": "ออกกำลังกาย สุขภาพ wellness",
            "config": {
                "mood": ["Energetic (สนุกสนาน)", "Bright & Airy (สว่างสดใส)"],
                "lighting": ["Natural Light (แสงธรรมชาติ)", "Studio Lighting (จัดแสง)"],
                "camera_angle": ["Eye Level (ระดับสายตา)", "Low Angle (มุมเสย)"],
                "shot_size": ["Full Body (เต็มตัว)", "Medium Shot (ครึ่งตัว)"],
                "movement": "Tracking (ตามติด)",
                "style": "Realistic (สมจริง)"
            }
        },
        {
            "name": "เพลง/บันเทิง (Music & Entertainment)",
            "description": "เพลง MV บันเทิง",
            "config": {
                "mood": ["Energetic (สนุกสนาน)", "Playful (สนุกสนาน)", "Dramatic (ดราม่า)"],
                "lighting": ["Neon/Cyberpunk (นีออน)", "Cinematic Lighting (ดรามาติก)"],
                "camera_angle": ["Eye Level (ระดับสายตา)", "Low Angle (มุมเสย)"],
                "shot_size": ["Full Body (เต็มตัว)", "Medium Shot (ครึ่งตัว)"],
                "movement": "Tracking (ตามติด)",
                "style": "Realistic (สมจริง)"
            }
        }
    ]
    
    for p in profiles:
        profile = StyleProfileDB(
            name=p["name"],
            description=p["description"],
            config=p["config"]
        )
        db.add(profile)
    
    logger.info("Style profiles seeded (8 profiles)")


def init_visual_tags(db):
    """Seed default visual tags"""
    logger.info("Seeding visual tags...")
    
    seed_data = {
        "mood": [
            ("Bright & Airy (สว่างสดใส)", "bright and airy, optimistic atmosphere"),
            ("Cinematic (หนัง)", "cinematic atmosphere, high production value"),
            ("Warm & Cozy (อบอุ่น)", "warm tones, cozy atmosphere, inviting"),
            ("Dark & Moody (มืดขรึม)", "dark and moody, dramatic atmosphere"),
            ("Minimalist (มินิมอล)", "minimalist, clean, uncluttered"),
            ("Energetic (สนุกสนาน)", "energetic, vibrant, dynamic"),
            ("Professional (ทางการ)", "professional, corporate, trustworthy"),
            ("Vintage (ย้อนยุค)", "vintage style, retro aesthetic, nostalgic"),
            ("Futuristic (ล้ำยุค)", "futuristic, sci-fi, neon accents, high-tech"),
            ("Dreamy (เพ้อฝัน)", "dreamy, ethereal, soft focus, romantic"),
            ("Dramatic (ดราม่า)", "dramatic, intense, powerful, emotional"),
            ("Playful (สนุกสนาน)", "playful, fun, colorful, whimsical"),
            ("Mysterious (ลึกลับ)", "mysterious, suspenseful, enigmatic"),
            ("Calm & Peaceful (สงบ)", "calm, peaceful, zen, relaxing"),
            ("Urban (เมือง)", "urban, city life, metropolitan"),
            ("Nature (ธรรมชาติ)", "nature, organic, earthy, natural"),
            ("Luxury (หรูหรา)", "luxury, elegant, premium, sophisticated"),
            ("Gritty (ดิบ)", "gritty, raw, authentic, street style"),
            ("Romantic (โรแมนติก)", "romantic, love, soft, tender"),
            ("Epic (มหากาพย์)", "epic, grand scale, majestic, awe-inspiring")
        ],
        "lighting": [
            ("Natural Light (แสงธรรมชาติ)", "soft natural lighting"),
            ("Golden Hour (แสงเช้า/เย็น)", "golden hour lighting, warm sun rays"),
            ("Studio Lighting (จัดแสง)", "professional studio lighting, perfect exposure"),
            ("Neon/Cyberpunk (นีออน)", "neon lighting, colorful gels, cyberpunk style"),
            ("Cinematic Lighting (ดรามาติก)", "dramatic lighting, high contrast, rim light"),
            ("Softbox (นุ่มนวล)", "soft diffused lighting, no harsh shadows"),
            ("Blue Hour (แสงฟ้า)", "blue hour lighting, twilight, magical"),
            ("Backlit (แสงหลัง)", "backlit, silhouette, halo effect"),
            ("Hard Light (แสงแข็ง)", "hard light, sharp shadows, high contrast"),
            ("Ring Light (วงแหวน)", "ring light, even face lighting, beauty lighting"),
            ("Moody/Low Key (โลว์คีย์)", "low key lighting, dark shadows, dramatic"),
            ("High Key (ไฮคีย์)", "high key lighting, bright, minimal shadows"),
            ("Candlelight (เทียน)", "candlelight, warm glow, intimate"),
            ("Moonlight (แสงจันทร์)", "moonlight, cool blue tones, night"),
            ("Fluorescent (ฟลูออเรสเซนต์)", "fluorescent lighting, office, industrial"),
            ("Mixed Lighting (แสงผสม)", "mixed lighting sources, creative color mix"),
            ("Volumetric (หมอกแสง)", "volumetric lighting, fog, light rays, atmospheric"),
            ("Sunbeam (ลำแสง)", "sunbeam, god rays, rays of light through clouds")
        ],
        "camera_angle": [
            ("Eye Level (ระดับสายตา)", "eye-level shot"),
            ("Low Angle (มุมเสย)", "low angle shot, looking up, imposing"),
            ("High Angle (มุมกด)", "high angle shot, looking down"),
            ("Aerial/Drone (โดรน)", "aerial drone shot, establishing view"),
            ("Dutch Angle (เอียง)", "dutch angle, tilted frame, dynamic"),
            ("Over the Shoulder (ข้ามไหล่)", "over-the-shoulder shot"),
            ("Bird's Eye View (มุมนก)", "bird's eye view, top-down, overhead"),
            ("Worm's Eye View (มุมหนอน)", "worm's eye view, extreme low angle"),
            ("POV (มุมมองตัวละคร)", "point of view shot, first person"),
            ("Two Shot (สองคน)", "two shot, framing two subjects"),
            ("Profile (ด้านข้าง)", "profile shot, side angle"),
            ("Three-Quarter (สามส่วน)", "three-quarter angle, 45 degree"),
            ("Front (ด้านหน้า)", "frontal shot, straight on"),
            ("Behind (ด้านหลัง)", "behind shot, back of subject"),
            ("Canted (เอียงมาก)", "canted frame, extreme tilt, disorienting")
        ],
        "shot_size": [
            ("Wide Shot (ภาพกว้าง)", "wide shot, establishing the scene"),
            ("Medium Shot (ครึ่งตัว)", "medium shot, focus on subject"),
            ("Close-up (ใบหน้า/วัตถุ)", "close-up shot, detailed"),
            ("Macro (ระยะประชิด)", "macro shot, extreme detail, texture"),
            ("Full Body (เต็มตัว)", "full body shot"),
            ("Extreme Wide (กว้างมาก)", "extreme wide shot, epic landscape"),
            ("Medium Close-up (กลางใกล้)", "medium close-up, chest up"),
            ("Extreme Close-up (ใกล้มาก)", "extreme close-up, eyes only, tiny details"),
            ("Long Shot (ไกล)", "long shot, subject small in frame"),
            ("Cowboy Shot (เอว)", "cowboy shot, mid-thigh up"),
            ("Insert Shot (รายละเอียด)", "insert shot, detail of object"),
            ("Cutaway (ตัดไป)", "cutaway shot, secondary element"),
            ("Establishing (เปิดฉาก)", "establishing shot, scene location"),
            ("Master Shot (ภาพหลัก)", "master shot, full scene coverage")
        ],
        "movement": [
            ("Static (นิ่ง)", "static camera, tripod shot"),
            ("Handheld (Vlog/สมจริง)", "handheld camera movement, organic feel"),
            ("Slow Pan (แพนช้าๆ)", "slow smooth panning shot"),
            ("Dolly In (ซูมเข้า)", "slow dolly in, pushing towards subject"),
            ("Tracking (ตามติด)", "tracking shot, following the subject"),
            ("Slow Motion (สโลว์)", "slow motion, cinematic framerate"),
            ("Dolly Out (ซูมออก)", "dolly out, pulling away from subject"),
            ("Tilt Up (เงยขึ้น)", "tilt up, revealing from bottom to top"),
            ("Tilt Down (ก้มลง)", "tilt down, revealing from top to bottom"),
            ("Pedestal (ยกขึ้น/ลง)", "pedestal movement, camera moves up/down"),
            ("Crane/Jib (เครน)", "crane shot, sweeping elevated movement"),
            ("Steadicam (เดินสมูท)", "steadicam shot, smooth walking movement"),
            ("Whip Pan (แพนเร็ว)", "whip pan, fast transition pan"),
            ("Zoom In (ซูมอิน)", "zoom in, optical zoom effect"),
            ("Zoom Out (ซูมเอาท์)", "zoom out, revealing wider view"),
            ("360 Orbit (วนรอบ)", "360 orbit shot, rotating around subject"),
            ("Push In (เข้าใกล้)", "push in, slow approaching movement"),
            ("Pull Back (ถอยออก)", "pull back reveal, dramatic reveal"),
            ("Arc Shot (โค้ง)", "arc shot, moving in curve around subject"),
            ("Time Lapse (ไทม์แลปส์)", "time lapse, accelerated motion"),
            ("Hyperlapse (ไฮเปอร์แลปส์)", "hyperlapse, moving time lapse")
        ],
        "style": [
            ("Realistic (สมจริง)", "photorealistic, 4k, highly detailed"),
            ("3D Animation (3D)", "3D animation style, Pixar style, smooth"),
            ("Anime (อนิเมะ)", "anime style, Makoto Shinkai style, vibrant"),
            ("Digital Art (ดิจิทัล)", "digital art, concept art, trending on artstation"),
            ("Oil Painting (สีน้ำมัน)", "oil painting style, brush strokes"),
            ("Watercolor (สีน้ำ)", "watercolor painting style, soft edges, flowing"),
            ("Cartoon (การ์ตูน)", "cartoon style, animated, stylized"),
            ("Comic Book (คอมมิค)", "comic book style, bold lines, halftone"),
            ("Sketch (สเกตช์)", "sketch style, pencil drawing, artistic"),
            ("Vintage Film (ฟิล์มย้อนยุค)", "vintage film grain, 35mm, nostalgic"),
            ("Cyberpunk (ไซเบอร์พังค์)", "cyberpunk style, neon, futuristic dystopia"),
            ("Steampunk (สตีมพังค์)", "steampunk style, Victorian era, brass gears"),
            ("Fantasy (แฟนตาซี)", "fantasy art style, magical, ethereal"),
            ("Documentary (สารคดี)", "documentary style, authentic, journalistic"),
            ("Fashion (แฟชั่น)", "fashion photography style, editorial, high-end"),
            ("Portrait (พอร์เทรต)", "portrait photography, professional headshot"),
            ("Product (สินค้า)", "product photography, clean, commercial"),
            ("Food (อาหาร)", "food photography, appetizing, styled"),
            ("Nature (ธรรมชาติ)", "nature photography, wildlife, landscape"),
            ("Street (สตรีท)", "street photography, candid, urban life"),
            ("Abstract (แอ็บสแตรกต์)", "abstract art, non-representational, artistic"),
            ("Surreal (เซอร์เรียล)", "surreal, dreamlike, Salvador Dali inspired"),
            ("Noir (ฟิล์มนัวร์)", "film noir, black and white, dramatic shadows"),
            ("Pop Art (ป๊อปอาร์ต)", "pop art style, Andy Warhol, bold colors")
        ]
    }
    
    for category, items in seed_data.items():
        for i, (label, value) in enumerate(items):
            tag = VisualTagDB(
                category=category,
                label=label,
                value=value,
                order_num=i
            )
            db.add(tag)
    
    logger.info("Visual tags seeded")


def init_video_profiles(db):
    """Seed master video profiles (8 content types)"""
    logger.info("Seeding video profiles...")
    
    profiles = [
        {
            "id": "vlog-lifestyle",
            "name_th": "Vlog สบายๆ",
            "name_en": "Casual Vlog",
            "description_th": "สไตล์ vlog ท่องเที่ยว ไลฟ์สไตล์ ญี่ปุ่น เกาหลี",
            "description_en": "Travel, lifestyle, daily vlog style",
            "icon": "📱",
            "order_num": 1,
            "config": {
                "mood": "bright_airy", "lighting": "natural", "camera_angle": "eye_level",
                "shot_size": "medium", "movement": "handheld", "style": "realistic",
                "prompt_suffix": "bright and airy atmosphere, natural lighting, handheld camera, vlog style, casual and inviting, 4K quality",
                "voice_speed": 1.0, "aspect_ratio_default": "9:16"
            }
        },
        {
            "id": "educational",
            "name_th": "สาระให้ความรู้",
            "name_en": "Educational",
            "description_th": "สารคดี วิชาการ How-to ให้ความรู้",
            "description_en": "Documentary, how-to, informative content",
            "icon": "📚",
            "order_num": 2,
            "config": {
                "mood": "professional", "lighting": "studio", "camera_angle": "eye_level",
                "shot_size": "medium", "movement": "static", "style": "realistic",
                "prompt_suffix": "professional, clean composition, informative style, studio lighting, educational content, clear and focused, 4K quality",
                "voice_speed": 0.9, "aspect_ratio_default": "16:9"
            }
        },
        {
            "id": "product-showcase",
            "name_th": "โปรโมทสินค้า",
            "name_en": "Product Showcase",
            "description_th": "รีวิวสินค้า Unboxing โฆษณา",
            "description_en": "Product review, unboxing, advertisement",
            "icon": "🛍️",
            "order_num": 3,
            "config": {
                "mood": "bright_airy", "lighting": "softbox", "camera_angle": "eye_level",
                "shot_size": "close_up", "movement": "slow_pan", "style": "realistic",
                "prompt_suffix": "professional product photography, soft diffused lighting, clean white background, detailed close-up, commercial quality, 4K HDR",
                "voice_speed": 0.95, "aspect_ratio_default": "16:9"
            }
        },
        {
            "id": "cooking-food",
            "name_th": "อาหาร/ทำอาหาร",
            "name_en": "Cooking & Food",
            "description_th": "สอนทำอาหาร รีวิวร้านอาหาร",
            "description_en": "Cooking tutorial, food review",
            "icon": "🍳",
            "order_num": 4,
            "config": {
                "mood": "warm_cozy", "lighting": "golden_hour", "camera_angle": "high_angle",
                "shot_size": "close_up", "movement": "slow_pan", "style": "realistic",
                "prompt_suffix": "warm tones, appetizing food photography, golden hour lighting, cozy atmosphere, delicious looking, close-up details, 4K quality",
                "voice_speed": 0.95, "aspect_ratio_default": "16:9"
            }
        },
        {
            "id": "tech-review",
            "name_th": "รีวิวเทคโนโลยี",
            "name_en": "Tech Review",
            "description_th": "รีวิว Gadget เทคโนโลยี",
            "description_en": "Technology, gadget reviews",
            "icon": "💻",
            "order_num": 5,
            "config": {
                "mood": "futuristic", "lighting": "neon", "camera_angle": "low_angle",
                "shot_size": "close_up", "movement": "dolly_in", "style": "realistic",
                "prompt_suffix": "sleek modern aesthetic, futuristic lighting, high-tech atmosphere, neon accents, professional tech review, clean minimalist, 4K HDR",
                "voice_speed": 1.0, "aspect_ratio_default": "16:9"
            }
        },
        {
            "id": "storytelling",
            "name_th": "เล่าเรื่อง/Drama",
            "name_en": "Storytelling",
            "description_th": "เล่าเรื่อง ดราม่า อารมณ์",
            "description_en": "Story, drama, emotional content",
            "icon": "🎭",
            "order_num": 6,
            "config": {
                "mood": "cinematic", "lighting": "cinematic", "camera_angle": "dutch_angle",
                "shot_size": "wide", "movement": "tracking", "style": "cinematic",
                "prompt_suffix": "cinematic lighting, dramatic atmosphere, film look, professional color grading, emotional storytelling, high contrast, 4K cinema quality",
                "voice_speed": 0.9, "aspect_ratio_default": "16:9"
            }
        },
        {
            "id": "fitness-health",
            "name_th": "ออกกำลังกาย/สุขภาพ",
            "name_en": "Fitness & Health",
            "description_th": "ออกกำลังกาย สุขภาพ Wellness",
            "description_en": "Fitness, wellness, health content",
            "icon": "💪",
            "order_num": 7,
            "config": {
                "mood": "energetic", "lighting": "natural", "camera_angle": "low_angle",
                "shot_size": "full_body", "movement": "tracking", "style": "realistic",
                "prompt_suffix": "dynamic energetic atmosphere, bright lighting, motivational feel, active lifestyle, vibrant colors, fitness motivation, 4K quality",
                "voice_speed": 1.1, "aspect_ratio_default": "9:16"
            }
        },
        {
            "id": "music-entertainment",
            "name_th": "เพลง/บันเทิง",
            "name_en": "Music & Entertainment",
            "description_th": "MV เพลง Performance บันเทิง",
            "description_en": "Music video, performance, entertainment",
            "icon": "🎵",
            "order_num": 8,
            "config": {
                "mood": "dark_moody", "lighting": "neon", "camera_angle": "dutch_angle",
                "shot_size": "medium", "movement": "slow_motion", "style": "cinematic",
                "prompt_suffix": "music video aesthetic, creative lighting, neon colors, artistic composition, performance style, dramatic atmosphere, 4K cinematic",
                "voice_speed": 1.0, "aspect_ratio_default": "16:9"
            }
        }
    ]
    
    for p in profiles:
        profile = VideoProfileDB(
            id=p["id"], name_th=p["name_th"], name_en=p["name_en"],
            description_th=p["description_th"], description_en=p["description_en"],
            icon=p["icon"], order_num=p["order_num"], config=p["config"],
            is_active=True, is_system=True
        )
        db.add(profile)
    
    logger.info("Video profiles seeded (8 profiles)")


def init_content_categories(db):
    """Seed content categories - หัวแหน่งเนื้อหา"""
    logger.info("Seeding content categories...")
    
    categories = [
        {"name_th": "รีวิวสินค้า/บริการ", "name_en": "Product/Service Review", "description": "รีวิวผลิตภัณฑ์หรือบริการต่างๆ", "icon": "⭐", "order_num": 1},
        {"name_th": "สาระความรู้", "name_en": "Educational", "description": "เนื้อหาให้ความรู้ สาระประโยชน์", "icon": "📚", "order_num": 2},
        {"name_th": "บันเทิง", "name_en": "Entertainment", "description": "เนื้อหาความบันเทิง ตลก สนุกสนาน", "icon": "🎭", "order_num": 3},
        {"name_th": "Tutorial/How-to", "name_en": "Tutorial", "description": "สอนวิธีการทำสิ่งต่างๆ", "icon": "🎓", "order_num": 4},
        {"name_th": "ข่าวสาร", "name_en": "News", "description": "ข่าวสารและเหตุการณ์ปัจจุบัน", "icon": "📰", "order_num": 5},
        {"name_th": "ไลฟ์สไตล์", "name_en": "Lifestyle", "description": "ไลฟ์สไตล์ Vlog การใช้ชีวิต", "icon": "✨", "order_num": 6},
        {"name_th": "อาหาร/ท่องเที่ยว", "name_en": "Food/Travel", "description": "อาหาร ร้านอาหาร สถานที่ท่องเที่ยว", "icon": "🍽️", "order_num": 7},
        {"name_th": "อื่นๆ", "name_en": "Others", "description": "หมวดหมู่อื่นๆ", "icon": "📌", "order_num": 8},
    ]
    
    for cat in categories:
        db.add(ContentCategoryDB(**cat, is_active=True))
    
    logger.info("Content categories seeded (8 categories)")


def init_content_goals(db):
    """Seed content goals - เป้าหมายเนื้อหา"""
    logger.info("Seeding content goals...")
    
    goals = [
        {"name_th": "สอนให้ความรู้", "name_en": "Educate", "description": "ให้ความรู้ สอนทักษะ อธิบายเรื่องยากให้เข้าใจง่าย", "icon": "📚", "prompt_hint": "เนื้อหาต้องอธิบายชัดเจน มีขั้นตอน ใช้ภาษาง่ายๆ เน้นความเข้าใจของผู้ชม", "order_num": 1},
        {"name_th": "รีวิว/แนะนำสินค้า", "name_en": "Product Review", "description": "รีวิวสินค้า บริการ หรือสถานที่", "icon": "⭐", "prompt_hint": "เนื้อหาต้องซื่อสัตย์ แสดงข้อดีข้อเสีย มีรายละเอียดที่เป็นประโยชน์ต่อการตัดสินใจซื้อ", "order_num": 2},
        {"name_th": "โปรโมทแบรนด์", "name_en": "Brand Promotion", "description": "สร้างการรับรู้แบรนด์ โฆษณา ประชาสัมพันธ์", "icon": "📢", "prompt_hint": "เนื้อหาต้องสร้างความน่าสนใจ เน้นจุดเด่นของแบรนด์ กระตุ้นให้ผู้ชมจดจำและติดตาม", "order_num": 3},
        {"name_th": "ให้ความบันเทิง", "name_en": "Entertain", "description": "สร้างความสนุก ตลก ผ่อนคลาย", "icon": "🎭", "prompt_hint": "เนื้อหาต้องสนุก มีมุกตลก หรือสถานการณ์ที่น่าสนใจ ดึงดูดให้ดูจนจบ", "order_num": 4},
        {"name_th": "สร้างแรงบันดาลใจ", "name_en": "Inspire", "description": "สร้างแรงบันดาลใจ กำลังใจ แรงจูงใจ", "icon": "💪", "prompt_hint": "เนื้อหาต้องกระตุ้นอารมณ์ ให้กำลังใจ มีเรื่องราวที่สร้างแรงบันดาลใจ ใช้ภาษาที่ทรงพลัง", "order_num": 5},
        {"name_th": "ข่าวสาร/อัปเดต", "name_en": "News & Updates", "description": "อัปเดตข่าวสาร เทรนด์ สถานการณ์", "icon": "📰", "prompt_hint": "เนื้อหาต้องกระชับ ตรงประเด็น อัปเดตล่าสุด ใช้ข้อมูลที่น่าเชื่อถือ", "order_num": 6},
        {"name_th": "เล่าเรื่อง/Storytelling", "name_en": "Storytelling", "description": "เล่าเรื่องราว สร้างเรื่องเล่าที่น่าสนใจ", "icon": "📖", "prompt_hint": "เนื้อหาต้องมีโครงสร้างเรื่องที่ดี มีจุดเริ่ม กลาง จบ ดึงดูดอารมณ์ผู้ชม ใช้เทคนิค storytelling", "order_num": 7},
        {"name_th": "ขายของ/E-Commerce", "name_en": "Sales & E-Commerce", "description": "ขายสินค้าออนไลน์ กระตุ้นยอดขาย", "icon": "🛒", "prompt_hint": "เนื้อหาต้องมี call-to-action ชัดเจน แสดงราคา โปรโมชัน สร้างความเร่งด่วน กระตุ้นการตัดสินใจซื้อ", "order_num": 8},
    ]
    
    for goal in goals:
        db.add(ContentGoalDB(**goal, is_active=True))
    
    logger.info("Content goals seeded (8 goals)")


def init_target_audiences(db):
    """Seed target audiences - กลุ่มเป้าหมาย"""
    logger.info("Seeding target audiences...")
    
    audiences = [
        {"name_th": "วัยรุ่น", "name_en": "Teenagers", "age_range": "13-17 ปี", "description": "นักเรียน วัยรุ่น", "order_num": 1},
        {"name_th": "เยาวชน Gen Z", "name_en": "Young Adults (Gen Z)", "age_range": "18-25 ปี", "description": "นักศึกษา Gen Z วัยเริ่มทำงาน", "order_num": 2},
        {"name_th": "วัยทำงาน", "name_en": "Working Adults", "age_range": "25-35 ปี", "description": "กลุ่มวัยทำงานยุคใหม่", "order_num": 3},
        {"name_th": "มืออาชีพ", "name_en": "Professionals", "age_range": "35-50 ปี", "description": "ผู้บริหาร มืออาชีพ กำลังซื้อสูง", "order_num": 4},
        {"name_th": "แม่บ้าน/ครอบครัว", "name_en": "Homemakers/Families", "age_range": "25-50 ปี", "description": "แม่บ้าน ครอบครัว พ่อแม่ลูก", "order_num": 5},
        {"name_th": "ผู้สูงอายุ", "name_en": "Seniors", "age_range": "50+ ปี", "description": "กลุ่มผู้สูงอายุ วัยเกษียณ", "order_num": 6},
        {"name_th": "ทั่วไป", "name_en": "General Public", "age_range": "ทุกวัย", "description": "กลุ่มเป้าหมายทั่วไป ไม่จำกัดอายุ", "order_num": 7},
    ]
    
    for aud in audiences:
        db.add(TargetAudienceDB(**aud, is_active=True))
    
    logger.info("Target audiences seeded (7 audiences)")
