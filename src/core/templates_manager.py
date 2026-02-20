"""
Template Library Manager
Save/load project style configurations as reusable presets.
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional
import uuid

logger = logging.getLogger("vdo_content.templates_manager")

TEMPLATES_DIR = Path("data/templates")
TEMPLATES_DIR.mkdir(parents=True, exist_ok=True)


class StyleTemplate:
    """Reusable style configuration that can be applied across projects."""

    def __init__(
        self,
        name: str,
        description: str = "",
        video_type: str = "with_person",
        character_reference: str = "",
        visual_theme: str = "",
        direction_style: str = "",
        prompt_style_config: Optional[dict] = None,
        aspect_ratio: str = "16:9",
        hook_type: str = "auto",
        closing_type: str = "auto",
        target_platforms: Optional[list] = None,
        content_category: str = "",
        tone: str = "",
        template_id: Optional[str] = None,
        created_at: Optional[str] = None,
        is_builtin: bool = False,
    ):
        self.template_id = template_id or str(uuid.uuid4())
        self.name = name
        self.description = description
        self.video_type = video_type
        self.character_reference = character_reference
        self.visual_theme = visual_theme
        self.direction_style = direction_style
        self.prompt_style_config = prompt_style_config or {}
        self.aspect_ratio = aspect_ratio
        self.hook_type = hook_type
        self.closing_type = closing_type
        self.target_platforms = target_platforms or []
        self.content_category = content_category
        self.tone = tone
        self.created_at = created_at or datetime.now().isoformat()
        self.is_builtin = is_builtin

    def to_dict(self) -> dict:
        return {
            "template_id": self.template_id,
            "name": self.name,
            "description": self.description,
            "video_type": self.video_type,
            "character_reference": self.character_reference,
            "visual_theme": self.visual_theme,
            "direction_style": self.direction_style,
            "prompt_style_config": self.prompt_style_config,
            "aspect_ratio": self.aspect_ratio,
            "hook_type": self.hook_type,
            "closing_type": self.closing_type,
            "target_platforms": self.target_platforms,
            "content_category": self.content_category,
            "tone": self.tone,
            "created_at": self.created_at,
            "is_builtin": self.is_builtin,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "StyleTemplate":
        known = set(cls.__init__.__code__.co_varnames)
        return cls(**{k: v for k, v in data.items() if k in known})


# Built-in style presets
BUILTIN_TEMPLATES = [
    StyleTemplate(
        template_id="builtin-thai-lifestyle",
        name="Thai Lifestyle",
        description="Lifestyle / food / travel review style with warm golden tones",
        video_type="with_person",
        visual_theme="Warm and cozy atmosphere. Soft golden lighting, warm color temperature, comfortable indoor settings.",
        hook_type="question",
        closing_type="cta",
        target_platforms=["tiktok", "instagram_reels"],
        content_category="lifestyle",
        tone="friendly, approachable, casual",
        is_builtin=True,
    ),
    StyleTemplate(
        template_id="builtin-product-review",
        name="Product Review",
        description="Clean product hero shots, minimal white/neutral backgrounds",
        video_type="mixed",
        visual_theme="Minimal and clean aesthetic. White or neutral backgrounds, simple compositions, lots of negative space.",
        hook_type="hook",
        closing_type="cta",
        target_platforms=["youtube", "tiktok"],
        content_category="review",
        tone="informative, honest, confident",
        is_builtin=True,
    ),
    StyleTemplate(
        template_id="builtin-educational",
        name="Educational Short",
        description="Educational / tutorial / knowledge-sharing content",
        video_type="with_person",
        visual_theme="Bright and energetic. Vivid saturated colors, dynamic angles, high-key lighting, bold compositions.",
        hook_type="dramatic",
        closing_type="summary",
        target_platforms=["youtube", "youtube_shorts"],
        content_category="educational",
        tone="clear, engaging, authoritative",
        is_builtin=True,
    ),
    StyleTemplate(
        template_id="builtin-luxury",
        name="Luxury Premium",
        description="High-end luxury product or service, premium look",
        video_type="no_person",
        visual_theme="Luxury premium look. Gold accents, marble textures, rich deep colors, elegant lighting.",
        hook_type="visual",
        closing_type="brand",
        target_platforms=["instagram_reels", "youtube"],
        content_category="luxury",
        tone="sophisticated, exclusive, aspirational",
        is_builtin=True,
    ),
    StyleTemplate(
        template_id="builtin-travel",
        name="Travel Vlog",
        description="Travel, nature, adventure content",
        video_type="mixed",
        visual_theme="Tropical aesthetic. Vibrant tropical colors, Thai cultural elements, lush vegetation, warm exotic atmosphere.",
        hook_type="journey",
        closing_type="inspiration",
        target_platforms=["youtube", "instagram_reels"],
        content_category="travel",
        tone="adventurous, inspiring, warm",
        is_builtin=True,
    ),
]


def _template_path(template_id: str) -> Path:
    return TEMPLATES_DIR / f"{template_id}.json"


def save_template(template: StyleTemplate) -> StyleTemplate:
    """Save a template to disk."""
    path = _template_path(template.template_id)
    path.write_text(json.dumps(template.to_dict(), ensure_ascii=False, indent=2), encoding="utf-8")
    logger.info(f"Saved template '{template.name}' ({template.template_id})")
    return template


def load_template(template_id: str) -> Optional[StyleTemplate]:
    """Load template by ID (checks built-ins first)."""
    for t in BUILTIN_TEMPLATES:
        if t.template_id == template_id:
            return t
    path = _template_path(template_id)
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return StyleTemplate.from_dict(data)
    except Exception as e:
        logger.error(f"Failed to load template {template_id}: {e}")
        return None


def list_templates() -> list:
    """List all available templates (built-in + user-created)."""
    templates = list(BUILTIN_TEMPLATES)
    for path in sorted(TEMPLATES_DIR.glob("*.json")):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            t = StyleTemplate.from_dict(data)
            if not t.is_builtin:
                templates.append(t)
        except Exception as e:
            logger.warning(f"Failed to read template {path}: {e}")
    return templates


def delete_template(template_id: str) -> bool:
    """Delete a user template. Built-in templates cannot be deleted."""
    for t in BUILTIN_TEMPLATES:
        if t.template_id == template_id:
            return False  # cannot delete built-ins
    path = _template_path(template_id)
    if path.exists():
        path.unlink()
        return True
    return False


def template_from_project(project, name: str, description: str = "") -> StyleTemplate:
    """Create a new template from the current project settings."""
    return StyleTemplate(
        name=name,
        description=description,
        video_type=getattr(project, "video_type", "with_person"),
        character_reference=getattr(project, "character_reference", ""),
        visual_theme=getattr(project, "visual_theme", ""),
        direction_style=getattr(project, "default_style", ""),
        prompt_style_config=getattr(project, "prompt_style_config", {}),
        aspect_ratio=getattr(project, "aspect_ratio", "16:9"),
        hook_type=getattr(project, "hook_type", "auto"),
        closing_type=getattr(project, "closing_type", "auto"),
        target_platforms=getattr(project, "platforms", []),
        content_category=getattr(project, "content_category", ""),
    )


def apply_template_to_project(project, template: StyleTemplate):
    """Apply template settings to a project object in-place."""
    if template.video_type:
        project.video_type = template.video_type
    if template.character_reference:
        project.character_reference = template.character_reference
    if template.visual_theme:
        project.visual_theme = template.visual_theme
    if template.direction_style:
        project.default_style = template.direction_style
    if template.prompt_style_config:
        project.prompt_style_config = template.prompt_style_config
    if template.aspect_ratio:
        project.aspect_ratio = template.aspect_ratio
    if template.hook_type:
        project.hook_type = template.hook_type
    if template.closing_type:
        project.closing_type = template.closing_type
    if template.target_platforms:
        project.platforms = template.target_platforms
    if template.content_category:
        project.content_category = template.content_category
    logger.info(f"Applied template '{template.name}' to project '{project.title}'")
    return project
