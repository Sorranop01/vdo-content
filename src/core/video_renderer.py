
import logging
import os
import subprocess
import shutil
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import tempfile
from typing import Optional

try:
    from pydub import AudioSegment as PydubSegment
    PYDUB_AVAILABLE = True
except ImportError:
    PYDUB_AVAILABLE = False

from .models import Project

logger = logging.getLogger("vdo_content.video_renderer")

class VideoRenderer:
    """
    Renders draft video previews using FFmpeg.
    Stitches scene cards + audio into a single MP4 file.
    """
    
    # Characters that could be used for command injection
    FORBIDDEN_CHARS = [';', '|', '&', '$', '`', '>', '<', '\n', '\r', '(', ')']
    
    def __init__(self, output_dir: str = "data/renders"):
        self.output_base = Path(output_dir)
        self.output_base.mkdir(parents=True, exist_ok=True)
    
    def _validate_path(self, path: str) -> bool:
        """Validate path is safe for use in subprocess commands"""
        path_str = str(path)
        return not any(c in path_str for c in self.FORBIDDEN_CHARS)
        
    def _get_thai_font_path(self) -> str:
        """Find a suitable Thai font path"""
        # Common locations for Thai fonts in Linux/Docker
        candidates = [
            "/usr/share/fonts/truetype/tlwg/Loma.ttf",
            "/usr/share/fonts/truetype/tlwg/Garuda.ttf",
            "/usr/share/fonts/truetype/tlwg/Waree.ttf",
            "/usr/share/fonts/truetype/noto/NotoSansThai-Regular.ttf",
            "C:/Windows/Fonts/Angsana.ttf",  # Windows fallback
            "C:/Windows/Fonts/Tahoma.ttf",
        ]
        
        for path in candidates:
            if os.path.exists(path):
                return path
        
        return None

    def _create_scene_image(self, text: str, order: int, duration: float, output_path: str):
        """Generate a simple image for the scene"""
        width, height = 1280, 720
        img = Image.new('RGB', (width, height), color=(30, 30, 40))
        draw = ImageDraw.Draw(img)
        
        font_path = self._get_thai_font_path()
        font_lg = None
        font_sm = None
        
        try:
            if font_path:
                # Load Thai font
                font_lg = ImageFont.truetype(font_path, 40)
                font_sm = ImageFont.truetype(font_path, 30)
            else:
                # Fallback to default
                font_lg = ImageFont.load_default()
                font_sm = ImageFont.load_default()
        except Exception:
            font_lg = ImageFont.load_default()
            font_sm = ImageFont.load_default()
            
        # Draw text
        draw.text((50, 50), f"SCENE {order}", fill=(200, 50, 50), font=font_lg)
        draw.text((50, 100), f"Duration: {duration:.1f}s", fill=(255, 255, 255), font=font_sm)
        
        # Word wrap text
        lines = []
        words = text.split()
        curr_line = []
        for word in words:
            curr_line.append(word)
            if len(" ".join(curr_line)) > 40: # Rough char limit
                lines.append(" ".join(curr_line[:-1]))
                curr_line = [word]
        lines.append(" ".join(curr_line))
        
        y = 200
        for line in lines[:10]: # Limit lines
            draw.text((50, y), line, fill=(200, 200, 200), font=font_sm)
            y += 40  # Increased line height
            
        img.save(output_path)

    def _generate_srt(self, project: Project, output_path: str):
        """Generate SRT subtitle file from scenes"""
        def format_time(seconds):
            """Convert seconds to HH:MM:SS,mmm"""
            millis = int((seconds % 1) * 1000)
            seconds = int(seconds)
            mins, secs = divmod(seconds, 60)
            hours, mins = divmod(mins, 60)
            return f"{hours:02d}:{mins:02d}:{secs:02d},{millis:03d}"

        with open(output_path, "w", encoding="utf-8") as f:
            # Use actual timestamps from Whisper when available,
            # fall back to cumulative audio_duration otherwise
            current_time = 0.0
            has_real_timestamps = any(
                s.start_time > 0.0 or s.end_time > 0.0 
                for s in project.scenes if s.order > 1
            )
            
            for i, scene in enumerate(project.scenes):
                if has_real_timestamps and (scene.start_time >= 0.0 and scene.end_time > 0.0):
                    # Use Whisper's actual timestamps
                    start = scene.start_time
                    end = scene.end_time
                else:
                    # Fallback: cumulative from audio_duration
                    start = current_time
                    end = current_time + scene.audio_duration
                    current_time = end
                
                f.write(f"{i+1}\n")
                f.write(f"{format_time(start)} --> {format_time(end)}\n")
                f.write(f"{scene.narration_text}\n\n")

    def _concat_with_transitions(
        self, scenes: list, work_dir: Path, output_path: Path, 
        transition_duration: float = 0.5
    ) -> None:
        """Concat scene clips using FFmpeg xfade filter for smooth transitions.
        
        Args:
            scenes: List of Scene objects (with .transition field)
            work_dir: Working directory containing scene_N.mp4 files
            output_path: Path for the concatenated output
            transition_duration: Duration of each transition in seconds
        """
        if len(scenes) < 2:
            # Single scene, just copy
            src = work_dir / "scene_1.mp4"
            shutil.copy2(str(src), str(output_path))
            return
        
        # Build xfade filter chain progressively
        # [0][1]xfade=...[v01]; [v01][2]xfade=...[v012]; ...
        inputs = []
        filter_parts = []
        
        for i, scene in enumerate(scenes):
            inputs.extend(["-i", str(work_dir / f"scene_{scene.order}.mp4")])
        
        prev_label = "0:v"
        cumulative_offset = 0.0
        
        for i in range(len(scenes) - 1):
            scene = scenes[i]
            transition = getattr(scene, 'transition', 'cut')
            
            # Map transition types to FFmpeg xfade names
            xfade_type = {
                'fade': 'fade',
                'dissolve': 'dissolve',
            }.get(transition, None)
            
            next_label = f"{i+1}:v"
            out_label = f"v{i}" if i < len(scenes) - 2 else "vout"
            
            # Calculate offset: when the transition starts
            offset = cumulative_offset + scenes[i].audio_duration - transition_duration
            offset = max(0.0, offset)  # Safety: don't go negative
            
            if xfade_type:
                filter_parts.append(
                    f"[{prev_label}][{next_label}]xfade=transition={xfade_type}"
                    f":duration={transition_duration}:offset={offset:.3f}[{out_label}]"
                )
                # After xfade, the output is shorter by transition_duration
                cumulative_offset = offset
            else:
                # 'cut' transition: just concatenate (no xfade)
                filter_parts.append(
                    f"[{prev_label}][{next_label}]xfade=transition=fade"
                    f":duration=0:offset={offset:.3f}[{out_label}]"
                )
                cumulative_offset += scenes[i].audio_duration
            
            prev_label = out_label
        
        if not filter_parts:
            # Fallback to simple concat
            return
        
        filter_complex = ";".join(filter_parts)
        
        cmd = [
            "ffmpeg", "-y",
            *inputs,
            "-filter_complex", filter_complex,
            "-map", f"[vout]",
            "-c:v", "libx264", "-pix_fmt", "yuv420p",
            str(output_path)
        ]
        
        try:
            subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except subprocess.CalledProcessError:
            # Fallback to simple concat if xfade fails
            logger.warning("Transition rendering failed, falling back to hard cuts")
            list_file = work_dir / "input_list.txt"
            cmd_fallback = [
                "ffmpeg", "-y",
                "-f", "concat", "-safe", "0",
                "-i", str(list_file),
                "-c", "copy",
                str(output_path)
            ]
            subprocess.run(cmd_fallback, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    def _validate_audio_sync(self, project: Project) -> None:
        """Validate that total scene duration roughly matches actual audio length.
        Logs a warning if drift exceeds 1 second."""
        if not PYDUB_AVAILABLE or not project.audio_path:
            return
        try:
            audio = PydubSegment.from_file(project.audio_path)
            actual_length = len(audio) / 1000.0  # ms -> seconds
            scene_total = sum(
                s.audio_duration if s.audio_duration > 0 else s.estimated_duration
                for s in project.scenes
            )
            drift = abs(actual_length - scene_total)
            if drift > 1.0:
                logger.warning(
                    f"Audio sync drift: audio file is {actual_length:.1f}s but "
                    f"scenes total {scene_total:.1f}s (drift: {drift:.1f}s). "
                    f"Subtitles may be offset."
                )
        except Exception as e:
            logger.debug(f"Audio validation skipped: {e}")

    def render_draft(self, project: Project, music_path: Optional[str] = None) -> Optional[str]:
        """
        Render the full draft video with subtitles and background music.
        Returns path to the output mp4 file.
        """
        if not project.audio_path or not os.path.exists(project.audio_path):
            raise FileNotFoundError("Project audio file not found")
        
        # Validate audio/scene sync before rendering
        self._validate_audio_sync(project)
            
        work_dir = self.output_base / f"temp_{project.project_id}"
        if work_dir.exists():
            shutil.rmtree(work_dir)
        work_dir.mkdir()
        
        output_file = self.output_base / f"{project.project_id}_draft.mp4"
        list_file_path = work_dir / "input_list.txt"
        srt_path = work_dir / "subs.srt"
        
        try:
            # 1. Generate SRT
            self._generate_srt(project, str(srt_path))
            
            # 2. Create video parts
            video_parts = []
            for scene in project.scenes:
                # Create image
                img_path = work_dir / f"scene_{scene.order}.jpg"
                scene_text = f"{scene.narration_text}\n\n[{scene.veo_prompt[:50]}...]"
                self._create_scene_image(scene_text, scene.order, scene.audio_duration, str(img_path))
                
                # Create video snippet
                vid_path = work_dir / f"scene_{scene.order}.mp4"
                
                # FFmpeg: Loop image
                cmd = [
                    "ffmpeg", "-y",
                    "-loop", "1", "-i", str(img_path),
                    "-t", str(scene.audio_duration),
                    "-c:v", "libx264", "-pix_fmt", "yuv420p", "-vf", "scale=1280:720",
                    str(vid_path)
                ]
                subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                video_parts.append(f"file '{vid_path.name}'")
            
            # Write list file
            with open(list_file_path, "w") as f:
                f.write("\n".join(video_parts))
            
            # 3. Concat video parts (with transitions when specified)
            silent_video = work_dir / "silent_full.mp4"
            
            # Check if any scene uses fade/dissolve transitions
            has_transitions = any(
                getattr(s, 'transition', 'cut') in ('fade', 'dissolve')
                for s in project.scenes[:-1]  # Last scene has no outgoing transition
            )
            
            if has_transitions and len(video_parts) > 1:
                # Use xfade filter for smooth transitions
                self._concat_with_transitions(project.scenes, work_dir, silent_video)
            else:
                # Simple concat (hard cuts)
                cmd_concat = [
                    "ffmpeg", "-y",
                    "-f", "concat", "-safe", "0",
                    "-i", str(list_file_path),
                    "-c", "copy",
                    str(silent_video)
                ]
                subprocess.run(cmd_concat, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            
            # 4. Mux Audio & Burn Subtitles & Mix Music
            abs_srt_path = str(srt_path.absolute()).replace("\\", "/").replace(":", "\\:")
            
            # Base command parts
            cmd_mux = ["ffmpeg", "-y", "-i", str(silent_video), "-i", project.audio_path]
            
            # Filter complex construction
            # Use 'Loma' font which is available in fonts-thai-tlwg
            filter_complex = f"[0:v]subtitles='{abs_srt_path}':force_style='FontName=Loma,FontSize=24,PrimaryColour=&H00FFFFFF,OutlineColour=&H00000000,BorderStyle=1,Outline=2,Shadow=0,MarginV=30'[v]"
            map_args = ["-map", "[v]"]
            
            if music_path and os.path.exists(music_path):
                # Add music input
                cmd_mux.extend(["-stream_loop", "-1", "-i", music_path])
                
                # Update filter complex to mix audio
                # [1:a] is speech, [2:a] is music
                # Reduce music volume to 15%
                filter_complex += f";[2:a]volume=0.15[m];[1:a][m]amix=inputs=2:duration=first:dropout_transition=2[a]"
                map_args.extend(["-map", "[a]"])
            else:
                map_args.extend(["-map", "1:a"]) # Just speech
            
            cmd_mux.extend([
                "-filter_complex", filter_complex,
                *map_args,
                "-c:v", "libx264", "-c:a", "aac",
                "-shortest",
                str(output_file)
            ])
            
            subprocess.run(cmd_mux, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            
            return str(output_file)
            
        except subprocess.CalledProcessError as e:
            logger.error(f"FFmpeg Error: {e}")
            raise RuntimeError("Failed to render video")
        finally:
            # Cleanup temp
            if work_dir.exists():
                shutil.rmtree(work_dir)

