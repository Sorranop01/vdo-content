"""
Audio Transcription Module for VDO Content V3
Uses Faster-Whisper for local speech-to-text + LLM post-correction
Supports Thai language with high accuracy
"""

import logging
import os
import json
import re
from pathlib import Path
from typing import Optional
from dataclasses import dataclass, field

logger = logging.getLogger("vdo_content.transcriber")

# Check for faster-whisper availability
try:
    from faster_whisper import WhisperModel
    WHISPER_AVAILABLE = True
except ImportError:
    WHISPER_AVAILABLE = False
    WhisperModel = None


@dataclass
class WordInfo:
    """A single word with timing from Whisper"""
    word: str
    start: float
    end: float
    probability: float = 0.0


@dataclass
class TranscriptSegment:
    """A segment of transcribed audio"""
    start: float
    end: float
    text: str
    confidence: float = 0.0
    words: list[WordInfo] = field(default_factory=list)


class AudioTranscriber:
    """
    Transcribes audio files using Faster-Whisper
    Supports Thai language with automatic scene splitting at ≤8 seconds
    """
    
    # Model sizes: tiny, base, small, medium, large-v3
    DEFAULT_MODEL = "large-v3"  # Best accuracy for Thai
    MAX_SEGMENT_DURATION = 8.0  # Veo 3 clip length (hard ceiling)
    MIN_SEGMENT_DURATION = 7.0  # Target minimum — start looking for break points here
    
    def __init__(
        self,
        model_size: str = DEFAULT_MODEL,
        device: str = "auto",  # "auto", "cpu", or "cuda"
        compute_type: str = "auto"  # "auto", "int8", "float16"
    ):
        """
        Initialize transcriber
        
        Args:
            model_size: Whisper model size (tiny/base/small/medium/large-v3)
            device: Device to use (auto, cpu, cuda)
            compute_type: Computation type for optimization
        """
        self.model_size = model_size
        self.device = device
        self.compute_type = compute_type
        self._model = None
    
    def is_available(self) -> bool:
        """Check if faster-whisper is available"""
        return WHISPER_AVAILABLE
    
    @property
    def model(self) -> "WhisperModel":
        """Lazy load Whisper model with robust fallback"""
        if self._model is None and self.is_available():
            logger.info(f"Loading Whisper model: {self.model_size}...")
            
            # Defines attempts: (device, compute_type)
            attempts = []
            # 1. Try user preference first
            attempts.append((self.device, self.compute_type))
            
            # 2. Try CPU int8 (Standard CPU fallback)
            if self.device != "cpu" or self.compute_type != "int8":
                attempts.append(("cpu", "int8"))
                
            # 3. Try CPU float32 (Safe CPU fallback)
            attempts.append(("cpu", "float32"))
            
            last_error = None
            
            for device, compute_type in attempts:
                try:
                    logger.info(f"Attempting load with device='{device}', compute_type='{compute_type}'...")
                    self._model = WhisperModel(
                        self.model_size,
                        device=device,
                        compute_type=compute_type
                    )
                    logger.info(f"Model loaded successfully (device={device}, compute_type={compute_type})")
                    return self._model
                except Exception as e:
                    logger.error(f"Failed to load with device='{device}', compute_type='{compute_type}': {e}")
                    last_error = e
            
            # If we get here, all attempts failed
            if last_error:
                raise last_error
                
        return self._model
    
    def transcribe(
        self,
        audio_path: str,
        language: str = "th",
        split_to_scenes: bool = True,
        initial_prompt: Optional[str] = None
    ) -> list[TranscriptSegment]:
        """
        Transcribe audio file to text segments
        
        Args:
            audio_path: Path to audio file (mp3, wav, etc.)
            language: Language code (th=Thai, en=English)
            split_to_scenes: If True, merge/split segments to fit ≤8 seconds
            
        Returns:
            List of TranscriptSegment with timing
        """
        if not self.is_available():
            raise RuntimeError(
                "faster-whisper is not installed. Install with: pip install faster-whisper"
            )
        
        if not os.path.exists(audio_path):
            raise FileNotFoundError(f"Audio file not found: {audio_path}")
        
        # Transcribe with word-level timestamps for smart splitting
        segments_gen, info = self.model.transcribe(
            audio_path,
            language=language,
            beam_size=5,
            word_timestamps=True,
            vad_filter=True,  # Voice Activity Detection for better segmentation
            condition_on_previous_text=True,  # Use context across segments
            initial_prompt=initial_prompt
        )
        
        # Convert generator to list of segments with word-level timing
        raw_segments = []
        for segment in segments_gen:
            # Extract word-level timestamps
            words = []
            if hasattr(segment, 'words') and segment.words:
                for w in segment.words:
                    words.append(WordInfo(
                        word=w.word,
                        start=round(w.start, 2),
                        end=round(w.end, 2),
                        probability=round(w.probability, 3) if hasattr(w, 'probability') else 0.0
                    ))
            
            raw_segments.append(TranscriptSegment(
                start=round(segment.start, 2),
                end=round(segment.end, 2),
                text=segment.text.strip(),
                confidence=round(segment.avg_logprob, 3) if hasattr(segment, 'avg_logprob') else 0.0,
                words=words
            ))
        
        if split_to_scenes:
            return self._optimize_for_scenes(raw_segments)
        
        return raw_segments
    
    def _optimize_for_scenes(
        self,
        segments: list[TranscriptSegment]
    ) -> list[TranscriptSegment]:
        """
        Optimize segments for Veo 3 (target 7-8 seconds each).
        
        Strategy (3 phases):
        1. ACCUMULATE: Keep adding words while duration < 7s (MIN)
        2. SWEET ZONE (7-8s): Proactively look for natural Thai break points
           (ครับ, ค่ะ, นะ, punctuation) and cut there
        3. HARD CUT (>8s): Force-cut at 8s ceiling if no break found
        
        After building all segments, a final merge pass combines any
        trailing short segment (<7s) into its predecessor.
        """
        if not segments:
            return []
        
        # First: collect ALL words with timestamps across all segments
        all_words: list[WordInfo] = []
        for seg in segments:
            if seg.words:
                all_words.extend(seg.words)
            else:
                # Fallback: treat entire segment text as one "word"
                all_words.append(WordInfo(
                    word=seg.text,
                    start=seg.start,
                    end=seg.end
                ))
        
        if not all_words:
            return segments
        
        # Natural break indicators for Thai speech
        THAI_BREAK_PARTICLES = ('ครับ', 'ค่ะ', 'นะ', 'เลย', 'ด้วย', 'แล้ว')
        
        def _is_natural_break(w_text: str) -> bool:
            """Check if a word is a natural sentence/clause break point."""
            stripped = w_text.strip()
            return (
                stripped.endswith(THAI_BREAK_PARTICLES)
                or stripped.endswith((' ', ',', '.', '!', '?', '…'))
            )
        
        def _flush_scene(words: list[WordInfo], start: float) -> TranscriptSegment | None:
            """Create a TranscriptSegment from accumulated words."""
            if not words:
                return None
            text = "".join(w.word for w in words).strip()
            if not text:
                return None
            return TranscriptSegment(
                start=round(start, 2),
                end=round(words[-1].end, 2),
                text=text,
                words=list(words),
            )
        
        # === Phase 1+2+3: Build segments with 7-8s targeting ===
        optimized: list[TranscriptSegment] = []
        scene_words: list[WordInfo] = []
        scene_start = all_words[0].start
        
        for word in all_words:
            potential_end = word.end
            potential_duration = potential_end - scene_start
            
            if potential_duration <= self.MIN_SEGMENT_DURATION:
                # Phase 1: Still under 7s — keep accumulating
                scene_words.append(word)
            
            elif potential_duration <= self.MAX_SEGMENT_DURATION:
                # Phase 2: SWEET ZONE (7-8s) — add the word, then check for break
                scene_words.append(word)
                
                if _is_natural_break(word.word):
                    # Great break point found! Flush this scene
                    seg = _flush_scene(scene_words, scene_start)
                    if seg:
                        optimized.append(seg)
                    scene_words = []
                    scene_start = word.end  # Next scene starts after this word
            
            else:
                # Phase 3: Would EXCEED 8s — must cut before adding this word
                if scene_words:
                    # Try to find a natural break in the last few words
                    best_split = len(scene_words)  # default: all current words
                    search_start = max(0, len(scene_words) - 5)
                    for j in range(len(scene_words) - 1, search_start - 1, -1):
                        if _is_natural_break(scene_words[j].word):
                            best_split = j + 1
                            break
                    
                    split_words = scene_words[:best_split]
                    seg = _flush_scene(split_words, scene_start)
                    if seg:
                        optimized.append(seg)
                    
                    # Remaining words + current word become new scene
                    remaining = scene_words[best_split:]
                    scene_words = remaining + [word]
                    scene_start = scene_words[0].start if scene_words else word.start
                else:
                    # Single word longer than limit (rare) — keep it
                    scene_words = [word]
                    scene_start = word.start
        
        # Flush remaining words
        if scene_words:
            seg = _flush_scene(scene_words, scene_start)
            if seg:
                optimized.append(seg)
        
        # === Final merge pass: merge trailing short segment into predecessor ===
        if len(optimized) >= 2:
            last = optimized[-1]
            last_duration = last.end - last.start
            if last_duration < self.MIN_SEGMENT_DURATION:
                prev = optimized[-2]
                merged_duration = last.end - prev.start
                # Only merge if the combined segment won't be excessively long
                # Allow up to 10s for the merge (slightly over 8s is better than 2s orphan)
                if merged_duration <= self.MAX_SEGMENT_DURATION + 2.0:
                    merged_words = (prev.words or []) + (last.words or [])
                    merged_text = prev.text + last.text
                    optimized[-2] = TranscriptSegment(
                        start=prev.start,
                        end=last.end,
                        text=merged_text.strip(),
                        words=merged_words,
                    )
                    optimized.pop()
        
        return optimized
    
    def _split_long_segment(
        self,
        segment: TranscriptSegment
    ) -> list[TranscriptSegment]:
        """
        Split a segment that's too long (>8s)
        Uses word-level timestamps when available for accurate splitting
        """
        # If we have word timestamps, use them for precise splitting
        if segment.words and len(segment.words) > 1:
            return self._split_by_word_timestamps(segment)
        
        # Fallback: time-proportional splitting
        duration = segment.end - segment.start
        num_parts = int(duration / self.MAX_SEGMENT_DURATION) + 1
        time_per_part = round(duration / num_parts, 2)
        
        words = segment.text.split()
        if not words:
            return [segment]
        
        words_per_part = max(1, len(words) // num_parts)
        result = []
        for i in range(num_parts):
            start_idx = i * words_per_part
            end_idx = (i + 1) * words_per_part if i < num_parts - 1 else len(words)
            text = " ".join(words[start_idx:end_idx])
            if text:
                result.append(TranscriptSegment(
                    start=round(segment.start + i * time_per_part, 2),
                    end=round(segment.start + (i + 1) * time_per_part, 2),
                    text=text
                ))
        
        return result if result else [segment]
    
    def _split_by_word_timestamps(
        self,
        segment: TranscriptSegment
    ) -> list[TranscriptSegment]:
        """
        Split using actual word timestamps from Whisper.
        Finds natural break points near 8s boundaries.
        """
        words = segment.words
        THAI_BREAK_PARTICLES = ('ครับ', 'ค่ะ', 'นะ', 'เลย', 'แล้ว')
        
        result = []
        current_words: list[WordInfo] = []
        scene_start = words[0].start
        
        for word in words:
            potential_duration = word.end - scene_start
            
            if potential_duration <= self.MAX_SEGMENT_DURATION:
                current_words.append(word)
            else:
                if current_words:
                    text = "".join(w.word for w in current_words).strip()
                    if text:
                        result.append(TranscriptSegment(
                            start=round(scene_start, 2),
                            end=round(current_words[-1].end, 2),
                            text=text,
                            words=current_words
                        ))
                current_words = [word]
                scene_start = word.start
        
        if current_words:
            text = "".join(w.word for w in current_words).strip()
            if text:
                result.append(TranscriptSegment(
                    start=round(scene_start, 2),
                    end=round(current_words[-1].end, 2),
                    text=text,
                    words=current_words
                ))
        
        return result if result else [segment]
    
    def transcribe_with_summary(
        self,
        audio_path: str,
        language: str = "th",
        initial_prompt: Optional[str] = None
    ) -> dict:
        """
        Transcribe and return comprehensive result
        
        Returns:
            Dict with segments, full_text, duration, and stats
        """
        segments = self.transcribe(audio_path, language, initial_prompt=initial_prompt)
        
        full_text = " ".join([s.text for s in segments])
        total_duration = segments[-1].end if segments else 0
        
        return {
            "segments": segments,
            "full_text": full_text,
            "total_duration": total_duration,
            "num_segments": len(segments),
            "language": language,
            "model": self.model_size
        }
    
    @staticmethod
    def correct_with_llm(
        segments: list[TranscriptSegment],
        reference_script: str = "",
        api_key: str = "",
        provider: str = "deepseek",
    ) -> list[TranscriptSegment]:
        """
        Use LLM (DeepSeek) to correct Thai spelling errors in transcription.
        
        Args:
            segments: Raw segments from Whisper
            reference_script: Original script text for context
            api_key: API key for LLM provider
            provider: LLM provider name
            
        Returns:
            Corrected list of TranscriptSegment
        """
        if not segments or not api_key:
            return segments
        
        try:
            from .llm_router import LLMRouter
        except ImportError:
            logger.warning("LLM router not available, skipping correction")
            return segments
        
        # Build transcript text for correction
        transcript_data = []
        for seg in segments:
            transcript_data.append({
                "id": segments.index(seg),
                "text": seg.text,
                "start": seg.start,
                "end": seg.end
            })
        
        system_prompt = (
            "คุณเป็นผู้ตรวจทานภาษาไทยมืออาชีพ ให้แก้ไขคำที่สะกดผิดในบทถอดเสียง\n"
            "กฎ:\n"
            "- แก้เฉพาะคำที่สะกดผิดให้ถูกต้อง\n"
            "- ห้ามเพิ่มหรือลบคำ เพียงแก้การสะกดเท่านั้น\n"
            "- ห้ามเปลี่ยนความหมายหรือโครงสร้างประโยค\n"
            "- คืนผลลัพธ์เป็น JSON array เหมือนรูปแบบ input\n"
            "- ถ้าไม่มีคำผิด ให้คืนข้อมูลเดิมตามเดิม"
        )
        
        reference_context = ""
        if reference_script:
            reference_context = f"\n\nบทพูดต้นฉบับ (ใช้อ้างอิง):\n{reference_script}\n\n"
        
        user_message = (
            f"{reference_context}"
            f"บทถอดเสียงที่ต้องตรวจทาน:\n"
            f"```json\n{json.dumps(transcript_data, ensure_ascii=False, indent=2)}\n```\n\n"
            f"ให้คืนเฉพาะ JSON array ที่แก้แล้ว ไม่ต้องอธิบาย"
        )
        
        try:
            router = LLMRouter()
            response = router.chat(
                messages=[{"role": "user", "content": user_message}],
                provider=provider,
                system_prompt=system_prompt,
                temperature=0.1,  # Low creativity for accuracy
                max_tokens=4096,
            )
            router.close()
            
            # Parse JSON response
            content = response.content.strip()
            # Extract JSON from markdown code block if present
            json_match = re.search(r'```(?:json)?\s*\n(.+?)\n```', content, re.DOTALL)
            if json_match:
                content = json_match.group(1)
            
            corrected = json.loads(content)
            
            # Apply corrections back to segments
            for item in corrected:
                idx = item.get("id", -1)
                if 0 <= idx < len(segments):
                    segments[idx].text = item.get("text", segments[idx].text)
            
            logger.info(f"LLM correction applied to {len(corrected)} segments")
            
        except Exception as e:
            logger.error(f"LLM correction failed: {e}")
            # Return uncorrected segments on failure
        
        return segments


# Convenience function
def transcribe_audio(
    audio_path: str,
    language: str = "th",
    model_size: str = "base"
) -> list[TranscriptSegment]:
    """
    Quick function to transcribe audio
    
    Args:
        audio_path: Path to audio file
        language: Language code (th, en)
        model_size: Whisper model size
        
    Returns:
        List of TranscriptSegment objects
    """
    transcriber = AudioTranscriber(model_size=model_size)
    return transcriber.transcribe(audio_path, language)
