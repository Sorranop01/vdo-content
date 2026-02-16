
import logging
import os
from pathlib import Path
from dotenv import load_dotenv
import tempfile
import requests
import base64

logger = logging.getLogger("vdo_content.aistudio_voice")

class AIStudioVoiceGenerator:
    """
    Dual-mode voice generator supporting:
    1. Neural2 mode (API key) - Simple, decent quality
    2. Gemini TTS mode (service account) - AI Studio quality
    
    Auto-detects authentication method and uses best available option.
    """
    
    def __init__(self, api_key: str = None):
        # Force reload env
        load_dotenv(override=True)
        
        self.api_key = api_key or os.getenv("GOOGLE_TTS_API_KEY")
        self.service_account_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
        self.gcp_project_id = os.getenv("GCP_PROJECT_ID")
        
        # Auto-detect mode
        self.mode = self._detect_auth_mode()
        
        # Initialize appropriate client
        if self.mode == "gemini-tts":
            self._init_gemini_client()
        elif self.mode == "neural2":
            self._init_rest_client()
        else:
            raise ValueError("No valid authentication found. Please set GOOGLE_TTS_API_KEY or GOOGLE_APPLICATION_CREDENTIALS")
    
    def _detect_auth_mode(self) -> str:
        """Detect which authentication method is available"""
        # Priority 1: Service account (for Gemini TTS)
        if self.service_account_path and Path(self.service_account_path).exists():
            try:
                from google.cloud import texttospeech
                return "gemini-tts"
            except ImportError:
                logger.warning("google-cloud-texttospeech not installed. Run: pip install google-cloud-texttospeech")
        
        # Priority 2: API key (for Neural2)
        if self.api_key:
            return "neural2"
        
        return "none"
    
    def _init_gemini_client(self):
        """Initialize Cloud TTS client for Gemini TTS"""
        from google.cloud import texttospeech
        self.client = texttospeech.TextToSpeechClient()
        logger.info("Mode: Gemini TTS (AI Studio quality)")
    
    def _init_rest_client(self):
        """Initialize REST API client for Neural2"""
        self.base_url = "https://texttospeech.googleapis.com/v1beta1"
        logger.info("Mode: Neural2 (Standard quality)")
    
    def get_mode_info(self) -> dict:
        """Get current mode information"""
        if self.mode == "gemini-tts":
            return {
                "mode": "Gemini TTS",
                "quality": "AI Studio (Highest)",
                "auth": "Service Account",
                "models": ["gemini-2.5-flash-tts", "gemini-2.5-pro-tts"],
                "voices": ["Zephyr", "Orbit", "Leda", "Kore", "Puck", "Charon", "Aoede", "Fenrir"]
            }
        else:
            return {
                "mode": "Neural2",
                "quality": "Standard",
                "auth": "API Key",
                "models": ["Neural2"],
                "voices": ["th-TH-Neural2-C (Thai)", "en-US-Neural2-A (English)"]
            }
    
    def generate_speech(
        self, 
        text: str, 
        output_path: str = None,
        voice: str = None,
        language_code: str = "th-TH",
        model: str = None
    ) -> str:
        """
        Generate speech using best available method
        
        Args:
            text: Text to convert to speech
            output_path: Path to save the audio file (optional)
            voice: Voice name (auto-selected if None)
            language_code: Language code (th-TH, en-US, etc.)
            model: TTS model (only for Gemini TTS mode)
        
        Returns:
            Path to the generated audio file
        """
        
        if self.mode == "gemini-tts":
            return self._generate_gemini_tts(text, output_path, voice, language_code, model)
        else:
            return self._generate_neural2(text, output_path, voice, language_code)
    
    def _generate_gemini_tts(
        self,
        text: str,
        output_path: str = None,
        voice: str = None,
        language_code: str = "th-TH",
        model: str = None
    ) -> str:
        """Generate speech using Gemini TTS (Cloud client)"""
        from google.cloud import texttospeech
        
        # Default model and voice
        model = model or "gemini-2.5-flash-tts"
        
        # Auto-select voice based on language if not specified
        if not voice:
            voice = "Zephyr" if language_code.startswith("en") else "Aoede"
        
        try:
            # Single-shot synthesis (simpler than streaming for now)
            synthesis_input = texttospeech.SynthesisInput(text=text)
            
            voice_params = texttospeech.VoiceSelectionParams(
                name=voice,
                language_code=language_code,
                model_name=model
            )
            
            audio_config = texttospeech.AudioConfig(
                audio_encoding=texttospeech.AudioEncoding.MP3
            )
            
            response = self.client.synthesize_speech(
                input=synthesis_input,
                voice=voice_params,
                audio_config=audio_config
            )
            
            # Save audio
            if output_path:
                p = Path(output_path)
            else:
                tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3")
                p = Path(tmp.name)
            
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_bytes(response.audio_content)
            
            return str(p)
            
        except Exception as e:
            import traceback
            raise RuntimeError(
                f"Gemini TTS generation failed: {e}\n"
                f"Traceback:\n{traceback.format_exc()}\n\n"
                f"Tips:\n"
                f"- Verify service account has Text-to-Speech API access\n"
                f"- Check model: {model}\n"
                f"- Check voice: {voice}"
            )
    
    def _generate_neural2(
        self,
        text: str,
        output_path: str = None,
        voice: str = None,
        language_code: str = "th-TH"
    ) -> str:
        """Generate speech using Neural2 (REST API)"""
        
        # Auto-select voice if not specified
        if not voice:
            voice = "th-TH-Neural2-C" if language_code == "th-TH" else "en-US-Neural2-A"
        
        try:
            url = f"{self.base_url}/text:synthesize"
            
            headers = {
                "X-Goog-Api-Key": self.api_key,
                "Content-Type": "application/json; charset=utf-8"
            }
            
            payload = {
                "input": {"text": text},
                "voice": {
                    "languageCode": language_code,
                    "name": voice
                },
                "audioConfig": {
                    "audioEncoding": "MP3",
                    "speakingRate": 1.0,
                    "pitch": 0.0
                }
            }
            
            response = requests.post(url, json=payload, headers=headers, timeout=60)
            
            if response.status_code != 200:
                raise RuntimeError(
                    f"Neural2 TTS Error ({response.status_code}): {response.text}\n\n"
                    f"Tips:\n"
                    f"- API Key: {self.api_key[:10]}...\n"
                    f"- Voice: {voice}\n"
                    f"- Language: {language_code}"
                )
            
            result = response.json()
            audio_content = result.get("audioContent")
            
            if not audio_content:
                raise ValueError(f"No audio returned. Response: {result}")
            
            audio_bytes = base64.b64decode(audio_content)
            
            if output_path:
                p = Path(output_path)
            else:
                tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3")
                p = Path(tmp.name)
            
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_bytes(audio_bytes)
            
            return str(p)
            
        except requests.exceptions.RequestException as e:
            raise RuntimeError(f"Network error: {e}")
        except Exception as e:
            import traceback
            raise RuntimeError(
                f"Neural2 TTS failed: {e}\n"
                f"Traceback:\n{traceback.format_exc()}"
            )

    def generate_per_scene_speech(
        self,
        scene_texts: list[str],
        output_path: str,
        silence_gap_ms: int = 300,
        voice: str = None,
        language_code: str = "th-TH",
        model: str = None
    ) -> dict:
        """Generate TTS per scene and combine with precise timing.
        
        Instead of generating one big audio file, this generates each
        scene's audio separately, then concatenates with controlled silence
        gaps. This gives exact per-scene timing.
        
        Args:
            scene_texts: List of text strings, one per scene
            output_path: Path for the final combined audio
            silence_gap_ms: Milliseconds of silence between scenes
            voice: TTS voice name
            language_code: Language code
            model: TTS model (Gemini mode only)
            
        Returns:
            Dict with:
                - path: str (combined audio file path)
                - segments: list of {order, start_time, end_time, duration}
                - total_duration: float (seconds)
        """
        try:
            from pydub import AudioSegment as PydubAudio
        except ImportError:
            raise RuntimeError("pydub is required for per-scene TTS. Install: pip install pydub")
        
        if not scene_texts:
            raise ValueError("No scene texts provided")
        
        scene_audios = []
        temp_files = []
        
        try:
            # 1. Generate TTS for each scene individually
            for i, text in enumerate(scene_texts):
                tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3")
                temp_path = tmp.name
                tmp.close()
                temp_files.append(temp_path)
                
                self.generate_speech(
                    text=text.strip(),
                    output_path=temp_path,
                    voice=voice,
                    language_code=language_code,
                    model=model
                )
                
                audio_seg = PydubAudio.from_file(temp_path)
                scene_audios.append(audio_seg)
                logger.info(f"Scene {i+1}: {len(audio_seg)}ms")
            
            # 2. Combine with silence gaps
            silence = PydubAudio.silent(duration=silence_gap_ms)
            combined = PydubAudio.empty()
            segments = []
            current_ms = 0
            
            for i, audio in enumerate(scene_audios):
                start_ms = current_ms
                combined += audio
                current_ms += len(audio)
                end_ms = current_ms
                
                segments.append({
                    "order": i + 1,
                    "start_time": round(start_ms / 1000.0, 3),
                    "end_time": round(end_ms / 1000.0, 3),
                    "duration": round(len(audio) / 1000.0, 3)
                })
                
                # Add silence gap (except after last scene)
                if i < len(scene_audios) - 1:
                    combined += silence
                    current_ms += silence_gap_ms
            
            # 3. Export combined audio
            out_path = Path(output_path)
            out_path.parent.mkdir(parents=True, exist_ok=True)
            combined.export(str(out_path), format="mp3")
            
            total_duration = round(len(combined) / 1000.0, 3)
            
            logger.info(
                f"Per-scene TTS complete: {len(segments)} scenes, "
                f"{total_duration:.1f}s total"
            )
            
            return {
                "path": str(out_path),
                "segments": segments,
                "total_duration": total_duration
            }
            
        finally:
            # Clean up temp files
            for tmp in temp_files:
                try:
                    os.remove(tmp)
                except OSError:
                    pass

