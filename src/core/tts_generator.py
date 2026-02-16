"""
Google Cloud Text-to-Speech Generator
Uses Google's TTS API to generate Thai audio from text
"""

import os
import requests
import base64
import tempfile
from pathlib import Path
from typing import Optional


class GoogleTTSGenerator:
    """Generate speech from text using Google Cloud TTS API"""
    
    # Thai voice options
    THAI_VOICES = {
        "female_standard": {"name": "th-TH-Standard-A", "gender": "FEMALE"},
        "male_standard": {"name": "th-TH-Standard-A", "gender": "MALE"},
        "female_wavenet": {"name": "th-TH-Neural2-C", "gender": "FEMALE"},
        "male_wavenet": {"name": "th-TH-Neural2-D", "gender": "MALE"},
    }
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize with API key from env or parameter"""
        # Force reload env to ensure we get the latest key
        if not api_key:
            from dotenv import load_dotenv
            load_dotenv(override=True)
            self.api_key = os.getenv("GOOGLE_TTS_API_KEY")
        else:
            self.api_key = api_key

        if not self.api_key:
            raise ValueError("Google TTS API key not found. Set GOOGLE_TTS_API_KEY environment variable.")
        
        self.base_url = "https://texttospeech.googleapis.com/v1/text:synthesize"
    
    def generate_speech(
        self,
        text: str,
        voice_type: str = "female_wavenet",
        speaking_rate: float = 1.0,
        pitch: float = 0.0,
        output_path: Optional[str] = None
    ) -> str:
        """
        Generate speech from text
        ...
        """
        if not text.strip():
            raise ValueError("Text cannot be empty")
        
        # Get voice configuration
        voice_config = self.THAI_VOICES.get(voice_type, self.THAI_VOICES["female_wavenet"])
        
        # Prepare request payload
        payload = {
            "input": {
                "text": text
            },
            "voice": {
                "languageCode": "th-TH",
                "name": voice_config["name"],
                "ssmlGender": voice_config["gender"]
            },
            "audioConfig": {
                "audioEncoding": "MP3",
                "speakingRate": max(0.25, min(4.0, speaking_rate)),
                "pitch": max(-20.0, min(20.0, pitch)),
                "sampleRateHertz": 24000
            }
        }
        
        # Make API request
        # Use header for security instead of URL parameter
        headers = {
            "X-Goog-Api-Key": self.api_key,
            "Content-Type": "application/json; charset=utf-8"
        }
        
        try:
            response = requests.post(self.base_url, json=payload, headers=headers, timeout=60)
            
            # Check for error and raise with DETAILED message
            if response.status_code != 200:
                raise RuntimeError(f"Google TTS Error ({response.status_code}): {response.text}")
                
            result = response.json()
            audio_content = result.get("audioContent")
            
            if not audio_content:
                raise ValueError("No audio content in response")
            
            # Decode base64 audio
            audio_bytes = base64.b64decode(audio_content)
            
            # Save to file
            if output_path:
                output_file = Path(output_path)
            else:
                # Create temp file
                tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3")
                output_file = Path(tmp.name)
            
            output_file.parent.mkdir(parents=True, exist_ok=True)
            output_file.write_bytes(audio_bytes)
            
            return str(output_file)
            
        except requests.exceptions.RequestException as e:
            # Mask API key in error message just in case
            error_msg = str(e).replace(self.api_key, "HIDDEN_API_KEY")
            raise RuntimeError(f"TTS API request failed: {error_msg}")
    
    def list_voices(self) -> list:
        """List available Thai voices from API"""
        url = f"https://texttospeech.googleapis.com/v1/voices?key={self.api_key}&languageCode=th-TH"
        
        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            
            result = response.json()
            return result.get("voices", [])
            
        except requests.exceptions.RequestException as e:
            import logging
            logging.getLogger("vdo_content.tts_generator").warning(f"Failed to list voices: {e}")
            return list(self.THAI_VOICES.values())
    
    def is_available(self) -> bool:
        """Check if TTS API is available and configured"""
        if not self.api_key:
            return False
        
        try:
            # Try a minimal request to verify API key
            url = f"https://texttospeech.googleapis.com/v1/voices?key={self.api_key}&languageCode=th-TH"
            response = requests.get(url, timeout=10)
            return response.status_code == 200
        except Exception as e:
            import logging
            logging.getLogger("vdo_content.tts_generator").debug(f"TTS availability check failed: {e}")
            return False


# Convenience function
def generate_tts_audio(
    text: str,
    voice_type: str = "female_wavenet",
    speaking_rate: float = 1.0,
    api_key: Optional[str] = None
) -> str:
    """
    Quick helper to generate TTS audio
    
    Args:
        text: Thai text to speak
        voice_type: Voice type (female_wavenet, male_wavenet, female_standard, male_standard)
        speaking_rate: Speech speed (0.25-4.0)
        api_key: Optional API key (uses env var if not provided)
        
    Returns:
        Path to generated MP3 file
    """
    generator = GoogleTTSGenerator(api_key=api_key)
    return generator.generate_speech(text, voice_type, speaking_rate)
