"""
Thai-to-Visual Dictionary
Maps Thai keywords to specific English visual descriptions for Veo 3 prompt generation.
Used by both AI path (as visual anchors) and fallback path (direct mapping).
"""

from typing import NamedTuple


class VisualConcept(NamedTuple):
    """A visual concept mapped from Thai keyword"""
    subject: str        # Main visual subject
    action: str         # Visual action/movement
    setting: str        # Environment/background
    props: list[str]    # Key props/objects in frame
    mood: str           # Visual mood/atmosphere


# ============================================================
# FOOD & COOKING (30+ items)
# ============================================================

FOOD_VISUALS: dict[str, VisualConcept] = {
    # --- Clean/Healthy Food ---
    "อาหารคลีน": VisualConcept(
        subject="Colorful clean-eating meal plate",
        action="steam gently rises from freshly prepared dish",
        setting="Modern minimalist kitchen counter with marble surface",
        props=["grilled chicken breast", "quinoa", "fresh vegetables", "ceramic plate"],
        mood="bright, healthy, appetizing"
    ),
    "สลัด": VisualConcept(
        subject="Fresh vibrant salad bowl",
        action="dressing drizzles over crisp greens in slow motion",
        setting="Sunlit kitchen with natural light pouring in",
        props=["mixed greens", "cherry tomatoes", "avocado", "wooden bowl"],
        mood="fresh, natural, invigorating"
    ),
    "สมูทตี้": VisualConcept(
        subject="Colorful smoothie in tall glass",
        action="blender whirring with fruits, pouring into glass",
        setting="Bright modern kitchen counter",
        props=["blender", "fresh berries", "banana", "glass straw"],
        mood="energetic, refreshing, vibrant"
    ),
    "ข้าวกล้อง": VisualConcept(
        subject="Bowl of perfectly cooked brown rice",
        action="rice grains glistening, chopsticks lifting portion",
        setting="Warm-toned dining table with Asian aesthetics",
        props=["ceramic bowl", "chopsticks", "side dishes", "teapot"],
        mood="wholesome, earthy, comforting"
    ),
    "โปรตีน": VisualConcept(
        subject="Variety of protein sources arranged artfully",
        action="knife slicing through grilled meat, revealing juicy interior",
        setting="Professional kitchen prep station",
        props=["grilled salmon", "eggs", "tofu", "legumes", "cutting board"],
        mood="rich, satisfying, nourishing"
    ),
    "ผลไม้": VisualConcept(
        subject="Arrangement of tropical fruits",
        action="hands selecting ripe fruit, cutting reveals colorful interior",
        setting="Open-air tropical market or sunny kitchen",
        props=["mango", "papaya", "dragon fruit", "pineapple", "wooden board"],
        mood="tropical, colorful, fresh"
    ),
    "ผัก": VisualConcept(
        subject="Fresh colorful vegetables on display",
        action="water droplets roll off freshly washed vegetables",
        setting="Kitchen with natural light, farm-to-table feel",
        props=["broccoli", "bell peppers", "carrots", "lettuce", "colander"],
        mood="natural, organic, garden-fresh"
    ),

    # --- Japanese Style ---
    "ซูชิ": VisualConcept(
        subject="Elegant sushi platter with precision cuts",
        action="chopsticks lift a single piece of nigiri, dipped in soy sauce",
        setting="Japanese restaurant with wooden counter",
        props=["bamboo mat", "soy sauce", "wasabi", "pickled ginger"],
        mood="refined, zen, artisanal"
    ),
    "สไตล์ญี่ปุ่น": VisualConcept(
        subject="Japanese minimalist meal presentation",
        action="steam rises from miso soup, chopsticks rest on ceramic holder",
        setting="Traditional Japanese dining with low wooden table",
        props=["bento box", "ceramic bowls", "chopsticks", "matcha tea"],
        mood="zen, minimal, elegant"
    ),
    "ราเมง": VisualConcept(
        subject="Steaming bowl of ramen with rich broth",
        action="noodles lifted by chopsticks, broth glistening",
        setting="Cozy Japanese noodle shop with warm lighting",
        props=["ramen bowl", "soft-boiled egg", "chashu pork", "nori"],
        mood="warm, comforting, aromatic"
    ),

    # --- Thai Food ---
    "ต้มยำ": VisualConcept(
        subject="Aromatic tom yum soup in traditional bowl",
        action="ladle pours broth revealing shrimp and herbs",
        setting="Thai kitchen with mortar and pestle nearby",
        props=["galangal", "lemongrass", "lime leaves", "shrimp", "chili"],
        mood="spicy, aromatic, traditional"
    ),
    "ส้มตำ": VisualConcept(
        subject="Freshly pounded papaya salad",
        action="mortar and pestle pounding, vibrant ingredients mixing",
        setting="Thai street food stall or home kitchen",
        props=["green papaya", "dried shrimp", "peanuts", "chili", "lime"],
        mood="lively, tangy, authentic"
    ),
    "ผัดไทย": VisualConcept(
        subject="Sizzling pad Thai in hot wok",
        action="wok tossing noodles with flames, ingredients flying",
        setting="Open kitchen with high heat cooking",
        props=["flat rice noodles", "bean sprouts", "peanuts", "lime wedge"],
        mood="energetic, sizzling, dynamic"
    ),
    "แกงเขียวหวาน": VisualConcept(
        subject="Rich green curry in coconut cream",
        action="curry simmering gently, coconut cream swirling on surface",
        setting="Traditional Thai kitchen with clay pot",
        props=["Thai basil", "eggplant", "bamboo shoots", "jasmine rice"],
        mood="rich, aromatic, traditional"
    ),

    # --- Cooking Actions ---
    "ทำอาหาร": VisualConcept(
        subject="Hands preparing meal with fresh ingredients",
        action="chopping vegetables on wooden board, organized mise en place",
        setting="Well-equipped modern kitchen",
        props=["knife", "cutting board", "fresh ingredients", "bowls"],
        mood="productive, creative, focused"
    ),
    "ปรุงอาหาร": VisualConcept(
        subject="Chef seasoning dish with expertise",
        action="spices sprinkled from above, pan sizzling with aromatics",
        setting="Professional kitchen with copper pans",
        props=["spice jars", "salt", "pepper", "herbs", "tasting spoon"],
        mood="skilled, aromatic, artisanal"
    ),

    # --- Drinks ---
    "กาแฟ": VisualConcept(
        subject="Artisan coffee in ceramic cup",
        action="espresso pouring in slow motion, steam curling upward",
        setting="Cozy cafe with warm ambient lighting",
        props=["ceramic cup", "latte art", "coffee beans", "saucer"],
        mood="warm, aromatic, inviting"
    ),
    "ชา": VisualConcept(
        subject="Tea ceremony with delicate cups",
        action="hot water pouring over tea leaves, color infusing",
        setting="Peaceful tea room with natural light",
        props=["teapot", "tea cups", "tea leaves", "wooden tray"],
        mood="serene, contemplative, refined"
    ),
    "น้ำผลไม้": VisualConcept(
        subject="Freshly squeezed fruit juice in glass",
        action="fruits being juiced, colorful liquid flowing",
        setting="Bright kitchen with morning sunlight",
        props=["fresh oranges", "juicer", "tall glass", "ice cubes"],
        mood="refreshing, healthy, bright"
    ),
    "น้ำ": VisualConcept(
        subject="Crystal clear water in elegant glass",
        action="water pouring into glass, light refracting through droplets",
        setting="Clean minimal surface with soft backlighting",
        props=["glass", "water pitcher", "lemon slice", "mint leaf"],
        mood="pure, refreshing, clean"
    ),
}


