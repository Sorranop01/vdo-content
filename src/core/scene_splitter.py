"""
Scene Splitter - แบ่งบทพากย์เป็นฉากๆ ตาม timing
"""

import re
from typing import Optional
from .models import Scene


class SceneSplitter:
    """Split narration script into scenes based on duration limits"""
    
    # Speaking rates
    # Thai: ~10 characters per second for narration (natural pace)
    # English: ~2.5 words per second (~150 WPM)
    CHARS_PER_SECOND_TH = 10.0  # Thai characters per second (natural narration)
    WORDS_PER_SECOND_EN = 2.5   # English words per second
    
    # Default max duration per scene (Veo 3 limit)
    DEFAULT_MAX_DURATION = 8.0
    
    def __init__(
        self, 
        max_duration: float = DEFAULT_MAX_DURATION,
        language: str = "th"
    ):
        self.max_duration = max_duration
        self.language = language
    
    def calculate_duration(self, text: str) -> float:
        """Calculate speaking duration from text"""
        if self.language == "th":
            # For Thai: count characters (excluding spaces)
            char_count = len(text.replace(" ", ""))
            return round(char_count / self.CHARS_PER_SECOND_TH, 1)
        else:
            # For English: count words
            word_count = len(text.split())
            return round(word_count / self.WORDS_PER_SECOND_EN, 1)
    
    def calculate_max_chars(self) -> int:
        """Calculate max characters for max_duration (Thai)"""
        return int(self.max_duration * self.CHARS_PER_SECOND_TH)
    
    def calculate_max_words(self) -> int:
        """Calculate max words for max_duration (English)"""
        return int(self.max_duration * self.WORDS_PER_SECOND_EN)
    
    def split_into_sentences(self, text: str) -> list[str]:
        """Split text into sentences - optimized for Thai
        
        Uses multiple splitting strategies:
        1. Newlines (common in Thai scripts)
        2. Sentence-ending punctuation (. ! ?)
        3. Thai clause boundaries (particles, conjunctions)
        """
        # Clean up the text first
        text = text.strip()
        
        # Split on newlines first (common in Thai scripts)
        lines = text.split('\n')
        
        sentences = []
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Split on Thai/English sentence endings
            parts = re.split(r'[.!?।॥]+\s*', line)
            
            for part in parts:
                part = part.strip()
                if not part:
                    continue
                
                # If the part is short enough, keep it as-is
                duration = self.calculate_duration(part)
                if duration <= self.max_duration:
                    sentences.append(part)
                else:
                    # Too long — split on Thai clause boundaries
                    # Look for natural break points:
                    # - Thai particles: ครับ, ค่ะ, นะ, เลย, ด้วย
                    # - Conjunctions: แต่, แล้ว, และ, หรือ, เพราะ, ถ้า, จึง, ดังนั้น
                    # - Transition markers with spaces
                    clause_parts = re.split(
                        r'(?<=ครับ)\s*'
                        r'|(?<=ค่ะ)\s*'
                        r'|(?<=นะคะ)\s*'
                        r'|(?<=นะครับ)\s*'
                        r'|\s+(?=แต่)'
                        r'|\s+(?=แล้ว)'
                        r'|\s+(?=และ)'
                        r'|\s+(?=หรือ)'
                        r'|\s+(?=เพราะ)'
                        r'|\s+(?=ถ้า)'
                        r'|\s+(?=จึง)'
                        r'|\s+(?=ดังนั้น)'
                        r'|\s+(?=โดย)'
                        r'|\s+(?=ซึ่ง)',
                        part
                    )
                    
                    # Merge small clauses to avoid too-short scenes
                    buffer = ""
                    for clause in clause_parts:
                        clause = clause.strip()
                        if not clause:
                            continue
                        test = f"{buffer} {clause}".strip() if buffer else clause
                        if self.calculate_duration(test) <= self.max_duration:
                            buffer = test
                        else:
                            if buffer:
                                sentences.append(buffer)
                            buffer = clause
                    if buffer:
                        sentences.append(buffer)
        
        return sentences
    
    def split_script(
        self, 
        script: str,
        default_emotion: str = "neutral",
        default_style: str = "cinematic"
    ) -> list[Scene]:
        """
        Split script into scenes, each ≤ max_duration seconds
        
        Args:
            script: Full narration script
            default_emotion: Default emotion for scenes
            default_style: Default visual style
            
        Returns:
            List of Scene objects
        """
        sentences = self.split_into_sentences(script)
        scenes: list[Scene] = []
        
        current_text = ""
        scene_order = 1
        
        for sentence in sentences:
            # Calculate duration if we add this sentence
            test_text = f"{current_text} {sentence}".strip() if current_text else sentence
            test_duration = self.calculate_duration(test_text)
            
            # If adding this sentence exceeds max, create new scene
            if test_duration > self.max_duration and current_text:
                # Save current scene
                scene = Scene(
                    order=scene_order,
                    narration_text=current_text.strip(),
                    emotion=default_emotion,
                    visual_style=default_style
                )
                # Recalculate with proper method
                scene.word_count = len(current_text.split())
                scene.estimated_duration = self.calculate_duration(current_text.strip())
                scenes.append(scene)
                scene_order += 1
                
                # Start new scene
                current_text = sentence
            else:
                # Add to current scene
                if current_text:
                    current_text += " " + sentence
                else:
                    current_text = sentence
        
        # Don't forget the last scene
        if current_text.strip():
            scene = Scene(
                order=scene_order,
                narration_text=current_text.strip(),
                emotion=default_emotion,
                visual_style=default_style
            )
            scene.word_count = len(current_text.split())
            scene.estimated_duration = self.calculate_duration(current_text.strip())
            scenes.append(scene)
        
        return scenes
    
    def merge_scenes(self, scene1: Scene, scene2: Scene) -> Optional[Scene]:
        """
        Merge two consecutive scenes if combined duration ≤ max
        
        Returns merged scene or None if not possible
        """
        combined_text = f"{scene1.narration_text} {scene2.narration_text}"
        combined_duration = self.calculate_duration(combined_text)
        
        if combined_duration <= self.max_duration:
            return Scene(
                order=scene1.order,
                narration_text=combined_text,
                emotion=scene1.emotion,
                visual_style=scene1.visual_style,
                veo_prompt=scene1.veo_prompt,  # Might need regeneration
                notes=f"Merged from scenes {scene1.scene_id} and {scene2.scene_id}"
            )
        return None
    
    def split_scene(self, scene: Scene) -> list[Scene]:
        """
        Split a scene that's too long into smaller scenes
        """
        if scene.estimated_duration <= self.max_duration:
            return [scene]
        
        # Re-split just this scene's text
        return self.split_script(
            scene.narration_text,
            scene.emotion,
            scene.visual_style
        )
    
    def reorder_scenes(self, scenes: list[Scene]) -> list[Scene]:
        """Reorder scene.order after merging/splitting"""
        for i, scene in enumerate(scenes, 1):
            scene.order = i
        return scenes
    
    def get_stats(self, scenes: list[Scene]) -> dict:
        """Get statistics about scenes"""
        if not scenes:
            return {
                "total_scenes": 0,
                "total_duration": 0,
                "avg_duration": 0,
                "min_duration": 0,
                "max_duration": 0,
                "total_words": 0
            }
        
        durations = [s.estimated_duration for s in scenes]
        words = [s.word_count for s in scenes]
        
        return {
            "total_scenes": len(scenes),
            "total_duration": sum(durations),
            "avg_duration": round(sum(durations) / len(durations), 1),
            "min_duration": min(durations),
            "max_duration": max(durations),
            "total_words": sum(words)
        }


# Convenience function
def split_script(
    script: str, 
    max_duration: float = 8.0,
    language: str = "th"
) -> list[Scene]:
    """Quick function to split script into scenes"""
    splitter = SceneSplitter(max_duration=max_duration, language=language)
    return splitter.split_script(script)
