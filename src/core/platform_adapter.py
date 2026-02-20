"""
Platform Adapter -- Multi-platform Veo Prompt Variants
Generates platform-specific prompt variants from a base Veo prompt.
"""

import logging
from typing import Optional

logger = logging.getLogger("vdo_content.platform_adapter")

# --- Platform configurations ---

PLATFORM_CONFIGS = {
    "tiktok": {
        "name": "TikTok",
        "icon": "🎵",
        "aspect_ratio": "9:16",
        "max_duration_sec": 8,
        "composition_note": (
            "VERTICAL VIDEO 9:16. Subject must be centered vertically in the frame. "
            "Close-up or medium shot with subject filling majority of the vertical frame."
        ),
        "hook_note": (
            "Hook must be visually captivating within the FIRST 1.5 SECONDS "
            "with a bold gesture, expression, or dynamic movement."
        ),
        "pacing": "fast, dynamic, energetic",
        "extra_tags": "vertical video, mobile-optimized, social media, fast cut",
    },
    "instagram_reels": {
        "name": "Instagram Reels",
        "icon": "📸",
        "aspect_ratio": "9:16",
        "max_duration_sec": 8,
        "composition_note": (
            "VERTICAL VIDEO 9:16. Aesthetic, polished composition. "
            "Subject centered, visually pleasing with clean backgrounds."
        ),
        "hook_note": (
            "Opening must be instantly visually appealing -- "
            "bright, colorful, or elegant to stop scroll."
        ),
        "pacing": "smooth, aesthetic, polished",
        "extra_tags": "vertical video, Instagram Reels, aesthetic, lifestyle",
    },
    "youtube": {
        "name": "YouTube",
        "icon": "▶️",
        "aspect_ratio": "16:9",
        "max_duration_sec": 8,
        "composition_note": (
            "HORIZONTAL VIDEO 16:9. Standard cinematic widescreen composition. "
            "Rule of thirds framing, professional broadcast look."
        ),
        "hook_note": (
            "Strong visual opening that establishes the setting and subject clearly."
        ),
        "pacing": "steady, cinematic, informative",
        "extra_tags": "widescreen, cinematic, YouTube, professional",
    },
    "youtube_shorts": {
        "name": "YouTube Shorts",
        "icon": "🔴",
        "aspect_ratio": "9:16",
        "max_duration_sec": 8,
        "composition_note": (
            "VERTICAL VIDEO 9:16 for YouTube Shorts. "
            "Subject in center frame, clean and bold composition."
        ),
        "hook_note": (
            "First second must show the main subject clearly. "
            "Bold and visually direct opener."
        ),
        "pacing": "concise, impactful",
        "extra_tags": "vertical video, YouTube Shorts, mobile-first",
    },
    "facebook_reels": {
        "name": "Facebook Reels",
        "icon": "📘",
        "aspect_ratio": "9:16",
        "max_duration_sec": 8,
        "composition_note": (
            "VERTICAL VIDEO 9:16. Broad appeal composition, "
            "clear subject with readable visuals."
        ),
        "hook_note": "Engaging opener within first 2 seconds.",
        "pacing": "engaging, broad appeal",
        "extra_tags": "vertical video, Facebook Reels, social",
    },
}

ALL_PLATFORM_KEYS = list(PLATFORM_CONFIGS.keys())
DEFAULT_PLATFORMS = ["tiktok", "youtube"]


def adapt_prompt_for_platform(
    base_prompt: str,
    platform: str,
    video_type: str = "with_person",
) -> str:
    """
    Adapt a base Veo prompt for a specific platform.

    Injects platform-specific composition rules, aspect ratio, and pacing
    into the prompt without changing the core subject/action/setting.

    Args:
        base_prompt: Original Veo prompt (base, usually 16:9 or universal)
        platform: Platform key from PLATFORM_CONFIGS
        video_type: "with_person" | "no_person" | "mixed"

    Returns:
        Platform-adapted prompt string
    """
    config = PLATFORM_CONFIGS.get(platform)
    if not config:
        logger.warning(f"Unknown platform '{platform}' -- returning base prompt unchanged")
        return base_prompt

    # Build adaptation prefix
    lines = [
        f"[{config['aspect_ratio']} {config['name']} VERSION]",
        config["composition_note"],
    ]

    if config.get("hook_note"):
        lines.append(config["hook_note"])

    prefix = " ".join(lines)

    # Inject platform tags at the end
    tags = config.get("extra_tags", "")
    tag_suffix = f", {tags}" if tags else ""

    # Clean up base prompt -- remove any existing aspect ratio tags
    import re
    cleaned_base = re.sub(
        r"\[?(16:9|9:16|1:1|4:3)[^\]]*\]?",
        "",
        base_prompt,
        flags=re.IGNORECASE,
    ).strip()

    adapted = f"{prefix} {cleaned_base}{tag_suffix}"

    logger.info(f"Adapted prompt for {config['name']} ({config['aspect_ratio']})")
    return adapted


def generate_platform_variants(
    base_prompt: str,
    platforms: Optional[list] = None,
    video_type: str = "with_person",
) -> dict:
    """
    Generate prompt variants for multiple platforms.

    Args:
        base_prompt: Original Veo prompt
        platforms: List of platform keys (default: all platforms)
        video_type: Video type

    Returns:
        dict mapping platform key -> adapted prompt
    """
    if platforms is None:
        platforms = ALL_PLATFORM_KEYS

    variants = {}
    for platform in platforms:
        if platform in PLATFORM_CONFIGS:
            variants[platform] = adapt_prompt_for_platform(
                base_prompt, platform, video_type
            )
        else:
            logger.warning(f"Skipping unknown platform: {platform}")

    return variants


def get_platform_info(platform: str) -> Optional[dict]:
    """Get display information for a platform."""
    return PLATFORM_CONFIGS.get(platform)


def format_platform_label(platform: str) -> str:
    """Return user-facing label: icon + name + aspect ratio."""
    cfg = PLATFORM_CONFIGS.get(platform, {})
    return f"{cfg.get('icon', '')} {cfg.get('name', platform)} ({cfg.get('aspect_ratio', '')})"
