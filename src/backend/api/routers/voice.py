"""
Voice API Router
VDO Content V2 - FastAPI

Endpoints for voice preview generation.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
import base64

router = APIRouter(prefix="/api/voice", tags=["Voice"])


class VoicePreviewRequest(BaseModel):
    """Voice preview request"""
    text: str
    voice_id: str = "th-TH-PremwadeeNeural"
    provider: str = "edge"


class VoicePreviewResponse(BaseModel):
    """Voice preview response"""
    success: bool
    audio_url: Optional[str] = None
    audio_base64: Optional[str] = None
    duration: Optional[float] = None
    error: Optional[str] = None


class VoiceInfo(BaseModel):
    """Voice information"""
    voice_id: str
    name: str
    language: str
    gender: str


@router.post("/preview", response_model=VoicePreviewResponse)
async def generate_preview(request: VoicePreviewRequest):
    """Generate voice preview for text"""
    try:
        from core.voice_preview import VoicePreview
        
        preview = VoicePreview()
        audio_path = preview.generate_preview(
            text=request.text,
            voice_id=request.voice_id,
            provider=request.provider
        )
        
        # Read and encode audio
        audio_bytes = audio_path.read_bytes()
        audio_base64 = base64.b64encode(audio_bytes).decode()
        
        return VoicePreviewResponse(
            success=True,
            audio_base64=audio_base64
        )
    except Exception as e:
        return VoicePreviewResponse(
            success=False,
            error=str(e)
        )


@router.get("/voices", response_model=list[VoiceInfo])
async def list_voices(language: str = "all"):
    """List available voices"""
    from core.voice_preview import VoicePreview
    
    preview = VoicePreview()
    voices = preview.list_voices(language)
    
    return [
        VoiceInfo(
            voice_id=v.voice_id,
            name=v.name,
            language=v.language,
            gender=v.gender
        )
        for v in voices
    ]