# ============================================================
# HEALTH & FITNESS (15+ items)
# ============================================================

HEALTH_VISUALS: dict[str, VisualConcept] = {
    "ออกกำลังกาย": VisualConcept(
        subject="Athletic movement in gym setting",
        action="dynamic exercise movement with controlled form",
        setting="Modern gym with natural light streaming in",
        props=["dumbbells", "yoga mat", "water bottle", "towel"],
        mood="energetic, empowering, motivated"
    ),
    "โยคะ": VisualConcept(
        subject="Yoga pose in serene setting",
        action="flowing movement between poses, balanced and graceful",
        setting="Peaceful studio with floor-to-ceiling windows, morning light",
        props=["yoga mat", "blocks", "plants", "incense"],
        mood="calm, centered, mindful"
    ),
    "วิ่ง": VisualConcept(
        subject="Runner on scenic trail",
        action="steady rhythmic running, feet hitting ground",
        setting="Morning trail with golden hour light filtering through trees",
        props=["running shoes", "fitness tracker", "water belt"],
        mood="free, determined, adventurous"
    ),
    "ยืดเหยียด": VisualConcept(
        subject="Full body stretching routine",
        action="slow deliberate stretches, muscles lengthening",
        setting="Clean home workout space with natural light",
        props=["yoga mat", "foam roller", "resistance band"],
        mood="relaxed, flexible, refreshed"
    ),
    "หายใจ": VisualConcept(
        subject="Meditation breathing exercise",
        action="deep inhale and exhale, chest rising and falling slowly",
        setting="Quiet room with soft natural light, plants around",
        props=["meditation cushion", "candle", "essential oil diffuser"],
        mood="peaceful, centered, mindful"
    ),
    "สุขภาพ": VisualConcept(
        subject="Healthy lifestyle montage elements",
        action="balanced activities flowing naturally together",
        setting="Bright, airy living space with natural elements",
        props=["fresh food", "water glass", "exercise equipment", "plants"],
        mood="vibrant, balanced, wholesome"
    ),
    "ลดน้ำหนัก": VisualConcept(
        subject="Weight loss journey progress visualization",
        action="measuring tape wrapping, scale reading, clothes fitting",
        setting="Bright bathroom or bedroom with mirror",
        props=["measuring tape", "scale", "healthy meal", "running shoes"],
        mood="hopeful, determined, progressive"
    ),
    "นอนหลับ": VisualConcept(
        subject="Peaceful sleeping environment",
        action="soft light fading, gentle movement of curtains",
        setting="Cozy bedroom with dim warm lighting",
        props=["comfortable bed", "soft pillows", "moon through window", "clock showing night"],
        mood="peaceful, restful, dreamy"
    ),
    "พักผ่อน": VisualConcept(
        subject="Relaxation scene with calming elements",
        action="slow gentle movements, turning book pages, sipping tea",
        setting="Comfortable living room or garden with soft afternoon light",
        props=["book", "tea cup", "soft blanket", "cushions"],
        mood="relaxed, content, rejuvenating"
    ),
    "วิตามิน": VisualConcept(
        subject="Vitamin supplements and natural sources",
        action="capsules arranged next to fresh fruits and vegetables",
        setting="Clean white countertop with organized supplements",
        props=["vitamin bottles", "citrus fruits", "supplement organizer"],
        mood="clinical-clean, healthy, organized"
    ),
    "ชั่งน้ำหนัก": VisualConcept(
        subject="Bathroom scale with feet stepping on",
        action="digital numbers changing, subtle reaction",
        setting="Clean modern bathroom floor",
        props=["digital scale", "feet", "bathroom tiles"],
        mood="anticipation, self-awareness, progress"
    ),
}


