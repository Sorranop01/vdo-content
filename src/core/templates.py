"""
Template Manager
VDO Content V2 - Week 4

Manage project templates for quick content creation.
"""

import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional, Literal
from dataclasses import dataclass, field, asdict

from .models import Project, Scene


# Template categories
TemplateCategory = Literal["news", "tutorial", "product", "story", "knowledge", "entertainment", "custom"]


@dataclass
class Template:
    """Project template definition"""
    id: str
    name: str
    description: str
    category: TemplateCategory
    
    # Content structure
    default_style: str = "documentary"
    target_duration: int = 60
    scene_count: int = 5
    
    # Default prompts
    system_prompt: str = ""
    scene_templates: list[dict] = field(default_factory=list)
    
    # Metadata
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    usage_count: int = 0
    is_builtin: bool = False
    
    # Visual settings
    visual_theme: str = ""
    aspect_ratio: str = "16:9"


# Built-in templates
BUILTIN_TEMPLATES = [
    Template(
        id="news-short",
        name="ข่าวสั้น (News Short)",  
        description="ข่าวสั้น 30-60 วินาที สไตล์รายงาน",
        category="news",
        default_style="documentary",
        target_duration=45,
        scene_count=4,
        system_prompt="สร้างบทข่าวสั้นกระชับ มีหัวข้อ รายละเอียด และสรุป",
        scene_templates=[
            {"order": 1, "type": "headline", "duration": 8, "prompt_hint": "News headline graphic, bold text animation"},
            {"order": 2, "type": "detail_1", "duration": 12, "prompt_hint": "Visual representation of main event"},
            {"order": 3, "type": "detail_2", "duration": 15, "prompt_hint": "Supporting footage or interview setup"},
            {"order": 4, "type": "conclusion", "duration": 10, "prompt_hint": "Summary graphic or call-to-action"},
        ],
        is_builtin=True
    ),
    Template(
        id="tutorial-howto",
        name="สอนวิธีทำ (How-To)",
        description="สอนขั้นตอน step-by-step 2-3 นาที",
        category="tutorial",
        default_style="tutorial",
        target_duration=120,
        scene_count=6,
        system_prompt="สร้างบทสอนแบบ step-by-step อธิบายชัดเจน ตามลำดับ",
        scene_templates=[
            {"order": 1, "type": "intro", "duration": 10, "prompt_hint": "Title card with topic, friendly intro scene"},
            {"order": 2, "type": "overview", "duration": 15, "prompt_hint": "Overview of materials or prerequisites"},
            {"order": 3, "type": "step_1", "duration": 20, "prompt_hint": "First step demonstration"},
            {"order": 4, "type": "step_2", "duration": 25, "prompt_hint": "Second step demonstration"},
            {"order": 5, "type": "step_3", "duration": 25, "prompt_hint": "Third step demonstration"},
            {"order": 6, "type": "result", "duration": 15, "prompt_hint": "Final result showcase"},
        ],
        is_builtin=True
    ),
    Template(
        id="product-ad",
        name="โฆษณาสินค้า (Product)",
        description="โฆษณาสินค้า 30 วินาที สไตล์โน้มน้าว",
        category="product",
        default_style="storytelling",
        target_duration=30,
        scene_count=4,
        system_prompt="สร้างบทโฆษณาที่ดึงดูด เน้น Pain Point + Solution + CTA",
        scene_templates=[
            {"order": 1, "type": "hook", "duration": 5, "prompt_hint": "Attention-grabbing opening, problem statement"},
            {"order": 2, "type": "problem", "duration": 8, "prompt_hint": "Customer pain point visualization"},
            {"order": 3, "type": "solution", "duration": 10, "prompt_hint": "Product reveal, solving the problem"},
            {"order": 4, "type": "cta", "duration": 7, "prompt_hint": "Call-to-action, product showcase"},
        ],
        is_builtin=True
    ),
    Template(
        id="story-narrative",
        name="เล่าเรื่อง (Story)",
        description="เล่าเรื่องแบบมี plot 2-3 นาที",
        category="story",
        default_style="storytelling",
        target_duration=150,
        scene_count=7,
        system_prompt="สร้างบทเล่าเรื่องที่มี plot ชัดเจน มีตัวละคร มีความขัดแย้ง และ resolution",
        scene_templates=[
            {"order": 1, "type": "setup", "duration": 15, "prompt_hint": "Story world establishment"},
            {"order": 2, "type": "character", "duration": 20, "prompt_hint": "Character introduction"},
            {"order": 3, "type": "conflict", "duration": 25, "prompt_hint": "Conflict or challenge appears"},
            {"order": 4, "type": "struggle", "duration": 30, "prompt_hint": "Character facing difficulties"},
            {"order": 5, "type": "climax", "duration": 25, "prompt_hint": "Peak moment, turning point"},
            {"order": 6, "type": "resolution", "duration": 25, "prompt_hint": "Problem solved, outcome shown"},
            {"order": 7, "type": "conclusion", "duration": 10, "prompt_hint": "Final message or takeaway"},
        ],
        is_builtin=True
    ),
    Template(
        id="knowledge-facts",
        name="ให้ความรู้ (Facts)",
        description="Fact-based content 1-2 นาที",
        category="knowledge",
        default_style="documentary",
        target_duration=90,
        scene_count=5,
        system_prompt="สร้างบทให้ความรู้ที่น่าเชื่อถือ มีข้อมูลอ้างอิง",
        scene_templates=[
            {"order": 1, "type": "hook", "duration": 10, "prompt_hint": "Interesting fact or question"},
            {"order": 2, "type": "context", "duration": 15, "prompt_hint": "Background information"},
            {"order": 3, "type": "fact_1", "duration": 20, "prompt_hint": "Main fact visualization"},
            {"order": 4, "type": "fact_2", "duration": 25, "prompt_hint": "Supporting evidence"},
            {"order": 5, "type": "summary", "duration": 20, "prompt_hint": "Key takeaways"},
        ],
        is_builtin=True
    ),
]


