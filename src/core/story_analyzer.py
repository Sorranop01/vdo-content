"""
Story Analyzer for VDO Content V2
Analyzes topic and generates story proposal with approval workflow
"""

import os
from typing import Optional
from .models import StoryProposal, STYLE_PRESETS

# Check for OpenAI-compatible API
try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False


class StoryAnalyzer:
    """
    Analyzes user topic and generates story proposals
    Uses DeepSeek API for analysis
    """
    
    MAX_REVISIONS = 3
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "deepseek-chat",
        base_url: str = "https://api.deepseek.com"
    ):
        self.api_key = api_key or os.getenv("DEEPSEEK_API_KEY")
        self.model = model
        self.base_url = base_url
        self._client = None
    
    def is_available(self) -> bool:
        """Check if API is available"""
        return OPENAI_AVAILABLE and bool(self.api_key)
    
    @property
    def client(self):
        """Lazy load OpenAI client"""
        if self._client is None and self.is_available():
            self._client = OpenAI(
                api_key=self.api_key,
                base_url=self.base_url
            )
        return self._client
    
    def analyze_topic(
        self,
        topic: str,
        style: str = "documentary",
        target_duration: int = 60,
        previous_feedback: str = ""
    ) -> StoryProposal:
        """
        Analyze topic and generate story proposal
        
        Args:
            topic: User's content topic
            style: Visual style preset
            target_duration: Target video duration in seconds
            previous_feedback: Feedback from rejected proposal
            
        Returns:
            StoryProposal with analysis and outline
        """
        if not self.is_available():
            # Fallback to simple analysis
            return self._simple_analysis(topic, style)
        
        style_info = STYLE_PRESETS.get(style, STYLE_PRESETS["documentary"])
        
        prompt = f"""Analyze the following topic and create a story outline for a video.

Topic: {topic}
Style: {style_info.name} - {style_info.description}
Target Duration: {target_duration} seconds
Approximate Scenes: {target_duration // 8} scenes (~8 seconds each)

{f"Previous feedback: {previous_feedback}" if previous_feedback else ""}

Please respond in the following format:

## Analysis
[Analyze how this topic should be presented, target audience, strengths]

## Outline
1. [Scene 1: Brief description]
2. [Scene 2: Brief description]
3. [Scene 3: Brief description]
...

## Key Points
- [Key point 1]
- [Key point 2]
- [Key point 3]

Respond in English"""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a professional content planner, expert in creating engaging video story outlines."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=1500,
                temperature=0.5  # Balanced creativity with consistency for outlines
            )
            
            content = response.choices[0].message.content
            return self._parse_analysis(topic, content)
            
        except Exception as e:
            # Fallback on error
            return self._simple_analysis(topic, style, error=str(e))
    
    def _parse_analysis(self, topic: str, content: str) -> StoryProposal:
        """Parse AI response into StoryProposal"""
        lines = content.split("\n")
        
        analysis = ""
        outline = []
        key_points = []
        
        current_section = None
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            if "## การวิเคราะห์" in line or "## Analysis" in line:
                current_section = "analysis"
            elif "## โครงเรื่อง" in line or "## Outline" in line:
                current_section = "outline"
            elif "## จุดสำคัญ" in line or "## Key Points" in line:
                current_section = "key_points"
            elif line.startswith("##"):
                current_section = None
            elif current_section == "analysis":
                analysis += line + " "
            elif current_section == "outline":
                if line.startswith(("1.", "2.", "3.", "4.", "5.", "6.", "7.", "8.", "9.", "-")):
                    outline.append(line.lstrip("0123456789.- "))
            elif current_section == "key_points":
                if line.startswith("-"):
                    key_points.append(line.lstrip("- "))
        
        return StoryProposal(
            topic=topic,
            analysis=analysis.strip(),
            outline=outline,
            key_points=key_points,
            status="pending"
        )
    
    def _simple_analysis(
        self,
        topic: str,
        style: str = "documentary",
        error: str = ""
    ) -> StoryProposal:
        """Simple analysis without AI"""
        return StoryProposal(
            topic=topic,
            analysis=f"Story outline for: {topic}" + (f" (AI Error: {error})" if error else ""),
            outline=[
                f"Opening: Introduce {topic[:30]}...",
                "Main Content: Explain details",
                "Examples/Case studies",
                "Summary and Call to Action"
            ],
            key_points=[
                "Present clear information",
                "Use supporting visuals",
                "End with Call to Action"
            ],
            status="pending"
        )
    
    def revise_proposal(
        self,
        proposal: StoryProposal,
        feedback: str
    ) -> StoryProposal:
        """
        Create revised proposal based on feedback
        
        Args:
            proposal: Previous rejected proposal
            feedback: User's rejection feedback
            
        Returns:
            New StoryProposal with incremented version
        """
        if proposal.version >= self.MAX_REVISIONS:
            raise ValueError(
                f"Maximum revisions ({self.MAX_REVISIONS}) reached. "
                "Please create a new project."
            )
        
        new_proposal = self.analyze_topic(
            topic=proposal.topic,
            previous_feedback=feedback
        )
        
        new_proposal.version = proposal.version + 1
        return new_proposal


def analyze_topic(
    topic: str,
    style: str = "documentary",
    target_duration: int = 60,
    api_key: Optional[str] = None
) -> StoryProposal:
    """Convenience function for topic analysis"""
    analyzer = StoryAnalyzer(api_key=api_key)
    return analyzer.analyze_topic(topic, style, target_duration)
