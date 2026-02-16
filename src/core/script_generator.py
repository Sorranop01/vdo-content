"""
Script Generator - Generate narration scripts with AI (Multi-Provider)

Supports: DeepSeek, OpenAI, Gemini, Claude via LLMRouter
"""

import logging
import os
from typing import Optional

logger = logging.getLogger("vdo_content.script_generator")

from .llm_router import LLMRouter, get_router, LLMResponse
from .llm_config import ProviderName, DEFAULT_PROVIDER, get_available_providers


class ScriptGenerator:
    """Generate narration scripts using multiple LLM providers"""
    
    def __init__(
        self, 
        api_key: Optional[str] = None,
        provider: ProviderName = DEFAULT_PROVIDER,
        model: Optional[str] = None
    ):
        """
        Initialize script generator
        
        Args:
            api_key: API key (optional, uses env vars)
            provider: LLM provider (deepseek, openai, gemini, claude)
            model: Specific model ID (optional)
        """
        self.provider = provider
        self.model = model
        self._router = get_router()
        
        # Legacy support: if api_key provided, set env var for the provider
        if api_key:
            from .llm_config import get_provider as _get_provider
            try:
                env_key = _get_provider(provider).env_key
                os.environ[env_key] = api_key
            except ValueError:
                pass
    
    def is_available(self) -> bool:
        """Check if any LLM provider is configured"""
        return len(get_available_providers()) > 0
    
    def set_provider(self, provider: ProviderName, model: Optional[str] = None):
        """Switch LLM provider"""
        self.provider = provider
        self.model = model
    
    def generate_script(
        self,
        topic: str,
        style: str = "documentary",
        target_duration: int = 60,
        language: str = "en",
        provider: Optional[ProviderName] = None,
        story_proposal = None,
        visual_context: Optional[str] = None
    ) -> str:
        """
        Generate narration script from topic
        
        Args:
            topic: Content topic (e.g., "ลดน้ำหนักใน 2 เดือน")
            style: Content style (documentary, storytelling, etc.)
            target_duration: Target duration in seconds
            language: Output language (th/en)
            provider: Override default provider for this call
            story_proposal: StoryProposal from Ideation (optional)
            visual_context: Visual theme/director's note (optional)
            
        Returns:
            Generated script text
        """
        if not self.is_available():
            raise RuntimeError("No LLM provider configured. Set API key in .env")
        
        use_provider = provider or self.provider
        
        # Calculate approximate word count
        if language == "th":
            target_chars = target_duration * 10
            length_hint = f"ประมาณ {target_chars} ตัวอักษร"
        else:
            target_words = int(target_duration * 2.5)
            length_hint = f"approximately {target_words} words"
        
        # Style-specific prompts
        style_prompts = {
            "documentary": "Documentary style, informative, objective, credible",
            "storytelling": "Storytelling style, emotional, engaging, captivating",
            "motivational": "Motivational style, inspiring, action-oriented",
            "tutorial": "Tutorial style, step-by-step, clear explanations",
        }
        
        style_hint = style_prompts.get(style, style_prompts["documentary"])
        
        # Build context from story proposal
        context_parts = []
        if story_proposal:
            # Handle both dict (from DB JSON) and StoryProposal object
            if isinstance(story_proposal, dict):
                analysis = story_proposal.get('analysis', '')
                outline = story_proposal.get('outline', [])
                key_points = story_proposal.get('key_points', [])
            else:
                analysis = getattr(story_proposal, 'analysis', '')
                outline = getattr(story_proposal, 'outline', [])
                key_points = getattr(story_proposal, 'key_points', [])
            
            if analysis:
                context_parts.append(f"การวิเคราะห์:\n{analysis}")
            
            if outline:
                context_parts.append("\nโครงเรื่อง:")
                for i, item in enumerate(outline, 1):
                    context_parts.append(f"{i}. {item}")
            
            if key_points:
                context_parts.append("\nประเด็นหลักที่ต้องนำเสนอ:")
                for i, point in enumerate(key_points, 1):
                    context_parts.append(f"{i}. {point}")
        
        if visual_context:
            context_parts.append(f"\nแนวทางภาพ: {visual_context}")
        
        # Construct prompt with STRICT duration enforcement
        if language == "th":
            # Calculate min/max bounds (±20% tolerance)
            min_chars = int(target_chars * 0.8)
            max_chars = int(target_chars * 1.2)
            num_scenes = max(3, target_duration // 8)  # ~8 seconds per scene
            
            system_prompt = f"""You are a professional video script writer for Thai language content.

**CRITICAL LENGTH REQUIREMENT:**
- Target duration: {target_duration} seconds
- You MUST write approximately {target_chars} Thai characters (±20%)
- Minimum: {min_chars} characters, Maximum: {max_chars} characters
- Aim for approximately {num_scenes} paragraphs/scenes

**Rules:**
1. Write ONLY the actual spoken narration — the exact words to be read aloud by a voice actor
2. Do NOT include scene descriptions, stage directions, or visual instructions
3. Do NOT include parenthetical notes like (ฉากเปิด...), (บรรยากาศ...), (ตัวละคร...)
4. Do NOT include scene labels like [ฉาก 1], ฉากที่ 1:, Scene 1: etc.
5. Do NOT describe camera angles, character actions, lighting, or visual elements
6. Write ONLY in Thai characters (ก-ฮ, vowels, tone marks) — no English, Japanese, or Chinese
7. Use proper Thai spelling - if unsure, use simpler words
8. Numbers should be written as Thai words (e.g., "สิบ กิโลกรัม", not "10 kg")
9. Keep sentences short, max 80 characters each
10. Each sentence on a new line
11. No headers, numbering, or markdown formatting
12. Natural conversational style — as if speaking directly to the viewer
13. **IMPORTANT**: Count your characters! Script MUST be {min_chars}-{max_chars} characters.

**⚠️ WRONG OUTPUT (contains scene directions — DO NOT do this):**
- (ฉากเปิดด้วยตัวละครผู้หญิงวัยรุ่น ใส่ชุดสบายๆ ยืนอยู่หน้าโต๊ะเครื่องแป้ง)
- [ฉาก 1: ห้องนอน]
- (บรรยากาศสีพาสเทลอ่อนๆ ให้ความรู้สึกอบอุ่น)

**✅ CORRECT OUTPUT (only spoken words):**
- รู้ไหมครับ
- แค่ลดน้ำหนักลงได้เพียงห้าเปอร์เซ็นต์
- ร่างกายของเราก็จะเปลี่ยนแปลงไปอย่างน่าทึ่ง

**Style:** {style_hint}
**Target Length:** {length_hint} (THIS IS MANDATORY, NOT OPTIONAL)
"""
            
            # Build ideation context string
            ideation_context = "\n".join(context_parts) if context_parts else ''
            
            user_prompt = f"""Write a Thai narration script about: {topic}

{ideation_context}

⚠️ CRITICAL: Your script MUST be approximately {target_chars} characters ({target_duration} seconds).
If too short, add more content. If too long, summarize.

Remember: Use 100% correct Thai language. No English or garbled characters!

Create a natural script covering the specified topics."""
        else:
            target_words = int(target_duration * 2.5)
            min_words = int(target_words * 0.8)
            max_words = int(target_words * 1.2)
            
            system_prompt = f"""You are a professional video content script writer.
Write narration script in English suitable for voice-over.
Style: {style}

**CRITICAL LENGTH REQUIREMENT:**
- Target duration: {target_duration} seconds
- You MUST write approximately {target_words} words (±20%)
- Minimum: {min_words} words, Maximum: {max_words} words

Rules:
- Write short sentences, max 15 words each
- Each sentence on a new line
- No headers or numbering
- Write naturally as if speaking
- **COUNT YOUR WORDS**: Script MUST be {min_words}-{max_words} words."""
            
            user_prompt = f"""Write a narration script about: {topic}

⚠️ CRITICAL: Your script MUST be approximately {target_words} words ({target_duration} seconds)."""
        
        # Call LLM via router with lower temperature for Thai
        response = self._router.chat(
            messages=[{"role": "user", "content": user_prompt}],
            provider=use_provider,
            model=self.model,
            system_prompt=system_prompt,
            temperature=0.3 if language == "th" else 0.5,  # Lower temp for Thai quality
            max_tokens=4000  # Increased for longer scripts
        )
        
        script = response.content.strip()
        
        # Strip any scene descriptions/stage directions that slipped through
        script = self._strip_stage_directions(script)
        
        # Validate Thai script quality
        if language == "th":
            script = self._validate_thai_script(script)
            
            # Post-generation length validation
            script = self._validate_script_length(
                script, target_duration, language, topic, 
                use_provider, style_hint, context_parts
            )
        
        return script
    
    def _validate_thai_script(self, script: str) -> str:
        """
        Validate Thai script quality and warn about common issues
        
        Args:
            script: Generated Thai script
            
        Returns:
            Validated script (may include warning comments)
        """
        import re
        
        issues = []
        
        # Check for English characters (except numbers and basic punctuation)
        if re.search(r'[a-zA-Z]{2,}', script):
            english_words = re.findall(r'[a-zA-Z]{2,}', script)
            issues.append(f"⚠️ พบคำภาษาอังกฤษ: {', '.join(set(english_words[:5]))}")
        
        # Check for common garbled patterns
        garbled_patterns = [
            r'[ก-ฮ][a-zA-Z][ก-ฮ]',  # Thai-English-Thai mix
            r'[ก-ฮ]{1}[าิีึืุู]{2,}',  # Multiple vowels (unusual)
            r'[\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FFF]',  # Japanese/Chinese chars
        ]
        
        for pattern in garbled_patterns:
            if re.search(pattern, script):
                issues.append("⚠️ พบรูปแบบตัวอักษรผิดปกติ - แนะนำให้สร้างใหม่")
                break
        
        # Check for common misspellings
        common_errors = {
            r'การลตร์': 'การลด',
            r'นำหนัก': 'น้ำหนัก',
            r'อะะ': 'อะ',
        }
        
        for wrong, correct in common_errors.items():
            if re.search(wrong, script):
                issues.append(f"⚠️ อาจสะกดผิด: '{wrong}' ควรเป็น '{correct}'")
        
        # If issues found, log warning
        if issues:
            warning = "⚠️ คำเตือน: AI อาจสร้างข้อความที่มีปัญหา กรุณาตรวจสอบก่อนใช้งาน\n"
            warning += "\n".join(issues)
            logger.warning(warning)
            
        return script
    
    def _strip_stage_directions(self, script: str) -> str:
        """Remove scene descriptions, stage directions, and non-spoken content from script."""
        import re
        if not script:
            return script
        lines = script.split("\n")
        spoken = []
        for line in lines:
            stripped = line.strip()
            if not stripped:
                # Preserve blank lines between paragraphs
                if spoken and spoken[-1] != "":
                    spoken.append("")
                continue
            # Skip lines entirely in parentheses (stage directions)
            if stripped.startswith("(") and stripped.endswith(")"):
                continue
            # Skip Thai visual/scene directions: (ภาพ...), (ฉาก...), (ตัวละคร...) etc.
            # These may not end with ) if the AI truncates or wraps them
            if re.match(r'^\((?:ภาพ|ฉาก|ตัวละคร|บรรยากาศ|เสียง|แสง|กล้อง|มุมกล้อง|ซูม|แพน|ทันใดนั้น|สลิต|คัท|โคลสอัพ|ไวด์ช็อต)', stripped):
                continue
            # Skip lines in square brackets
            if stripped.startswith("[") and stripped.endswith("]"):
                continue
            # Skip scene headers: "Scene 1:", "ฉากที่ 1:"
            if re.match(r'^(scene|ฉาก|ฉากที่)\s*\d+', stripped, re.IGNORECASE):
                continue
            # Skip separator lines
            if re.match(r'^[-=*]{3,}$', stripped):
                continue
            # Skip markdown bold headers like **ฉากที่ 1:** or **เปิดเรื่อง**
            if re.match(r'^\*\*[^*]+\*\*:?\s*$', stripped):
                continue
            # Remove inline parenthetical directions
            cleaned = re.sub(r'\([^)]*\)', '', stripped).strip()
            # Remove inline markdown bold
            cleaned = re.sub(r'\*\*([^*]+)\*\*', r'\1', cleaned).strip()
            if cleaned:
                spoken.append(cleaned)
        # Remove trailing empty lines
        while spoken and spoken[-1] == "":
            spoken.pop()
        return "\n".join(spoken)
    
    def _validate_script_length(
        self, 
        script: str, 
        target_duration: int, 
        language: str,
        topic: str,
        provider: str,
        style_hint: str,
        context_parts: list
    ) -> str:
        """
        Validate script length matches target duration, regenerate if needed
        
        Args:
            script: Generated script
            target_duration: Target duration in seconds
            language: Language code
            topic: Original topic
            provider: LLM provider
            style_hint: Style hint for regeneration
            context_parts: Context for regeneration
            
        Returns:
            Validated script (may be regenerated)
        """
        if language == "th":
            target_chars = target_duration * 10
            min_chars = int(target_chars * 0.6)  # Allow 40% under
            max_chars = int(target_chars * 1.4)  # Allow 40% over
            
            current_chars = len(script.replace("\n", "").replace(" ", ""))
            
            # Check if within acceptable range
            if min_chars <= current_chars <= max_chars:
                logger.info(f"Script length OK: {current_chars} chars (target: {target_chars})")
                return script
            
            # Script too short or too long - add warning
            if current_chars < min_chars:
                diff = target_chars - current_chars
                warning = f"⚠️ Script too short: {current_chars} chars (need ~{target_chars}, missing ~{diff} chars)"
                logger.warning(warning)
                
                # Try to extend the script
                extend_prompt = f"""The following Thai script is TOO SHORT. 
Current: {current_chars} characters
Target: {target_chars} characters (need {diff} more characters)

Original script:
{script}

Please EXTEND this script by adding more content about: {topic}
Add approximately {diff} more Thai characters.
Keep the same style and tone.
Output ONLY the extended script, no explanations."""
                
                try:
                    response = self._router.chat(
                        messages=[{"role": "user", "content": extend_prompt}],
                        provider=provider,
                        model=self.model,
                        temperature=0.3,
                        max_tokens=4000
                    )
                    extended = response.content.strip()
                    new_chars = len(extended.replace("\n", "").replace(" ", ""))
                    
                    # Only use extended version if it's longer
                    if new_chars > current_chars:
                        logger.info(f"Extended script: {current_chars} → {new_chars} chars")
                        return self._validate_thai_script(extended)
                except Exception as e:
                    logger.warning(f"Extension failed: {e}")
                    
            elif current_chars > max_chars:
                diff = current_chars - target_chars
                warning = f"⚠️ Script too long: {current_chars} chars (target: {target_chars}, excess ~{diff} chars)"
                logger.warning(warning)
                
                # Try to shorten the script
                shorten_prompt = f"""The following Thai script is TOO LONG.
Current: {current_chars} characters  
Target: {target_chars} characters (need to remove {diff} characters)

Original script:
{script}

Please SHORTEN this script to approximately {target_chars} characters.
Keep the most important points, remove redundancy.
Output ONLY the shortened script, no explanations."""
                
                try:
                    response = self._router.chat(
                        messages=[{"role": "user", "content": shorten_prompt}],
                        provider=provider,
                        model=self.model,
                        temperature=0.3,
                        max_tokens=4000
                    )
                    shortened = response.content.strip()
                    new_chars = len(shortened.replace("\n", "").replace(" ", ""))
                    
                    # Only use shortened version if it's shorter but not too short
                    if min_chars <= new_chars < current_chars:
                        logger.info(f"Shortened script: {current_chars} → {new_chars} chars")
                        return self._validate_thai_script(shortened)
                except Exception as e:
                    logger.warning(f"Shortening failed: {e}")
            
            # Return original if adjustment failed
            logger.info(f"Returning original script ({current_chars} chars)")
            return script
        
        return script
    
    def generate_outline(
        self, 
        topic: str, 
        num_points: int = 5,
        provider: Optional[ProviderName] = None
    ) -> list[str]:
        """
        Generate content outline/key points
        
        Args:
            topic: Content topic
            num_points: Number of key points
            provider: Override default provider
            
        Returns:
            List of key points
        """
        if not self.is_available():
            raise RuntimeError("No LLM provider configured.")
        
        use_provider = provider or self.provider
        
        # Define prompts for outline generation
        system_prompt = f"""Generate {num_points} key talking points for a video script.
Return each point on a new line.
Be concise and focused.
No numbering or bullets needed."""
        
        user_prompt = f"Generate {num_points} key points about: {topic}"
        
        response = self._router.chat(
            messages=[{"role": "user", "content": user_prompt}],
            provider=use_provider,
            model=self.model,
            system_prompt=system_prompt,
            temperature=0.5,
            max_tokens=2000
        )
        
        content = response.content.strip()
        points = [p.strip() for p in content.split('\n') if p.strip()]
        return points[:num_points]


# Convenience functions
def generate_script(
    topic: str, 
    api_key: Optional[str] = None,
    provider: ProviderName = DEFAULT_PROVIDER,
    **kwargs
) -> str:
    """Quick function to generate script"""
    generator = ScriptGenerator(api_key, provider=provider)
    return generator.generate_script(topic, **kwargs)

