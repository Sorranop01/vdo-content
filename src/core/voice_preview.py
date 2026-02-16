"""
Voice Preview - AI Voice Preview Generator
VDO Content V2 - Week 2

Generate quick TTS previews for narration text.
"""

import os
import hashlib
import tempfile
from pathlib import Path
from typing import Optional, Literal
from dataclasses import dataclass


VoiceProvider = Literal["google", "elevenlabs", "edge"]


@dataclass
class VoiceConfig:
    """Voice configuration"""
    voice_id: str
    name: str
    language: str = "th-TH"
    gender: str = "female"
    provider: VoiceProvider = "google"


# Thai voice options
THAI_VOICES = [
    VoiceConfig("th-TH-PremwadeeNeural", "Premwadee (หญิง)", "th-TH", "female", "edge"),
    VoiceConfig("th-TH-NiwatNeural", "Niwat (ชาย)", "th-TH", "male", "edge"),
    VoiceConfig("th-TH-Standard-A", "Google Thai A", "th-TH", "female", "google"),
]

# English voice options
ENGLISH_VOICES = [
    VoiceConfig("en-US-JennyNeural", "Jenny (Female)", "en-US", "female", "edge"),
    VoiceConfig("en-US-GuyNeural", "Guy (Male)", "en-US", "male", "edge"),
]


class VoicePreview:
    """
    Voice preview generator using multiple TTS providers.
    
    Supports:
    - Google Cloud TTS (requires GOOGLE_API_KEY)
    - Microsoft Edge TTS (free, requires edge-tts package)
    """
    
    def __init__(self, cache_dir: Optional[str] = None):
        """
        Initialize voice preview
        
        Args:
            cache_dir: Cache directory for audio files (default: temp dir)
        """
        self.cache_dir = Path(cache_dir) if cache_dir else Path(tempfile.gettempdir()) / "vdo_voice_cache"
        self.cache_dir.mkdir(parents=True, exist_ok=True)
    
    def get_cache_key(self, text: str, voice_id: str) -> str:
        """Generate cache key from text and voice"""
        content = f"{text}:{voice_id}"
        return hashlib.md5(content.encode()).hexdigest()[:16]
    
    def get_cached_audio(self, text: str, voice_id: str) -> Optional[Path]:
        """Check if audio is cached"""
        cache_key = self.get_cache_key(text, voice_id)
        cache_path = self.cache_dir / f"{cache_key}.mp3"
        return cache_path if cache_path.exists() else None
    
    def generate_preview(
        self,
        text: str,
        voice_id: str = "th-TH-PremwadeeNeural",
        provider: VoiceProvider = "edge"
    ) -> Path:
        """
        Generate voice preview for text
        
        Args:
            text: Text to speak (Thai or English)
            voice_id: Voice ID
            provider: TTS provider
            
        Returns:
            Path to audio file
        """
        # Check cache
        cached = self.get_cached_audio(text, voice_id)
        if cached:
            return cached
        
        # Generate new audio
        cache_key = self.get_cache_key(text, voice_id)
        output_path = self.cache_dir / f"{cache_key}.mp3"
        
        if provider == "edge":
            self._generate_edge_tts(text, voice_id, output_path)
        elif provider == "google":
            self._generate_google_tts(text, voice_id, output_path)
        else:
            raise ValueError(f"Unknown provider: {provider}")
        
        return output_path
    
    def _generate_edge_tts(self, text: str, voice_id: str, output_path: Path):
        """Generate using Edge TTS (free)"""
        try:
            import edge_tts
            import asyncio
            
            async def generate():
                communicate = edge_tts.Communicate(text, voice_id)
                await communicate.save(str(output_path))
            
            asyncio.run(generate())
        except ImportError:
            raise RuntimeError("edge-tts not installed. Run: pip install edge-tts")
    
    def _generate_google_tts(self, text: str, voice_id: str, output_path: Path):
        """Generate using Google Cloud TTS"""
        api_key = os.getenv("GOOGLE_TTS_API_KEY") or os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise RuntimeError("GOOGLE_TTS_API_KEY not configured")
        
        import httpx
        
        url = f"https://texttospeech.googleapis.com/v1/text:synthesize?key={api_key}"
        
        # Map voice_id to Google format
        language_code = "th-TH" if "th" in voice_id.lower() else "en-US"
        
        payload = {
            "input": {"text": text},
            "voice": {
                "languageCode": language_code,
                "name": voice_id
            },
            "audioConfig": {
                "audioEncoding": "MP3",
                "speakingRate": 1.0,
                "pitch": 0
            }
        }
        
        response = httpx.post(url, json=payload)
        response.raise_for_status()
        
        import base64
        audio_content = base64.b64decode(response.json()["audioContent"])
        output_path.write_bytes(audio_content)
    
    def list_voices(self, language: str = "th") -> list[VoiceConfig]:
        """Get available voices for language"""
        if language == "th":
            return THAI_VOICES
        elif language == "en":
            return ENGLISH_VOICES
        return THAI_VOICES + ENGLISH_VOICES
    
    def clear_cache(self):
        """Clear all cached audio files"""
        for f in self.cache_dir.glob("*.mp3"):
            f.unlink()


# Convenience functions
def preview_text(text: str, voice_id: str = "th-TH-PremwadeeNeural") -> Path:
    """Quick function to generate preview"""
    preview = VoicePreview()
    return preview.generate_preview(text, voice_id)


def list_thai_voices() -> list[VoiceConfig]:
    """Get available Thai voices"""
    return THAI_VOICES
