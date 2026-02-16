import logging
import os
import io
import json
import shutil
import zipfile
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any

from PIL import Image, ImageDraw, ImageFont
from .models import Project, Scene

logger = logging.getLogger("vdo_content.exporter")

class ProjectExporter:
    """
    Export project assets for production/editing
    Generates Scene Cards (Placeholders) and organizes files
    """
    
    def __init__(self, output_dir: str = "exports"):
        self.output_base = Path(output_dir)
        self.output_base.mkdir(exist_ok=True)
        
    def create_scene_card(self, scene: Scene, output_path: str, width: int = 1920, height: int = 1080):
        """Create a placeholder image for the scene with details"""
        # Create dark background
        img = Image.new('RGB', (width, height), color=(20, 20, 30))
        draw = ImageDraw.Draw(img)
        
        # Try to load a font, fallback to default
        try:
            # Try to find a system font
            font_large = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 80)
            font_medium = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 40)
            font_small = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 30)
        except IOError:
            font_large = ImageFont.load_default()
            font_medium = ImageFont.load_default()
            font_small = ImageFont.load_default()
        
        # Draw Scene Number
        draw.text((100, 100), f"SCENE {scene.order}", font=font_large, fill=(233, 69, 96))
        
        # Draw Timing
        draw.text((100, 220), f"Time: {scene.time_range}", font=font_medium, fill=(255, 255, 255))
        draw.text((100, 280), f"Duration: {scene.audio_duration}s", font=font_medium, fill=(255, 255, 255))
        
        # Draw Narration (Wrap text)
        draw.text((100, 400), "Narration:", font=font_medium, fill=(100, 200, 255))
        self._draw_text_wrapped(draw, scene.narration_text, 100, 460, font_medium, width - 200)
        
        # Draw Prompt info
        draw.text((100, 700), "Veo 3 Prompt:", font=font_medium, fill=(100, 255, 100))
        # Just show start of prompt
        prompt_preview = (scene.veo_prompt[:150] + '...') if len(scene.veo_prompt) > 150 else scene.veo_prompt
        self._draw_text_wrapped(draw, prompt_preview, 100, 760, font_small, width - 200, color=(200, 200, 200))
        
        # Save
        img.save(output_path)

    def _draw_text_wrapped(self, draw, text, x, y, font, max_width, color=(255, 255, 255)):
        """Helper to draw wrapped text"""
        lines = []
        words = text.split()
        current_line = []
        
        for word in words:
            current_line.append(word)
            # Check width
            line_str = " ".join(current_line)
            bbox = draw.textbbox((0, 0), line_str, font=font)
            if bbox[2] > max_width:
                current_line.pop()
                lines.append(" ".join(current_line))
                current_line = [word]
        
        if current_line:
            lines.append(" ".join(current_line))
            
        try:
            # For TrueType fonts
            line_height = font.getbbox("Ay")[3] + 10
        except AttributeError:
            # Fallback for default font
            line_height = 15
            
        for i, line in enumerate(lines):
            draw.text((x, y + i * line_height), line, font=font, fill=color)

    def export_project(self, project: Project) -> str:
        """
        Export full production kit
        Returns: Path to the exported folder
        """
        # Create project export folder
        safe_title = "".join([c for c in project.title if c.isalnum() or c in (' ', '-', '_')]).strip().replace(' ', '_')
        export_dir = self.output_base / f"{safe_title}_Kit"
        
        if export_dir.exists():
            shutil.rmtree(export_dir)
        export_dir.mkdir(parents=True)
        
        assets_dir = export_dir / "Scene_Cards"
        assets_dir.mkdir()
        
        logger.info(f"Exporting to {export_dir}...")
        
        # 1. Copy Master Audio
        if project.audio_path and os.path.exists(project.audio_path):
            ext = Path(project.audio_path).suffix
            shutil.copy2(project.audio_path, export_dir / f"Master_Audio{ext}")
        
        # 2. Generate Scene Cards
        for scene in project.scenes:
            # Sanitize duration for filename
            duration_str = f"{scene.audio_duration:.1f}".replace('.', '-')
            card_filename = f"Scene_{scene.order:02d}_{duration_str}s.jpg"
            self.create_scene_card(scene, str(assets_dir / card_filename))
            
        # 3. Generate Manifest / Subtitle file (SRT-like but simpler)
        with open(export_dir / "Timeline.txt", "w", encoding="utf-8") as f:
            f.write(f"Project: {project.title}\n")
            f.write(f"Total Duration: {project.total_duration}s\n")
            f.write("="*50 + "\n\n")
            
            for scene in project.scenes:
                f.write(f"SCENE {scene.order:02d}\n")
                f.write(f"Time: {scene.time_range}\n")
                f.write(f"Audio: {scene.narration_text}\n")
                f.write(f"Prompt: {scene.veo_prompt}\n")
                f.write("-" * 30 + "\n")
                
        return str(export_dir)
    
    # ============ NEW: Batch Export Methods ============
    
    def export_full_package(self, project: Project) -> bytes:
        """
        Export complete project as a ZIP file in memory.
        
        Contents:
        - prompts.txt: All Veo 3 prompts formatted for easy use
        - script.txt: Thai narration script
        - scenes.json: Structured scene data
        - metadata.json: Project metadata
        - README.md: Usage instructions
        
        Returns:
            bytes: ZIP file content as bytes
        """
        buffer = io.BytesIO()
        
        with zipfile.ZipFile(buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
            # 1. All prompts as text file
            prompts_content = self._generate_prompts_file(project)
            zf.writestr("prompts.txt", prompts_content)
            
            # 2. Script file (Thai narration)
            script_content = self._generate_script_file(project)
            zf.writestr("script.txt", script_content)
            
            # 3. Scenes as JSON
            scenes_json = self._generate_scenes_json(project)
            zf.writestr("scenes.json", json.dumps(scenes_json, ensure_ascii=False, indent=2))
            
            # 4. Metadata JSON
            metadata = self._generate_metadata_json(project)
            zf.writestr("metadata.json", json.dumps(metadata, ensure_ascii=False, indent=2))
            
            # 5. README with usage instructions
            readme_content = self._generate_readme(project)
            zf.writestr("README.md", readme_content)
            
            # 6. Timeline (existing format)
            timeline_content = self._generate_timeline(project)
            zf.writestr("Timeline.txt", timeline_content)
        
        buffer.seek(0)
        return buffer.getvalue()
    
    def export_all_prompts_text(self, project: Project) -> str:
        """
        Export all prompts as formatted text for easy copy-paste.
        
        Format:
        === SCENE 1 (0:00 - 0:08) ===
        [prompt text]
        
        === SCENE 2 (0:08 - 0:15) ===
        [prompt text]
        ...
        
        Returns:
            str: Formatted prompts text
        """
        if not project.scenes:
            return "No scenes found."
        
        lines = [
            f"# {project.title} - Veo 3 Prompts",
            f"# Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            f"# Total Scenes: {len(project.scenes)}",
            f"# Total Duration: {project.total_duration:.1f}s",
            "",
            "=" * 60,
            ""
        ]
        
        for scene in project.scenes:
            # Scene header
            lines.append(f"=== SCENE {scene.order} ({scene.time_range}) ===")
            lines.append("")
            
            # Video Style Prompt
            lines.append("[🎬 Video Style Prompt]")
            lines.append(scene.veo_prompt if scene.veo_prompt else "[No prompt generated]")
            lines.append("")
            
            # Thai Voiceover (pure narration)
            if scene.voiceover_prompt:
                lines.append("[🎤 เสียงพากย์ไทย]")
                lines.append(scene.voiceover_prompt)
                lines.append("")
            
            # Speaking Style (English direction)
            if scene.voice_tone:
                lines.append("[🎭 Speaking Style]")
                lines.append(scene.voice_tone)
                lines.append("")
            
            lines.append("-" * 60)
            lines.append("")
        
        return "\n".join(lines)
    
    def _generate_prompts_file(self, project: Project) -> str:
        """Generate prompts.txt content — full 4-section format"""
        lines = [
            f"VDO CONTENT - VEO 3 PROMPTS (8s per clip)",
            f"Project: {project.title}",
            f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"Total Scenes: {len(project.scenes)}",
            "",
            "=" * 70,
            ""
        ]
        
        for scene in project.scenes:
            lines.append(f"[SCENE {scene.order}] Veo 3: 8s | Narration: {scene.audio_duration:.1f}s | Time: {scene.time_range}")
            lines.append("-" * 50)
            
            # Video Style Prompt
            lines.append("[🎬 Video Style Prompt]")
            lines.append(scene.veo_prompt if scene.veo_prompt else "(No prompt)")
            lines.append("")
            
            # Thai Voiceover
            if scene.voiceover_prompt:
                lines.append("[🎤 เสียงพากย์ไทย]")
                lines.append(scene.voiceover_prompt)
                lines.append("")
            
            # Speaking Style
            if scene.voice_tone:
                lines.append("[🎭 Speaking Style]")
                lines.append(scene.voice_tone)
                lines.append("")
            
            lines.append("")
        
        return "\n".join(lines)
    
    def _generate_script_file(self, project: Project) -> str:
        """Generate script.txt with Thai narration"""
        lines = [
            f"VDO CONTENT - THAI NARRATION SCRIPT",
            f"Project: {project.title}",
            f"Topic: {project.topic}",
            f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            "=" * 70,
            ""
        ]
        
        # Full script if available
        if project.full_script:
            lines.append("=== FULL SCRIPT ===")
            lines.append("")
            lines.append(project.full_script)
            lines.append("")
            lines.append("=" * 70)
            lines.append("")
        
        # Scene-by-scene
        lines.append("=== SCENE BREAKDOWN ===")
        lines.append("")
        
        for scene in project.scenes:
            lines.append(f"[SCENE {scene.order}] {scene.time_range}")
            lines.append(scene.narration_text)
            lines.append("")
        
        return "\n".join(lines)
    
    def _generate_scenes_json(self, project: Project) -> list:
        """Generate structured scene data as JSON-serializable list"""
        scenes_data = []
        
        for scene in project.scenes:
            scene_dict = {
                "scene_id": scene.scene_id,
                "order": scene.order,
                "start_time": scene.start_time,
                "end_time": scene.end_time,
                "duration": scene.audio_duration,
                "time_range": scene.time_range,
                "narration_text": scene.narration_text,
                "word_count": scene.word_count,
                "veo_prompt": scene.veo_prompt,
                "voiceover_prompt": scene.voiceover_prompt,
                "voice_tone": scene.voice_tone,
                "emotion": scene.emotion,
                "visual_style": scene.visual_style,
                "camera_movement": scene.camera_movement,
                "transition": scene.transition,
            }
            scenes_data.append(scene_dict)
        
        return scenes_data
    
    def _generate_metadata_json(self, project: Project) -> Dict[str, Any]:
        """Generate project metadata as JSON-serializable dict"""
        return {
            "project_id": project.project_id,
            "title": project.title,
            "topic": project.topic,
            "description": project.description,
            "status": project.status,
            "scene_count": len(project.scenes),
            "total_duration": project.total_duration,
            "character_reference": project.character_reference,
            "default_style": project.default_style,
            "visual_theme": project.visual_theme,
            "aspect_ratio": project.aspect_ratio,
            "audio_path": project.audio_path,
            "created_at": project.created_at.isoformat() if project.created_at else None,
            "updated_at": project.updated_at.isoformat() if project.updated_at else None,
            "export_timestamp": datetime.now().isoformat(),
            "version": "2.2.0"
        }
    
    def _generate_readme(self, project: Project) -> str:
        """Generate README.md with usage instructions"""
        return f"""# {project.title}

## Project Overview

- **Topic:** {project.topic}
- **Scenes:** {len(project.scenes)}
- **Total Duration:** {project.total_duration:.1f}s
- **Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M')}

## Included Files

| File | Description |
|------|-------------|
| `prompts.txt` | All Veo 3 prompts ready for video generation |
| `script.txt` | Thai narration script |
| `scenes.json` | Structured scene data (for programmatic use) |
| `metadata.json` | Project metadata |
| `Timeline.txt` | Simple timeline with all scene info |

## How to Use

### Veo 3 Prompts

1. Open `prompts.txt`
2. Copy each scene's prompt
3. Paste into Veo 3 video generator
4. Generate video for each scene (max 8 seconds each)

### Video Production

Each scene is designed for ≤8 seconds to fit Veo 3's maximum duration.

**Recommended workflow:**
1. Generate videos using prompts in order
2. Record or generate TTS audio using the script
3. Combine videos + audio in your video editor
4. Export final video

## Scene Summary

| Scene | Duration | Narration Preview |
|-------|----------|-------------------|
""" + "\n".join([
            f"| {s.order} | {s.audio_duration:.1f}s | {s.narration_text[:50]}... |"
            for s in project.scenes
        ]) + """

---

*Generated by VDO Content v2.2.0*
"""
    
    def _generate_timeline(self, project: Project) -> str:
        """Generate Timeline.txt (existing format)"""
        lines = [
            f"Project: {project.title}",
            f"Total Duration: {project.total_duration:.1f}s",
            "=" * 50,
            ""
        ]
        
        for scene in project.scenes:
            lines.append(f"SCENE {scene.order:02d}")
            lines.append(f"Time: {scene.time_range}")
            lines.append(f"Audio: {scene.narration_text}")
            lines.append(f"Prompt: {scene.veo_prompt}")
            lines.append("-" * 30)
        
        return "\n".join(lines)