# ============================================================
# LIFESTYLE & DAILY ROUTINE (15+ items)
# ============================================================

LIFESTYLE_VISUALS: dict[str, VisualConcept] = {
    "ตื่นเช้า": VisualConcept(
        subject="Morning wake-up routine",
        action="curtains opening, sunlight flooding in, stretching in bed",
        setting="Bright bedroom with morning golden light",
        props=["alarm clock", "bed", "curtains", "morning sunlight"],
        mood="fresh start, optimistic, energized"
    ),
    "ทำงาน": VisualConcept(
        subject="Productive work environment",
        action="typing on laptop, writing notes, organizing tasks",
        setting="Modern desk setup with clean organisation",
        props=["laptop", "notebook", "coffee cup", "desk plant"],
        mood="focused, productive, professional"
    ),
    "เรียน": VisualConcept(
        subject="Study session with learning materials",
        action="highlighting text, taking notes, turning pages",
        setting="Library or study desk with warm lamp light",
        props=["books", "notebook", "highlighter", "desk lamp"],
        mood="studious, focused, intellectual"
    ),
    "ครอบครัว": VisualConcept(
        subject="Family moment together",
        action="sharing meal, playing, laughing together",
        setting="Warm home dining room or living room",
        props=["dining table", "family photos", "shared meal"],
        mood="warm, loving, connected"
    ),
    "ช้อปปิ้ง": VisualConcept(
        subject="Shopping experience at market",
        action="selecting fresh produce, comparing items, putting in basket",
        setting="Farmers market or organic grocery store",
        props=["woven basket", "fresh produce", "price tags", "eco bag"],
        mood="lively, abundant, selective"
    ),
    "ธรรมชาติ": VisualConcept(
        subject="Natural landscape",
        action="wind moving through trees, water flowing, clouds drifting",
        setting="Lush green forest, river, or mountain landscape",
        props=["trees", "flowing water", "rocks", "wildflowers"],
        mood="serene, majestic, grounding"
    ),
    "สวน": VisualConcept(
        subject="Garden with growing plants",
        action="planting seeds, watering, sunlight on leaves",
        setting="Home garden or community garden",
        props=["potted plants", "watering can", "garden tools", "soil"],
        mood="nurturing, growth, peaceful"
    ),
    "ตลาด": VisualConcept(
        subject="Bustling Thai market scene",
        action="vendors arranging produce, steam from food stalls",
        setting="Colorful Thai fresh market with overhead awnings",
        props=["fresh produce", "market baskets", "price signs", "food stalls"],
        mood="vibrant, bustling, authentic"
    ),
    "บ้าน": VisualConcept(
        subject="Cozy home interior",
        action="soft light changing through windows, gentle daily activities",
        setting="Well-decorated Thai home with warm tones",
        props=["living room furniture", "family photos", "indoor plants"],
        mood="comfortable, homey, welcoming"
    ),
}


