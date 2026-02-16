"""
AI Studio Output Generator for VDO Content V2
Generates Style Instructions + Text for Google AI Studio voice generation
"""

from .models import Project, StylePreset, STYLE_PRESETS


def generate_ai_studio_output(
    project: Project,
    full_script: str
) -> tuple[str, str]:
    """
    Generate AI Studio output in two parts:
    1. Style Instructions (voice settings)
    2. Script Text (narration)
    
    Args:
        project: Project with settings
        full_script: Full narration script
        
    Returns:
        Tuple of (style_instructions, script_text)
    """
    import os
    
    style = STYLE_PRESETS.get(project.default_style, STYLE_PRESETS["documentary"])
    
    # Get API key for DeepSeek
    api_key = os.getenv("DEEPSEEK_API_KEY", "")
    
    # Generate concise English style instructions using DeepSeek
    if api_key:
        try:
            from openai import OpenAI
            client = OpenAI(api_key=api_key, base_url="https://api.deepseek.com")
            
            # Prepare context for AI
            voice_type = _get_voice_type(project)
            pacing = "slow and clear" if style.voice_speed < 1 else "normal" if style.voice_speed == 1 else "fast and energetic"
            
            prompt = f"""Generate a concise, professional style instruction for Thai voice narration in English.

Style: {style.name}
Description: {style.description}
Voice: {voice_type}
Speed: {style.voice_speed}x ({pacing})
Voice Style: {style.voice_style}
Duration: ~{project.target_duration} seconds

Requirements:
- Write in clear, concise English (2-3 sentences max)
- Focus on tone, pacing, and emotion
- No decorative headers or emojis
- Professional and direct
- Example: "Generate Thai voice narration with a {style.voice_style} tone. Speak at {style.voice_speed}x speed with {pacing} pacing. The overall style should be {style.description.lower()}."

Generate the instruction:"""
            
            response = client.chat.completions.create(
                model="deepseek-chat",
                messages=[
                    {"role": "system", "content": "You are a professional voice direction writer. Generate concise, clear instructions in English."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=200
            )
            
            style_instructions = response.choices[0].message.content.strip()
            
        except Exception as e:
            # Fallback to simple template if AI fails
            style_instructions = f"Generate Thai voice narration with a {style.voice_style} tone. Speak at {style.voice_speed}x speed. The overall style should be {style.description.lower()}."
    else:
        # No API key - use simple template
        style_instructions = f"Generate Thai voice narration with a {style.voice_style} tone. Speak at {style.voice_speed}x speed. The overall style should be {style.description.lower()}."
    
    # Script Text - also simplified
    script_text = full_script.strip()
    
    return style_instructions, script_text


def _get_voice_type(project: Project) -> str:
    """Determine voice type from project settings"""
    # Can be extended based on character_reference
    char = project.character_reference.lower() if project.character_reference else ""
    
    if "ผู้ชาย" in char or "male" in char:
        return "Thai Male (ผู้ชาย)"
    elif "ผู้หญิง" in char or "female" in char:
        return "Thai Female (ผู้หญิง)"
    else:
        return "Thai Female (ผู้หญิง) - Default"


def format_for_display(style_instructions: str, script_text: str) -> str:
    """Format both parts for display"""
    return f"""
{style_instructions}

---

{script_text}
"""


class AIStudioGenerator:
    """Class-based interface for AI Studio output"""
    
    def __init__(self, project: Project):
        self.project = project
    
    def generate(self, script: str) -> dict:
        """Generate AI Studio output"""
        style_inst, script_text = generate_ai_studio_output(
            self.project, script
        )
        
        return {
            "style_instructions": style_inst,
            "script_text": script_text,
            "combined": format_for_display(style_inst, script_text)
        }
