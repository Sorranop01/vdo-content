"""
Scene Duration Calibration
Calculates actual speaking rate from TTS audio to improve scene splitting accuracy.
"""

import logging
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Optional

from .models import Scene

logger = logging.getLogger("vdo_content.calibration")

# Default Thai speaking rate (chars per second)
DEFAULT_CHARS_PER_SECOND_TH = 10.0
DEFAULT_WORDS_PER_SECOND_EN = 2.5

CALIBRATION_CACHE_PATH = Path("data/calibration_profiles.json")


class CalibrationProfile:
    """Calibrated speaking rate profile derived from actual TTS audio."""

    def __init__(
        self,
        chars_per_second: float = DEFAULT_CHARS_PER_SECOND_TH,
        words_per_second: float = DEFAULT_WORDS_PER_SECOND_EN,
        voice_type: str = "unknown",
        speaking_rate: float = 1.0,
        language: str = "th",
        sample_count: int = 0,
        calibrated_at: Optional[str] = None,
    ):
        self.chars_per_second = chars_per_second
        self.words_per_second = words_per_second
        self.voice_type = voice_type
        self.speaking_rate = speaking_rate
        self.language = language
        self.sample_count = sample_count
        self.calibrated_at = calibrated_at or datetime.now().isoformat()

    def to_dict(self) -> dict:
        return {
            "chars_per_second": self.chars_per_second,
            "words_per_second": self.words_per_second,
            "voice_type": self.voice_type,
            "speaking_rate": self.speaking_rate,
            "language": self.language,
            "sample_count": self.sample_count,
            "calibrated_at": self.calibrated_at,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "CalibrationProfile":
        return cls(**data)

    @classmethod
    def default(cls, language: str = "th") -> "CalibrationProfile":
        """Return default (uncalibrated) profile."""
        return cls(language=language)

    def summary(self) -> str:
        if self.language == "th":
            default = DEFAULT_CHARS_PER_SECOND_TH
            return (
                f"{self.chars_per_second:.1f} chars/sec "
                f"({'faster' if self.chars_per_second > default else 'slower'} than default {default})"
            )
        else:
            default = DEFAULT_WORDS_PER_SECOND_EN
            return (
                f"{self.words_per_second:.1f} words/sec "
                f"({'faster' if self.words_per_second > default else 'slower'} than default {default})"
            )


def calibrate_from_audio(
    audio_path: str,
    scenes: list,  # list[Scene]
    language: str = "th",
) -> CalibrationProfile:
    """
    Calculate actual speaking rate from TTS audio + scene text.

    Compares actual audio duration (from pydub) against scene text length
    to compute chars/second or words/second.

    Args:
        audio_path: Path to full combined TTS audio file
        scenes: List of Scene objects with narration_text and timing info
        language: Language code (th / en)

    Returns:
        CalibrationProfile with calibrated chars_per_second / words_per_second
    """
    try:
        from pydub import AudioSegment
    except ImportError:
        logger.warning("pydub not installed -- cannot calibrate. Using default profile.")
        return CalibrationProfile.default(language)

    if not os.path.exists(audio_path):
        logger.warning(f"Audio file not found: {audio_path}")
        return CalibrationProfile.default(language)

    # Scenes need real timing data (start_time / end_time from Whisper or per-scene TTS)
    scenes_with_timing = [
        s for s in scenes
        if hasattr(s, "start_time") and hasattr(s, "end_time")
        and s.end_time > s.start_time
    ]

    if not scenes_with_timing:
        logger.warning("No scenes with timing data available for calibration.")
        return CalibrationProfile.default(language)

    ratios = []
    for scene in scenes_with_timing:
        duration = scene.end_time - scene.start_time
        if duration <= 0:
            continue

        text = scene.narration_text.strip()
        if not text:
            continue

        if language == "th":
            # Count Thai characters (excluding spaces/punctuation)
            char_count = len(text.replace(" ", "").replace("\n", ""))
            if char_count > 0:
                ratios.append(char_count / duration)
        else:
            word_count = len(text.split())
            if word_count > 0:
                ratios.append(word_count / duration)

    if not ratios:
        logger.warning("Could not compute any ratios from scene timing data.")
        return CalibrationProfile.default(language)

    # Average ratio (trim outliers: ignore top/bottom 10%)
    ratios.sort()
    trim = max(1, len(ratios) // 10)
    trimmed = ratios[trim:-trim] if len(ratios) > trim * 2 else ratios
    avg_ratio = sum(trimmed) / len(trimmed)

    # Clamp to reasonable bounds
    if language == "th":
        avg_ratio = max(6.0, min(18.0, avg_ratio))  # real Thai TTS range
        profile = CalibrationProfile(
            chars_per_second=round(avg_ratio, 2),
            language=language,
            sample_count=len(ratios),
        )
        logger.info(
            f"Calibration complete: {avg_ratio:.2f} chars/sec "
            f"(default: {DEFAULT_CHARS_PER_SECOND_TH}, from {len(ratios)} scenes)"
        )
    else:
        avg_ratio = max(1.5, min(5.0, avg_ratio))
        profile = CalibrationProfile(
            words_per_second=round(avg_ratio, 2),
            language=language,
            sample_count=len(ratios),
        )
        logger.info(
            f"Calibration complete: {avg_ratio:.2f} words/sec "
            f"(default: {DEFAULT_WORDS_PER_SECOND_EN}, from {len(ratios)} scenes)"
        )

    return profile


def save_calibration_profile(profile: CalibrationProfile, key: str = "default") -> None:
    """Save calibration profile to disk for reuse."""
    CALIBRATION_CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)

    existing = {}
    if CALIBRATION_CACHE_PATH.exists():
        try:
            existing = json.loads(CALIBRATION_CACHE_PATH.read_text(encoding="utf-8"))
        except Exception:
            pass

    existing[key] = profile.to_dict()
    CALIBRATION_CACHE_PATH.write_text(
        json.dumps(existing, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    logger.info(f"Saved calibration profile '{key}' to {CALIBRATION_CACHE_PATH}")


def load_calibration_profile(key: str = "default", language: str = "th") -> CalibrationProfile:
    """Load calibration profile from disk, or return default if not found."""
    if not CALIBRATION_CACHE_PATH.exists():
        return CalibrationProfile.default(language)

    try:
        data = json.loads(CALIBRATION_CACHE_PATH.read_text(encoding="utf-8"))
        if key in data:
            return CalibrationProfile.from_dict(data[key])
    except Exception as e:
        logger.warning(f"Could not load calibration profile: {e}")

    return CalibrationProfile.default(language)