# ============================================================
# EMOTIONS & ABSTRACT CONCEPTS (10+ items)
# ============================================================

CONCEPT_VISUALS: dict[str, VisualConcept] = {
    "สมดุล": VisualConcept(
        subject="Balanced composition showing harmony",
        action="elements coming into perfect alignment",
        setting="Zen-inspired space with symmetrical design",
        props=["balanced stones", "yin-yang arrangement", "equal portions"],
        mood="harmonious, centered, peaceful"
    ),
    "พลังงาน": VisualConcept(
        subject="Dynamic energy visualization",
        action="burst of movement, light expanding outward",
        setting="Open space with dramatic lighting",
        props=["sunburst", "moving water", "wind-blown elements"],
        mood="powerful, dynamic, vibrant"
    ),
    "ความสุข": VisualConcept(
        subject="Joyful moment captured in warm light",
        action="laughter, celebration, arms raised in joy",
        setting="Sunlit outdoor space or cozy indoor gathering",
        props=["flowers", "warm light", "colorful elements"],
        mood="joyful, radiant, warm"
    ),
    "ความมั่นใจ": VisualConcept(
        subject="Confident stance or achievement moment",
        action="standing tall, looking forward, purposeful movement",
        setting="Expansive view from high point or stage",
        props=["podium", "spotlight", "open path ahead"],
        mood="empowered, strong, determined"
    ),
    "เปลี่ยนแปลง": VisualConcept(
        subject="Transformation visual metaphor",
        action="before-and-after transition, butterfly emerging, flower blooming",
        setting="Scene transitioning from dark to bright",
        props=["chrysalis", "sunrise", "new growth", "mirror"],
        mood="transformative, hopeful, evolving"
    ),
    "เป้าหมาย": VisualConcept(
        subject="Goal achievement visualization",
        action="reaching finish line, climbing to summit, hitting target",
        setting="Mountain peak or running track with finish line",
        props=["flag at summit", "finish ribbon", "calendar with checkmarks"],
        mood="aspirational, determined, triumphant"
    ),
    "เริ่มต้น": VisualConcept(
        subject="Fresh beginning scene",
        action="door opening to bright light, first step on new path",
        setting="Dawn landscape or clean empty room ready for new things",
        props=["sunrise", "open door", "blank page", "new seedling"],
        mood="hopeful, clean, exciting"
    ),
    "ความรัก": VisualConcept(
        subject="Love and care visual",
        action="gentle touch, holding hands, nurturing gesture",
        setting="Warm intimate space with soft golden light",
        props=["flowers", "warm embrace", "heart shapes in nature"],
        mood="tender, warm, intimate"
    ),
    "ปัญหา": VisualConcept(
        subject="Challenge or obstacle visualization",
        action="dark clouds gathering, maze from above, tangled threads",
        setting="Dramatic moody environment with tension",
        props=["storm clouds", "twisted path", "puzzle pieces"],
        mood="tense, challenging, dramatic"
    ),
    "แก้ปัญหา": VisualConcept(
        subject="Problem solving visualization",
        action="light breaking through darkness, puzzle coming together, knot untying",
        setting="Scene transitioning from chaos to order",
        props=["light beam", "completed puzzle", "organized desk"],
        mood="insightful, relieving, satisfying"
    ),
}


