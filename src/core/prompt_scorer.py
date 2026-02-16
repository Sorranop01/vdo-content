"""
Prompt Quality Scorer
VDO Content V2 - Week 3

Analyzes and scores Veo 3 prompts for quality and effectiveness.
"""

import re
from typing import Optional
from dataclasses import dataclass, field

from .llm_router import get_router
from .llm_config import ProviderName, DEFAULT_PROVIDER


@dataclass
class PromptScore:
    """Prompt quality score result"""
    total_score: float  # 0-100
    clarity: float  # 0-25
    specificity: float  # 0-25
    veo_compatibility: float  # 0-25
    visual_richness: float  # 0-25
    suggestions: list[str] = field(default_factory=list)
    grade: str = "C"  # A, B, C, D, F


class PromptScorer:
    """
    Analyzes Veo 3 prompts for quality and provides improvement suggestions.
    
    Scoring Criteria:
    - Clarity (0-25): How clear and unambiguous is the description?
    - Specificity (0-25): How specific are the visual details?
    - Veo Compatibility (0-25): Does it follow Veo 3 best practices?
    - Visual Richness (0-25): How visually descriptive is the prompt?
    """
    
    # Keywords that indicate good Veo 3 prompts
    GOOD_KEYWORDS = [
        "cinematic", "4k", "hdr", "high quality", "detailed",
        "camera", "shot", "movement", "lighting", "angle",
        "close-up", "wide shot", "medium shot", "pan", "zoom",
        "natural", "dramatic", "soft", "ambient",
    ]
    
    # Keywords that indicate poor prompts
    BAD_KEYWORDS = [
        "etc", "maybe", "possibly", "something like",
        "whatever", "stuff", "things",
    ]
    
    def __init__(self, use_ai: bool = True, provider: ProviderName = DEFAULT_PROVIDER):
        """
        Initialize scorer
        
        Args:
            use_ai: Use AI for detailed analysis (slower but better)
            provider: LLM provider for AI analysis
        """
        self.use_ai = use_ai
        self.provider = provider
        self._router = get_router() if use_ai else None
    
    def score(self, prompt: str) -> PromptScore:
        """
        Score a Veo 3 prompt
        
        Args:
            prompt: The prompt to analyze
            
        Returns:
            PromptScore with breakdown and suggestions
        """
        # Rule-based scoring (always run)
        clarity = self._score_clarity(prompt)
        specificity = self._score_specificity(prompt)
        veo_compat = self._score_veo_compatibility(prompt)
        visual_richness = self._score_visual_richness(prompt)
        
        total = clarity + specificity + veo_compat + visual_richness
        
        # Generate suggestions
        suggestions = self._generate_suggestions(prompt, clarity, specificity, veo_compat, visual_richness)
        
        # Determine grade
        grade = self._get_grade(total)
        
        return PromptScore(
            total_score=total,
            clarity=clarity,
            specificity=specificity,
            veo_compatibility=veo_compat,
            visual_richness=visual_richness,
            suggestions=suggestions,
            grade=grade
        )
    
    def _score_clarity(self, prompt: str) -> float:
        """Score clarity (0-25)"""
        score = 15.0  # Base score
        
        # Penalize vague words
        for word in self.BAD_KEYWORDS:
            if word in prompt.lower():
                score -= 3
        
        # Reward sentence structure
        if len(prompt.split('.')) >= 2:
            score += 3
        
        # Penalize too short
        if len(prompt) < 50:
            score -= 5
        elif len(prompt) > 100:
            score += 5
        
        return max(0, min(25, score))
    
    def _score_specificity(self, prompt: str) -> float:
        """Score specificity (0-25)"""
        score = 10.0
        
        # Check for specific details
        specific_patterns = [
            r'\d+',  # Numbers
            r'\b(red|blue|green|yellow|gold|silver|white|black)\b',  # Colors
            r'\b(young|old|elderly|teenage)\b',  # Age
            r'\b(tall|short|large|small|tiny|massive)\b',  # Size
        ]
        
        for pattern in specific_patterns:
            if re.search(pattern, prompt, re.I):
                score += 4
        
        return max(0, min(25, score))
    
    def _score_veo_compatibility(self, prompt: str) -> float:
        """Score Veo 3 compatibility (0-25)"""
        score = 10.0
        
        # Check for Veo-friendly keywords
        good_count = sum(1 for kw in self.GOOD_KEYWORDS if kw in prompt.lower())
        score += min(10, good_count * 2)
        
        # Check for camera/movement instructions
        if any(x in prompt.lower() for x in ["camera", "shot", "angle", "pan", "zoom"]):
            score += 5
        
        return max(0, min(25, score))
    
    def _score_visual_richness(self, prompt: str) -> float:
        """Score visual descriptiveness (0-25)"""
        score = 10.0
        
        # Visual descriptors
        visual_words = [
            "lighting", "shadows", "glow", "bright", "dark",
            "vibrant", "muted", "saturated", "contrast",
            "texture", "smooth", "rough", "shiny", "matte"
        ]
        
        word_count = sum(1 for w in visual_words if w in prompt.lower())
        score += min(10, word_count * 3)
        
        # Longer prompts generally have more visual detail
        if len(prompt) > 150:
            score += 5
        
        return max(0, min(25, score))
    
    def _generate_suggestions(
        self, 
        prompt: str, 
        clarity: float, 
        specificity: float,
        veo_compat: float,
        visual_richness: float
    ) -> list[str]:
        """Generate improvement suggestions"""
        suggestions = []
        
        if clarity < 15:
            suggestions.append("❌ Make the description clearer - avoid vague words like 'maybe', 'something'")
        
        if specificity < 15:
            suggestions.append("🎯 Add specific details: colors, sizes, numbers, ages")
        
        if veo_compat < 15:
            suggestions.append("🎬 Add camera instructions: 'cinematic wide shot', 'slow pan', 'close-up'")
        
        if visual_richness < 15:
            suggestions.append("🎨 Describe lighting and atmosphere: 'warm golden light', 'soft shadows'")
        
        if len(prompt) < 80:
            suggestions.append("📝 Prompt is too short - aim for 100-200 characters")
        
        return suggestions
    
    def _get_grade(self, total: float) -> str:
        """Convert score to letter grade"""
        if total >= 85:
            return "A"
        elif total >= 70:
            return "B"
        elif total >= 55:
            return "C"
        elif total >= 40:
            return "D"
        return "F"
    
    def suggest_improvements_ai(self, prompt: str) -> list[str]:
        """
        Use AI to suggest prompt improvements
        
        Args:
            prompt: The prompt to improve
            
        Returns:
            List of AI-generated suggestions
        """
        if not self._router:
            return self._generate_suggestions(prompt, 0, 0, 0, 0)
        
        system_prompt = """You are a Veo 3 prompt expert. Analyze the given video prompt and provide 3 specific improvements.

Format each suggestion as a single line starting with an emoji.
Focus on: visual details, camera work, lighting, and motion.
Be concise and actionable."""
        
        try:
            response = self._router.chat(
                messages=[{"role": "user", "content": f"Improve this Veo 3 prompt:\n\n{prompt}"}],
                provider=self.provider,
                system_prompt=system_prompt,
                temperature=0.3,  # Lower for consistent, reliable suggestions
                max_tokens=300
            )
            
            suggestions = [line.strip() for line in response.content.split('\n') if line.strip()]
            return suggestions[:3]
        except Exception as e:
            import logging
            logging.getLogger("vdo_content.prompt_scorer").debug(f"AI suggestion failed: {e}")
            return self._generate_suggestions(prompt, 0, 0, 0, 0)


# Convenience functions
def score_prompt(prompt: str) -> PromptScore:
    """Quick function to score a prompt"""
    scorer = PromptScorer(use_ai=False)
    return scorer.score(prompt)


def get_score_emoji(score: float) -> str:
    """Get emoji for score"""
    if score >= 80:
        return "🟢"
    elif score >= 60:
        return "🟡"
    elif score >= 40:
        return "🟠"
    return "🔴"
