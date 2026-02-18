"""
Cloud Transcriber - Groq Whisper API
VDO Content V2

Uses Groq's cloud-hosted Whisper models for speech-to-text.
Zero local RAM usage — all processing happens on Groq's servers.

Free tier: 2,000 requests/day at https://console.groq.com
"""

import os
import logging
import httpx
from typing import Optional
from dataclasses import dataclass

from .transcriber import TranscriptSegment, WordInfo

logger = logging.getLogger("vdo_content.cloud_transcriber")

# Groq Whisper models
GROQ_WHISPER_MODELS = {
    "whisper-large-v3": {
        "name": "Whisper Large V3",
        "desc": "🎯 แม่นที่สุดสำหรับภาษาไทย (แนะนำ)",
        "cost_per_hour": 0.111,
    },
    "whisper-large-v3-turbo": {
        "name": "Whisper Large V3 Turbo",
        "desc": "⚡ เร็วกว่า แม่นดี เหมาะกับไฟล์ยาว",
        "cost_per_hour": 0.04,
    },
}

DEFAULT_MODEL = "whisper-large-v3"
GROQ_API_URL = "https://api.groq.com/openai/v1/audio/transcriptions"


class CloudTranscriber:
    """
    Cloud-based audio transcriber using Groq's Whisper API.
    
    Zero local RAM usage — all processing happens on Groq's servers.
    
    Usage:
        transcriber = CloudTranscriber()
        result = transcriber.transcribe_with_summary("audio.mp3", language="th")
    """
    
    MAX_SEGMENT_DURATION = 8.0  # Match local transcriber
    
    def __init__(
        self,
        model: str = DEFAULT_MODEL,
        api_key: Optional[str] = None,
    ):
        self.model = model
        self.api_key = api_key or os.getenv("GROQ_API_KEY", "")
        self._client = httpx.Client(timeout=180.0)  # Up to 3 min for large files
    
    @staticmethod
    def is_available() -> bool:
        """Check if Groq API key is configured"""
        return bool(os.getenv("GROQ_API_KEY", ""))
    
    def transcribe(
        self,
        audio_path: str,
        language: str = "th",
        initial_prompt: Optional[str] = None,
    ) -> list[TranscriptSegment]:
        """
        Transcribe audio file using Groq Whisper API.
        
        Args:
            audio_path: Path to audio file
            language: Language code (e.g., "th" for Thai)
            initial_prompt: Optional context prompt
            
        Returns:
            List of TranscriptSegment with timing info
        """
        if not self.api_key:
            raise ValueError(
                "GROQ_API_KEY ยังไม่ได้ตั้งค่า\n\n"
                "สมัครฟรีที่ https://console.groq.com แล้วใส่ใน .env:\n"
                "GROQ_API_KEY=gsk_xxxx"
            )
        
        logger.info(f"Cloud transcribing: {audio_path} (model={self.model}, lang={language})")
        
        # Prepare multipart form data
        headers = {
            "Authorization": f"Bearer {self.api_key}",
        }
        
        # Read audio file
        with open(audio_path, "rb") as f:
            audio_data = f.read()
        
        # Determine filename for content type
        import os.path
        filename = os.path.basename(audio_path)
        
        # Build form data
        form_data = {
            "model": (None, self.model),
            "language": (None, language),
            "response_format": (None, "verbose_json"),
            "timestamp_granularities[]": (None, "word"),
            "timestamp_granularities[]": (None, "segment"),
        }
        
        if initial_prompt:
            form_data["prompt"] = (None, initial_prompt)
        
        # Send request with file
        files = {
            "file": (filename, audio_data),
        }
        
        # Use raw httpx to send both form fields and file
        response = self._client.post(
            GROQ_API_URL,
            headers=headers,
            data={
                "model": self.model,
                "language": language,
                "response_format": "verbose_json",
                "timestamp_granularities[]": ["word", "segment"],
                **({"prompt": initial_prompt} if initial_prompt else {}),
            },
            files={"file": (filename, audio_data)},
        )
        
        if response.status_code == 401:
            raise ValueError("GROQ_API_KEY ไม่ถูกต้อง กรุณาตรวจสอบที่ https://console.groq.com")
        elif response.status_code == 413:
            raise ValueError("ไฟล์เสียงใหญ่เกินไป (Groq รองรับสูงสุด 25MB)")
        elif response.status_code == 429:
            raise ValueError("เกิน rate limit ของ Groq (Free tier: 2000 req/วัน) ลองอีกครั้งในอีก 1 นาที")
        
        response.raise_for_status()
        
        data = response.json()
        logger.info(f"Groq response: duration={data.get('duration', 0):.1f}s, segments={len(data.get('segments', []))}")
        
        # Parse response into TranscriptSegments
        segments = self._parse_groq_response(data)
        
        # Optimize for scenes (≤8s per segment)
        return self._optimize_for_scenes(segments)
    
    def _parse_groq_response(self, data: dict) -> list[TranscriptSegment]:
        """Parse Groq verbose_json response into TranscriptSegments"""
        segments = []
        
        groq_segments = data.get("segments", [])
        groq_words = data.get("words", [])
        
        for seg in groq_segments:
            start = float(seg.get("start", 0))
            end = float(seg.get("end", 0))
            text = seg.get("text", "").strip()
            
            if not text:
                continue
            
            # Find words that belong to this segment (by time overlap)
            seg_words = []
            for w in groq_words:
                w_start = float(w.get("start", 0))
                w_end = float(w.get("end", 0))
                if w_start >= start - 0.05 and w_end <= end + 0.05:
                    seg_words.append(WordInfo(
                        word=w.get("word", ""),
                        start=w_start,
                        end=w_end,
                        probability=0.0,  # Groq doesn't return per-word confidence
                    ))
            
            segments.append(TranscriptSegment(
                start=round(start, 2),
                end=round(end, 2),
                text=text,
                confidence=float(seg.get("avg_logprob", 0)),
                words=seg_words,
            ))
        
        return segments
    
    def _optimize_for_scenes(
        self,
        segments: list[TranscriptSegment]
    ) -> list[TranscriptSegment]:
        """
        Optimize segments for Veo 3 (max 8 seconds each).
        Same logic as local AudioTranscriber.
        """
        if not segments:
            return []
        
        # Collect ALL words with timestamps
        all_words: list[WordInfo] = []
        for seg in segments:
            if seg.words:
                all_words.extend(seg.words)
            else:
                all_words.append(WordInfo(
                    word=seg.text,
                    start=seg.start,
                    end=seg.end
                ))
        
        if not all_words:
            return segments
        
        # Group words into scenes respecting 8s limit
        THAI_BREAK_PARTICLES = ('ครับ', 'ค่ะ', 'นะ', 'เลย', 'ด้วย', 'แล้ว')
        
        optimized = []
        scene_words: list[WordInfo] = []
        scene_start = all_words[0].start
        
        for word in all_words:
            potential_end = word.end
            potential_duration = potential_end - scene_start
            
            if potential_duration <= self.MAX_SEGMENT_DURATION:
                scene_words.append(word)
            else:
                if scene_words:
                    best_split = len(scene_words)
                    search_start = max(0, len(scene_words) - 5)
                    for j in range(len(scene_words) - 1, search_start - 1, -1):
                        w_text = scene_words[j].word.strip()
                        if w_text.endswith(tuple(THAI_BREAK_PARTICLES)) or w_text.endswith((' ', ',', '.', '!', '?')):
                            best_split = j + 1
                            break
                    
                    split_words = scene_words[:best_split]
                    if split_words:
                        text = "".join(w.word for w in split_words).strip()
                        if text:
                            optimized.append(TranscriptSegment(
                                start=round(scene_start, 2),
                                end=round(split_words[-1].end, 2),
                                text=text,
                                words=split_words
                            ))
                    
                    remaining = scene_words[best_split:]
                    scene_words = remaining + [word]
                    scene_start = scene_words[0].start if scene_words else word.start
                else:
                    scene_words = [word]
                    scene_start = word.start
        
        # Remaining words
        if scene_words:
            text = "".join(w.word for w in scene_words).strip()
            if text:
                optimized.append(TranscriptSegment(
                    start=round(scene_start, 2),
                    end=round(scene_words[-1].end, 2),
                    text=text,
                    words=scene_words
                ))
        
        return optimized
    
    def transcribe_with_summary(
        self,
        audio_path: str,
        language: str = "th",
        initial_prompt: Optional[str] = None
    ) -> dict:
        """
        Transcribe and return comprehensive result.
        Same interface as AudioTranscriber.transcribe_with_summary().
        
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
            "model": f"groq/{self.model}"
        }
    
    def close(self):
        """Close HTTP client"""
        self._client.close()
    
    def __enter__(self):
        return self
    
    def __exit__(self, *args):
        self.close()