# ============================================================
# COMBINED LOOKUP (all categories)
# ============================================================

ALL_VISUALS: dict[str, VisualConcept] = {
    **FOOD_VISUALS,
    **HEALTH_VISUALS,
    **LIFESTYLE_VISUALS,
    **CONCEPT_VISUALS,
}


def extract_visual_concepts(narration: str) -> list[tuple[str, VisualConcept]]:
    """
    Extract all matching visual concepts from Thai narration text.
    Returns list of (keyword, VisualConcept) tuples, ordered by position in text.
    
    Args:
        narration: Thai narration text to analyze
        
    Returns:
        List of (keyword, visual_concept) tuples found in narration
    """
    narration_lower = narration.lower()
    matches: list[tuple[int, str, VisualConcept]] = []
    
    for keyword, concept in ALL_VISUALS.items():
        pos = narration_lower.find(keyword)
        if pos >= 0:
            matches.append((pos, keyword, concept))
    
    # Sort by position in text (first mentioned = most relevant)
    matches.sort(key=lambda x: x[0])
    
    return [(kw, concept) for _, kw, concept in matches]


def build_visual_anchors(narration: str, video_type: str = "with_person") -> str:
    """
    Build visual anchor text from Thai narration for prompt injection.
    
    Args:
        narration: Thai narration text
        video_type: "with_person", "no_person", or "mixed"
        
    Returns:
        Formatted visual anchors string for AI prompt injection
    """
    matches = extract_visual_concepts(narration)
    
    if not matches:
        return ""
    
    # Take top 3 most relevant matches
    top_matches = matches[:3]
    
    lines = ["**🔑 VISUAL ANCHORS (extracted from narration):**"]
    
    for keyword, concept in top_matches:
        lines.append(f"• Thai keyword: \"{keyword}\"")
        
        if video_type == "no_person":
            lines.append(f"  → Subject: {concept.subject}")
            lines.append(f"  → Action: {concept.action}")
        else:
            lines.append(f"  → Visual: {concept.subject}, {concept.action}")
        
        lines.append(f"  → Setting: {concept.setting}")
        lines.append(f"  → Props: {', '.join(concept.props[:3])}")
        lines.append(f"  → Mood: {concept.mood}")
    
    lines.append("")
    lines.append("→ USE THESE SPECIFIC VISUAL DETAILS in your prompt. Do NOT use generic descriptions.")
    
    return "\n".join(lines)


def get_fallback_visuals(narration: str, video_type: str = "with_person") -> dict[str, str]:
    """
    Get fallback visual components from narration for rule-based prompt generation.
    
    Args:
        narration: Thai narration text
        video_type: "with_person", "no_person", or "mixed"
        
    Returns:
        Dict with keys: subject, action, setting, props, mood
    """
    matches = extract_visual_concepts(narration)
    
    if not matches:
        return {}
    
    # Use the first (most relevant) match
    _, concept = matches[0]
    
    result = {
        "subject": concept.subject,
        "action": concept.action,
        "setting": concept.setting,
        "props": ", ".join(concept.props),
        "mood": concept.mood,
    }
    
    # For no_person, ensure subject doesn't include people
    if video_type == "no_person":
        person_words = ["person", "chef", "runner", "family", "athlete"]
        for word in person_words:
            if word.lower() in result["subject"].lower():
                result["subject"] = result["subject"] + " (focus on objects, no people visible)"
    
    return result