class TemplateManager:
    """
    Manage project templates - both built-in and custom.
    
    Usage:
        manager = TemplateManager()
        templates = manager.list_templates()
        project = manager.apply_template("news-short", "หัวข้อข่าว")
    """
    
    def __init__(self, templates_dir: Optional[Path] = None):
        """
        Initialize template manager
        
        Args:
            templates_dir: Directory for custom templates
        """
        self.templates_dir = templates_dir or Path("templates")
        self.templates_dir.mkdir(parents=True, exist_ok=True)
        
        # Load custom templates
        self._custom_templates: dict[str, Template] = {}
        self._load_custom_templates()
    
    def _load_custom_templates(self):
        """Load custom templates from disk"""
        for file in self.templates_dir.glob("*.json"):
            try:
                data = json.loads(file.read_text(encoding="utf-8"))
                template = Template(**data)
                self._custom_templates[template.id] = template
            except Exception as e:
                import logging
                logging.getLogger("vdo_content.templates").warning(f"Failed to load template {file}: {e}")
                continue
    
    def list_templates(self, category: Optional[TemplateCategory] = None) -> list[Template]:
        """
        List all available templates
        
        Args:
            category: Filter by category
            
        Returns:
            List of templates
        """
        all_templates = BUILTIN_TEMPLATES + list(self._custom_templates.values())
        
        if category:
            return [t for t in all_templates if t.category == category]
        return all_templates
    
    def get_template(self, template_id: str) -> Optional[Template]:
        """Get template by ID"""
        # Check built-in
        for t in BUILTIN_TEMPLATES:
            if t.id == template_id:
                return t
        
        # Check custom
        return self._custom_templates.get(template_id)
    
    def apply_template(
        self, 
        template_id: str, 
        topic: str,
        title: Optional[str] = None
    ) -> Project:
        """
        Create a new project from template
        
        Args:
            template_id: Template ID
            topic: Content topic
            title: Custom title (default: topic)
            
        Returns:
            New Project instance
        """
        template = self.get_template(template_id)
        if not template:
            raise ValueError(f"Template not found: {template_id}")
        
        # Create scenes from template
        scenes = []
        for scene_template in template.scene_templates:
            scene = Scene(
                order=scene_template["order"],
                narration_text="",
                veo_prompt=scene_template.get("prompt_hint", ""),
                start_time=0,
                end_time=scene_template.get("duration", 8),
                visual_style=template.default_style
            )
            scenes.append(scene)
        
        # Create project
        project = Project(
            title=title or topic,
            topic=topic,
            description=template.description,
            scenes=scenes,
            target_duration=template.target_duration,
            default_style=template.default_style,
            visual_theme=template.visual_theme,
            aspect_ratio=template.aspect_ratio
        )
        
        # Increment usage count
        template.usage_count += 1
        
        return project
    
    def save_as_template(
        self,
        project: Project,
        name: str,
        description: str,
        category: TemplateCategory = "custom"
    ) -> Template:
        """
        Save a project as a reusable template
        
        Args:
            project: Project to save as template
            name: Template name
            description: Template description
            category: Template category
            
        Returns:
            Created Template
        """
        template_id = f"custom-{uuid.uuid4().hex[:8]}"
        
        # Extract scene templates
        scene_templates = []
        for scene in project.scenes:
            scene_templates.append({
                "order": scene.order,
                "type": f"scene_{scene.order}",
                "duration": int(scene.audio_duration) if scene.audio_duration else 8,
                "prompt_hint": scene.veo_prompt or ""
            })
        
        template = Template(
            id=template_id,
            name=name,
            description=description,
            category=category,
            default_style=project.default_style,
            target_duration=project.target_duration,
            scene_count=len(project.scenes),
            scene_templates=scene_templates,
            visual_theme=project.visual_theme,
            aspect_ratio=project.aspect_ratio,
            is_builtin=False
        )
        
        # Save to disk
        file_path = self.templates_dir / f"{template_id}.json"
        file_path.write_text(json.dumps(asdict(template), ensure_ascii=False, indent=2), encoding="utf-8")
        
        # Add to cache
        self._custom_templates[template_id] = template
        
        return template
    
    def delete_template(self, template_id: str) -> bool:
        """
        Delete a custom template
        
        Args:
            template_id: Template ID
            
        Returns:
            True if deleted
        """
        # Cannot delete built-in
        for t in BUILTIN_TEMPLATES:
            if t.id == template_id:
                raise ValueError("Cannot delete built-in template")
        
        if template_id in self._custom_templates:
            del self._custom_templates[template_id]
            
            file_path = self.templates_dir / f"{template_id}.json"
            if file_path.exists():
                file_path.unlink()
            
            return True
        
        return False
    
    def get_categories(self) -> list[tuple[str, str]]:
        """Get list of (category_id, display_name) tuples"""
        return [
            ("news", "📰 ข่าว (News)"),
            ("tutorial", "📚 สอน (Tutorial)"),
            ("product", "🛍️ โฆษณา (Product)"),
            ("story", "📖 เล่าเรื่อง (Story)"),
            ("knowledge", "🧠 ให้ความรู้ (Knowledge)"),
            ("entertainment", "🎬 บันเทิง (Entertainment)"),
            ("custom", "⭐ กำหนดเอง (Custom)"),
        ]


# Convenience functions
def list_templates() -> list[Template]:
    """Get all templates"""
    return TemplateManager().list_templates()


def apply_template(template_id: str, topic: str) -> Project:
    """Quick create project from template"""
    return TemplateManager().apply_template(template_id, topic)
