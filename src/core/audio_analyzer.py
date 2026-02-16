"""
Audio Analyzer for VDO Content V2
Analyzes audio files and splits into segments based on timing
"""

import os
from pathlib import Path
from typing import Optional
from pydantic import BaseModel

# Check for pydub availability
try:
    from pydub import AudioSegment as PydubAudioSegment
    from pydub.silence import detect_nonsilent
    PYDUB_AVAILABLE = True
except ImportError:
    PYDUB_AVAILABLE = False
    PydubAudioSegment = None

from .models import AudioSegment, Scene


class AudioAnalyzer:
    """
    Analyzes audio files and creates scene segments
    Uses pydub for audio processing
    """
    
    # Settings
    MIN_SILENCE_LEN = 300  # ms - minimum silence length to consider as pause
    SILENCE_THRESH = -40   # dB - silence threshold
    MAX_SEGMENT_DURATION = 8.0  # seconds - Veo 3 limit
    
    def __init__(
        self,
        min_silence_len: int = 300,
        silence_thresh: int = -40,
        max_segment_duration: float = 8.0
    ):
        self.min_silence_len = min_silence_len
        self.silence_thresh = silence_thresh
        self.max_segment_duration = max_segment_duration
    
    def is_available(self) -> bool:
        """Check if pydub is available"""
        return PYDUB_AVAILABLE
    
    def analyze_audio(
        self,
        audio_path: str,
        script_segments: Optional[list[str]] = None
    ) -> list[AudioSegment]:
        """
        Analyze audio file and split into segments
        
        Args:
            audio_path: Path to audio file (mp3, wav, etc.)
            script_segments: Optional list of text segments to map
            
        Returns:
            List of AudioSegment objects with timing
        """
        if not PYDUB_AVAILABLE:
            raise RuntimeError(
                "pydub is not installed. Install with: pip install pydub\n"
                "Also requires ffmpeg: apt-get install ffmpeg"
            )
        
        if not os.path.exists(audio_path):
            raise FileNotFoundError(f"Audio file not found: {audio_path}")
        
        # Load audio
        audio = PydubAudioSegment.from_file(audio_path)
        total_duration = len(audio) / 1000.0  # Convert ms to seconds
        
        # Detect non-silent parts
        nonsilent_ranges = detect_nonsilent(
            audio,
            min_silence_len=self.min_silence_len,
            silence_thresh=self.silence_thresh
        )
        
        if not nonsilent_ranges:
            # No silence detected, treat as single segment
            return self._split_by_duration(0, total_duration, script_segments)
        
        # Create segments from non-silent ranges
        raw_segments = []
        for start_ms, end_ms in nonsilent_ranges:
            start_sec = start_ms / 1000.0
            end_sec = end_ms / 1000.0
            duration = end_sec - start_sec
            
            # If segment is too long, split it
            if duration > self.max_segment_duration:
                raw_segments.extend(
                    self._split_long_segment(start_sec, end_sec)
                )
            else:
                raw_segments.append((start_sec, end_sec))
        
        # Create AudioSegment objects
        segments = []
        for i, (start, end) in enumerate(raw_segments):
            text = ""
            if script_segments and i < len(script_segments):
                text = script_segments[i]
            
            segments.append(AudioSegment(
                order=i + 1,
                start_time=round(start, 2),
                end_time=round(end, 2),
                duration=round(end - start, 2),
                text_content=text
            ))
        
        return segments
    
    def _split_long_segment(
        self,
        start: float,
        end: float
    ) -> list[tuple[float, float]]:
        """Split a long segment into chunks ≤ max_duration"""
        chunks = []
        current = start
        
        while current < end:
            chunk_end = min(current + self.max_segment_duration, end)
            chunks.append((current, chunk_end))
            current = chunk_end
        
        return chunks
    
    def _split_by_duration(
        self,
        start: float,
        total_duration: float,
        script_segments: Optional[list[str]] = None
    ) -> list[AudioSegment]:
        """Split audio by fixed duration when no silence detected"""
        segments = []
        current = start
        order = 1
        
        while current < total_duration:
            end = min(current + self.max_segment_duration, total_duration)
            
            text = ""
            if script_segments and order - 1 < len(script_segments):
                text = script_segments[order - 1]
            
            segments.append(AudioSegment(
                order=order,
                start_time=round(current, 2),
                end_time=round(end, 2),
                duration=round(end - current, 2),
                text_content=text
            ))
            
            current = end
            order += 1
        
        return segments
    
    def get_audio_duration(self, audio_path: str) -> float:
        """Get total duration of audio file in seconds"""
        if not PYDUB_AVAILABLE:
            raise RuntimeError("pydub is not installed")
        
        audio = PydubAudioSegment.from_file(audio_path)
        return len(audio) / 1000.0
    
    def create_scenes_from_segments(
        self,
        segments: list[AudioSegment],
        style: str = "documentary",
        character_ref: str = ""
    ) -> list[Scene]:
        """
        Convert audio segments to Scene objects
        
        Args:
            segments: List of AudioSegment from analysis
            style: Visual style for scenes
            character_ref: Character reference for consistency
            
        Returns:
            List of Scene objects ready for prompt generation
        """
        scenes = []
        
        for seg in segments:
            scene = Scene(
                order=seg.order,
                start_time=seg.start_time,
                end_time=seg.end_time,
                narration_text=seg.text_content,
                visual_style=style,
                subject_description=character_ref,
                audio_synced=True
            )
            # Duration from audio takes precedence
            scene.estimated_duration = seg.duration
            scenes.append(scene)
        
        return scenes


# Convenience function
def analyze_audio(
    audio_path: str,
    script_segments: Optional[list[str]] = None,
    max_duration: float = 8.0
) -> list[AudioSegment]:
    """
    Convenience function to analyze audio
    
    Args:
        audio_path: Path to audio file
        script_segments: Optional text segments to map
        max_duration: Maximum segment duration (default 8s for Veo 3)
        
    Returns:
        List of AudioSegment objects
    """
    analyzer = AudioAnalyzer(max_segment_duration=max_duration)
    return analyzer.analyze_audio(audio_path, script_segments)
