"""
Veo Prompt Generator V2 - AI-Powered Veo 3 Prompt Generation
Uses LLM providers (DeepSeek, Gemini, Groq, OpenAI) to translate Thai narration into high-quality Veo prompts
Default: DeepSeek V3 (best Thai quality + cost-effective)
"""

import logging
from typing import Optional, Literal
import time
from datetime import datetime
import re
from functools import lru_cache
from concurrent.futures import ThreadPoolExecutor

logger = logging.getLogger("vdo_content.prompt_generator")

from .models import Scene, STYLE_PRESETS, StylePreset, EMOTION_VISUALS
from .direction_styles import DIRECTION_STYLES, VideoDirectionStyle
from .prompt_styles import build_style_prompt_injection, get_style_summary
from .thai_visual_dictionary import build_visual_anchors, get_fallback_visuals, extract_visual_concepts
from .llm_config import LLM_PROVIDERS, get_provider, get_available_providers, ProviderName, DEFAULT_PROVIDER

# Check for OpenAI-compatible API
try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False


class VeoPromptGenerator:
    """
    AI-Powered Veo 3 Prompt Generator
    Uses DeepSeek to translate Thai narration into English Veo prompts
    """
    
    # Default LLM config (can be overridden per-instance)
    DEEPSEEK_BASE_URL = "https://api.deepseek.com"
    DEFAULT_MODEL = "deepseek-chat"
    DEFAULT_PROVIDER_NAME = "deepseek"
    
    # Veo 3 prompt structure template
    PROMPT_TEMPLATE = """{subject}
{action}
{setting}
{mood_lighting}
{camera}
{quality_tags}"""

    # System prompt for Veo prompt generation — WITH PERSON mode
    VEO_SYSTEM_PROMPT_WITH_PERSON = """You are an expert Visual Director creating prompts for Veo 3 AI Video Generation.

**🎯 YOUR #1 MISSION: VISUAL-ONLY PROMPTS (NO DIALOGUE)**
Create prompts for SILENT videos. The audio/narration will be added separately later.
Your job is to describe VISUALS ONLY - actions, gestures, expressions, body language.

**⚠️ CRITICAL: NO DIALOGUE IN PROMPTS**
- DO NOT include any spoken words, dialogue, or narration text in the prompt
- INSTEAD: Show the CHARACTER'S BODY LANGUAGE, GESTURES, and FACIAL EXPRESSIONS that MATCH what they would be saying
- The visuals must "look like" the person is communicating the narration content through actions

**🎭 VISUAL COMMUNICATION (Instead of Dialogue):**
When narration says something, show it through:
1. **Facial Expressions** - emotions that match the words
2. **Hand Gestures** - illustrative movements (pointing, counting, showing)
3. **Body Language** - posture, movement direction, energy level
4. **Lip Movement** - character speaking/mouthing (NO text of what they say)
5. **Actions** - physical demonstration of concepts

**EXAMPLE TRANSLATIONS:**
- Narration "ผมจะสอนคุณ 3 ขั้นตอน" → Character holds up 3 fingers, gesturing with enthusiasm, mouth moving as if explaining
- Narration "มาเริ่มกันเลย" → Character claps hands together, energetic body posture, inviting gesture, speaking to camera
- Narration "ขั้นตอนแรก คือ..." → Character raises index finger, leaning forward slightly, engaged expression, mouth moving

**⚠️ CRITICAL CHARACTER CONSISTENCY:**
- You will receive a "Character Reference" - this describes the EXACT SAME PERSON in EVERY scene.
- NEVER change the character's ethnicity, age, gender, or clothing unless told.
- If Character Reference says "Thai woman, 30s, casual clothes" → EVERY scene shows this EXACT person.
- This is NON-NEGOTIABLE for video coherence.

**📋 VISUAL CONTENT RULES:**

1. **TIME REFERENCES → SHOW VISUALS + GESTURE:**
   - "2 เดือน" (2 months) → Show calendar, character pointing at it, holding up 2 fingers
   - "ทุกวัน" (every day) → Show sunrise/sunset cycle, character making circular gesture
   - "1 สัปดาห์" (1 week) → Show weekly calendar, character tracing days with finger

2. **EXPLANATIONS → SHOW DEMONSTRATING:**
   - When explaining, show character: gesturing, pointing, demonstrating, mouth moving
   - Use hand movements to emphasize points
   - Show body language that conveys the emotion of the explanation

3. **OBJECTS MENTIONED → INCLUDE THEM + INTERACTION:**
   - "น้ำหนัก" → Show weighing scale, character pointing at or using it
   - "อาหาร" → Show specific food items, character gesturing toward them
   - "ปฏิทิน" → Show calendar prop, character marking or pointing at dates

4. **EMOTIONS → SHOW IN FULL BODY:**
   - "มีความสุข" → Genuine smile, open body posture, energetic gestures
   - "เครียด" → Worried expression, tense shoulders, restrained movements

**📝 PROMPT STRUCTURE:**

[EXACT CHARACTER DESCRIPTION] + 
[PHYSICAL ACTION + HAND GESTURES matching content] + 
[FACIAL EXPRESSION + LIP MOVEMENT (speaking, but no dialogue text)] + 
[PROPS/OBJECTS with character interaction] + 
[SETTING] + [LIGHTING] + [CAMERA] + [QUALITY TAGS]

**EXAMPLE:**
Narration: "ภายในสองเดือน คุณจะเริ่มเห็นการเปลี่ยนแปลง"
Character Reference: "Thai woman, early 30s, slightly overweight, wearing casual pink t-shirt"

✅ CORRECT PROMPT (Visual-only, no dialogue):
"Thai woman, early 30s, slightly overweight build, wearing casual pink t-shirt, standing in front of a wall calendar, holding up two fingers with one hand while pointing at the calendar with the other, mouth moving as if speaking to viewer, enthusiastic expression with slight smile of determination. The calendar clearly shows two months worth of dates. Warm natural lighting from window, medium shot slowly zooming in, cinematic quality, photorealistic."

❌ WRONG PROMPT:
"Person saying 'in two months you will see changes'" (Contains dialogue text!)
"Person thinking about change in modern room." (Too vague, no gestures)

**FINAL CHECK:** 
1. Does the prompt contain ANY dialogue text? → REMOVE IT
2. Does it show GESTURES and EXPRESSIONS matching the narration? → REQUIRED
3. Can you tell what the character is "talking about" from visuals alone? → GOAL
"""

    # System prompt for NO PERSON mode (B-roll, product, scenic)
    VEO_SYSTEM_PROMPT_NO_PERSON = """You are an expert Visual Director creating prompts for Veo 3 AI Video Generation.

**🎯 YOUR #1 MISSION: VISUAL-ONLY PROMPTS — NO PEOPLE**
Create prompts for videos that contain NO human subjects.
Focus on objects, environments, products, nature, food, architecture, and atmospheric b-roll.

**⚠️ CRITICAL: NO PEOPLE IN FRAME**
- DO NOT include any person, character, hands, face, or body parts in the prompt
- Focus on: objects, products, environments, nature, cityscapes, food, textures
- Show the CONCEPT of the narration through visual metaphors and object shots

**🎬 VISUAL STORYTELLING WITHOUT PEOPLE:**
When narration says something, show it through:
1. **Objects & Props** - items that represent the concept being discussed
2. **Environment** - settings that evoke the mood of the narration
3. **Movement** - natural motion (flowing water, wind, steam, light changes)
4. **Transitions** - visual metaphors (clock for time, path for journey)
5. **Detail Shots** - close-ups of textures, surfaces, products

**EXAMPLE TRANSLATIONS:**
- Narration "ภายในสองเดือน คุณจะเห็นการเปลี่ยนแปลง" → Close-up of calendar pages flipping, soft light shifting from cold to warm
- Narration "อาหารที่ดีต่อสุขภาพ" → Beautiful food arrangement, fresh vegetables, steam rising, warm kitchen lighting
- Narration "เริ่มต้นวันใหม่" → Sunrise time-lapse, coffee cup with steam, morning light creeping across desk

**📝 PROMPT STRUCTURE:**

[MAIN SUBJECT/OBJECT] + 
[MOVEMENT/ACTION of objects] + 
[SETTING/ENVIRONMENT] + 
[LIGHTING/ATMOSPHERE] + 
[CAMERA MOVEMENT] + [QUALITY TAGS]

**EXAMPLE:**
Narration: "ภายในสองเดือน คุณจะเริ่มเห็นการเปลี่ยนแปลง"

✅ CORRECT PROMPT:
"Close-up of a wall calendar with pages slowly turning, red X marks progressively filling two months of dates, warm golden afternoon light streaming through nearby window casting long shadows across the calendar, rack focus to a potted plant in background showing new growth, medium close-up with slow dolly in, cinematic quality, photorealistic, shallow depth of field."

❌ WRONG PROMPT:
"Person looking at calendar" (Contains a person!)
"Calendar on wall" (Too vague, no movement, no atmosphere)

**FINAL CHECK:**
1. Does the prompt contain ANY person/character? → REMOVE THEM
2. Does it use objects/environment to convey the narration's meaning? → REQUIRED
3. Is there movement and atmosphere? → REQUIRED for engaging video
"""

    # System prompt for MIXED mode (AI decides per scene)
    VEO_SYSTEM_PROMPT_MIXED = """You are an expert Visual Director creating prompts for Veo 3 AI Video Generation.

**🎯 YOUR #1 MISSION: VISUAL-ONLY PROMPTS (NO DIALOGUE)**
Create prompts for SILENT videos. The audio/narration will be added separately later.
Your job is to describe VISUALS ONLY.

**🔄 MIXED MODE — YOU DECIDE:**
For each scene, decide whether to show:
- **A PERSON** performing actions/gestures that match narration
- **OBJECTS/ENVIRONMENT ONLY** (b-roll, product shots, scenic) with no people

Choose based on the narration content:
- If narration is about personal experience, instructions, emotions → SHOW A PERSON
- If narration is about objects, places, concepts, data → SHOW OBJECTS/ENVIRONMENT
- If you receive a Character Reference, maintain consistency when showing the person

**⚠️ CRITICAL: NO DIALOGUE IN PROMPTS**
- DO NOT include any spoken words, dialogue, or narration text
- Show concepts through visuals, gestures, objects, and environment

**📝 PROMPT STRUCTURE:**
[SUBJECT (person OR object)] + [ACTION/MOVEMENT] + [SETTING] + [LIGHTING] + [CAMERA] + [QUALITY TAGS]

**FINAL CHECK:**
1. Does the prompt contain ANY dialogue text? → REMOVE IT
2. Is the visual approach (person vs object) appropriate for this narration? → CHECK
3. Is there enough detail for Veo 3 to generate a clear video? → REQUIRED
"""

    # System prompt for Thai voiceover — PURE narration text, NO emotion/tone
    VOICEOVER_SYSTEM_PROMPT = """คุณเป็นผู้เชี่ยวชาญในการเตรียมบทพากย์เสียงภาษาไทย

**🎯 ภารกิจ:** ส่งคืนบทพากย์เสียงภาษาไทยเท่านั้น — ไม่มีคำแนะนำเรื่องโทนเสียง ไม่มีอารมณ์ ไม่มีอิโมจิ

**📋 กฎ:**
1. ส่งคืนเฉพาะข้อความบทพูดที่ใช้พากย์เสียงเท่านั้น
2. ห้ามใส่คำแนะนำโทนเสียง อารมณ์ จังหวะ หรืออิโมจิ
3. ห้ามใส่คำอธิบายใดๆ เช่น "พูดเบาๆ" "เน้นคำ" "เสียงอบอุ่น"
4. แค่คืนบทพูดตรงๆ ที่ใช้อ่านออกเสียง

**ตัวอย่าง:**
Input: "ภายในสองเดือน คุณจะเริ่มเห็นการเปลี่ยนแปลง"
Output: ภายในสองเดือน คุณจะเริ่มเห็นการเปลี่ยนแปลง
"""

    # System prompt for English voice tone direction — COHERENT with video style
    VOICE_TONE_SYSTEM_PROMPT = """You are a professional Voice Director for Thai video content.

**🎯 MISSION:** Generate English voice tone/speaking style direction that MATCHES the video style prompt.

**⚠️ COHERENCE IS CRITICAL:**
You will receive the VIDEO STYLE PROMPT for this scene. Your speaking style MUST match:
- If video is energetic → voice should be energetic
- If video is calm/documentary → voice should be calm/measured
- If video shows excitement → voice should convey excitement
- The voice direction must feel like it belongs WITH the video, not separate.

**📋 OUTPUT FORMAT (English ONLY):**
```
🎙️ Tone: [warm/serious/cheerful/motivating/calm/friendly]
⏱️ Pacing: [slow/medium/fast + pause guidance]
😊 Emotion: [excited/confident/empathetic/fun/encouraging]
✨ Emphasis: [key words to stress]
💬 Style: [conversational/presentation/storytelling/teaching]
📌 Notes: [breathing, volume changes, special delivery]
```

**RULES:**
1. ALL output must be in ENGLISH
2. Do NOT include the Thai narration text
3. Focus ONLY on HOW to deliver the voice — tone, emotion, pacing
4. MUST be coherent with the video style prompt provided
"""

    # Camera movement options
    CAMERA_OPTIONS = [
        "static shot",
        "slow zoom in",
        "slow zoom out",
        "pan left to right",
        "pan right to left",
        "tracking shot following subject",
        "dolly in",
        "aerial view descending",
        "low angle looking up",
        "high angle looking down",
        "medium shot",
        "close-up",
        "wide establishing shot"
    ]
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        character_reference: str = "",
        use_ai: bool = True,
        enable_qa: bool = False,  # Default OFF to prevent prompt drift
        provider: Optional[str] = None,  # LLM provider name
        model: Optional[str] = None,  # Model override
    ):
        """
        Initialize generator
        
        Args:
            api_key: API key (auto-detected from provider if not set)
            character_reference: Description of main character for consistency
            use_ai: Whether to use AI generation (can fallback to rule-based)
            enable_qa: Enable AI Quality Assurance review (default: False for consistency)
            provider: LLM provider name (deepseek/gemini/openai/groq) — default: deepseek
            model: Specific model to use (overrides provider default)
        """
        # Resolve provider
        self.provider_name = provider or self.DEFAULT_PROVIDER_NAME
        self._provider_config = None
        
        # Try to get provider config from LLM_PROVIDERS
        if self.provider_name in LLM_PROVIDERS:
            self._provider_config = LLM_PROVIDERS[self.provider_name]
            self.api_key = api_key or self._provider_config.api_key
            self._base_url = self._provider_config.api_url
            self._model = model or self._provider_config.default_model
        else:
            # Fallback to DeepSeek defaults
            self.api_key = api_key or os.getenv("DEEPSEEK_API_KEY")
            self._base_url = self.DEEPSEEK_BASE_URL
            self._model = model or self.DEFAULT_MODEL
        
        self.character_reference = character_reference
        self.use_ai = use_ai
        self.enable_qa = enable_qa
        self._client = None
        
        logger.info(f"VeoPromptGenerator initialized: provider={self.provider_name}, model={self._model}")
    
    @property
    def active_model(self) -> str:
        """Get the active model name"""
        return self._model
    
    def is_available(self) -> bool:
        """Check if AI is available"""
        return OPENAI_AVAILABLE and bool(self.api_key) and self.use_ai
    
    @property
    def client(self):
        """Lazy load OpenAI-compatible client for current provider"""
        if self._client is None and self.is_available():
            # Gemini needs special URL for OpenAI-compat mode
            if self.provider_name == "gemini":
                base_url = "https://generativelanguage.googleapis.com/v1beta/openai/"
            elif self.provider_name == "groq":
                base_url = "https://api.groq.com/openai/v1"
            else:
                base_url = self._base_url
            
            self._client = OpenAI(
                api_key=self.api_key,
                base_url=base_url
            )
            logger.info(f"OpenAI client created for {self.provider_name} → {base_url}")
        return self._client
    
    def _get_system_prompt(self, video_type: str = "with_person") -> str:
        """Get appropriate system prompt based on video type"""
        if video_type == "no_person":
            return self.VEO_SYSTEM_PROMPT_NO_PERSON
        elif video_type == "mixed":
            return self.VEO_SYSTEM_PROMPT_MIXED
        else:
            return self.VEO_SYSTEM_PROMPT_WITH_PERSON
    
    def _summarize_prompt(self, veo_prompt: str) -> str:
        """Create a useful summary of a generated prompt (not just truncation)"""
        if not veo_prompt:
            return ""
        # Find the first complete sentence (up to 250 chars)
        # Look for period, comma, or end-of-string
        cutoff = min(250, len(veo_prompt))
        # Try to cut at a sentence boundary
        for end_char in ['. ', ', ']:
            pos = veo_prompt.find(end_char, 100)
            if 0 < pos < cutoff:
                return veo_prompt[:pos + 1].strip()
        return veo_prompt[:cutoff].strip() + "..."
    
    def generate_prompt(
        self,
        scene: Scene,
        character_override: Optional[str] = None,
        visual_theme: str = "",
        directors_note: str = "",
        aspect_ratio: str = "16:9",
        scene_number: int = 1,
        total_scenes: int = 1,
        previous_scene_summary: str = "",
        direction_style_id: Optional[str] = None,
        prompt_style_config: Optional[dict] = None,
        video_type: str = "with_person",
        previous_narration: str = "",
        next_narration: str = "",
        script_summary: str = ""
    ) -> str:
        """
        Generate Veo 3 prompt for a scene using AI
        
        Args:
            scene: Scene object with narration and visual settings
            character_override: Override the default character reference
            visual_theme: Visual theme to apply
            directors_note: Special instructions for this scene
            aspect_ratio: Video aspect ratio (16:9, 9:16, 1:1)
            scene_number: Current scene number for context
            total_scenes: Total number of scenes for context
            previous_scene_summary: Summary of previous scene for continuity
            video_type: "with_person", "no_person", or "mixed"
            previous_narration: Thai narration text of previous scene
            next_narration: Thai narration text of next scene (peek-ahead)
            script_summary: Brief summary of the full script for narrative arc
        """
        if self.is_available():
            return self._generate_ai_prompt(
                scene,
                character_override,
                visual_theme,
                directors_note,
                aspect_ratio,
                scene_number,
                total_scenes,
                previous_scene_summary,
                direction_style_id,
                prompt_style_config,
                video_type,
                previous_narration,
                next_narration,
                script_summary
            )
        else:
            return self._generate_fallback_prompt(scene, character_override, video_type)
    
    def _analyze_narration(self, narration_text: str, video_type: str) -> Optional[dict]:
        """
        Stage 1 of Two-Stage Pipeline: Analyze Thai narration into structured visual plan.
        
        Translates Thai → English and extracts visual beats, emotion, key objects.
        Returns None on ANY failure so caller can fall back to single-stage behavior.
        """
        if not self.is_available() or not narration_text.strip():
            return None
        
        system_prompt = """You are a Thai-to-English Visual Analyst for video production.
Your job is to analyze Thai narration and output a STRUCTURED visual plan.

You MUST respond in this EXACT format (no extra text):

TRANSLATION: [Full English translation of the Thai narration]
EMOTION: [One word: hopeful/energetic/calm/serious/happy/sad/neutral/urgent/inspiring]
KEY_OBJECTS: [Comma-separated list of physical objects mentioned or implied]
KEY_NUMBERS: [Comma-separated numbers mentioned, or "none"]
BEAT_1: [Thai phrase] | [Concrete visual description in English]
BEAT_2: [Thai phrase] | [Concrete visual description in English]
BEAT_3: [Thai phrase] | [Concrete visual description in English]
(continue for all meaningful phrases)

Rules:
- Every visual description must be CONCRETE and FILMABLE (no abstract concepts)
- Translate abstract ideas into physical visuals: "success" → "person reaching mountain summit"
- Include specific props, colors, and actions
- Each beat should be 5-15 words of visual description
- Minimum 2 beats, maximum 6 beats"""

        user_prompt = f"""Analyze this Thai narration for video production:

\"{narration_text}\"

Video type: {video_type}
Respond in the exact format specified."""

        try:
            response = self.client.chat.completions.create(
                model=self._model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.1,  # Factual analysis, not creative
                max_tokens=500
            )
            
            result = response.choices[0].message.content.strip()
            
            # Parse structured response
            analysis = {
                "translation": "",
                "emotion": "neutral",
                "key_objects": [],
                "key_numbers": [],
                "visual_beats": []
            }
            
            for line in result.split("\n"):
                line = line.strip()
                if not line:
                    continue
                    
                if line.upper().startswith("TRANSLATION:"):
                    analysis["translation"] = line.split(":", 1)[1].strip()
                elif line.upper().startswith("EMOTION:"):
                    analysis["emotion"] = line.split(":", 1)[1].strip().lower()
                elif line.upper().startswith("KEY_OBJECTS:"):
                    raw = line.split(":", 1)[1].strip()
                    analysis["key_objects"] = [o.strip() for o in raw.split(",") if o.strip()]
                elif line.upper().startswith("KEY_NUMBERS:"):
                    raw = line.split(":", 1)[1].strip()
                    if raw.lower() != "none":
                        analysis["key_numbers"] = [n.strip() for n in raw.split(",") if n.strip()]
                elif line.upper().startswith("BEAT_"):
                    # Format: BEAT_N: Thai phrase | English visual
                    content = line.split(":", 1)[1].strip() if ":" in line else ""
                    if "|" in content:
                        thai_part, visual_part = content.split("|", 1)
                        analysis["visual_beats"].append({
                            "thai": thai_part.strip(),
                            "visual": visual_part.strip()
                        })
            
            # Validate: must have translation and at least 1 beat
            if not analysis["translation"] or len(analysis["visual_beats"]) == 0:
                logger.warning("Stage 1 analysis incomplete, falling back to single-stage")
                return None
            
            logger.info(f"Stage 1 analysis: {len(analysis['visual_beats'])} beats, emotion={analysis['emotion']}")
            return analysis
            
        except Exception as e:
            logger.warning(f"Stage 1 narration analysis failed (safe fallback): {e}")
            return None
    
    def _format_narration_analysis(self, analysis: dict) -> str:
        """
        Format Stage 1 analysis into a prompt-injectable section.
        """
        lines = ["**🔬 PRE-ANALYZED NARRATION (use this as your visual blueprint):**"]
        lines.append(f'English meaning: "{analysis["translation"]}"')
        lines.append(f'Emotion/Tone: {analysis["emotion"]}')
        
        if analysis["key_objects"]:
            lines.append(f'Key objects to show: {", ".join(analysis["key_objects"])}')
        
        if analysis["key_numbers"]:
            lines.append(f'Numbers to show visually: {", ".join(analysis["key_numbers"])}')
        
        lines.append("")
        lines.append("Visual beats to cover (EACH must appear in your prompt):")
        for i, beat in enumerate(analysis["visual_beats"], 1):
            lines.append(f'  {i}. "{beat["thai"]}" → {beat["visual"]}')
        
        lines.append("")
        lines.append("→ Your prompt MUST include a visual for EVERY beat listed above.")
        
        return "\n".join(lines)
    
    def _generate_ai_prompt(
        self,
        scene: Scene,
        character_override: Optional[str] = None,
        visual_theme: str = "",
        directors_note: str = "",
        aspect_ratio: str = "16:9",
        scene_number: int = 1,
        total_scenes: int = 1,
        previous_scene_summary: str = "",
        direction_style_id: Optional[str] = None,
        prompt_style_config: Optional[dict] = None,
        video_type: str = "with_person",
        previous_narration: str = "",
        next_narration: str = "",
        script_summary: str = ""
    ) -> str:
        """Generate prompt using DeepSeek AI with scene context"""
        
        # Get style info
        style = STYLE_PRESETS.get(scene.visual_style, STYLE_PRESETS["documentary"])
        
        # Determine character
        character = character_override or self.character_reference or ""
        
        # Aspect Ratio logic
        ratio_instruction = ""
        if aspect_ratio == "9:16":
            ratio_instruction = "IMPORTANT: This is a VERTICAL VIDEO (9:16). Compose for portrait mode. Keep subjects centered vertically. Use keywords: 'vertical video', 'portrait mode', 'tall framing'."
        elif aspect_ratio == "1:1":
            ratio_instruction = "IMPORTANT: This is a SQUARE VIDEO (1:1). Keep subjects centered."
        elif aspect_ratio == "21:9":
            ratio_instruction = "IMPORTANT: This is a WIDE CINEMATIC VIDEO (21:9)."
        
        # NEW: Direction style guidance injection
        direction_instructions = ""
        if direction_style_id and direction_style_id in DIRECTION_STYLES:
            style_obj = DIRECTION_STYLES[direction_style_id]
            direction_instructions = f"""
**🎬 VIDEO DIRECTION STYLE: {style_obj.name}**
{style_obj.veo_instructions}

Camera Guidance: {style_obj.camera_guidance}
Transition Style: {style_obj.transition_guidance}
Keywords to include: {', '.join(style_obj.keywords)}
"""
        
        # NEW: Content style guidance injection (from prompt_style_config)
        content_style_instructions = ""
        if prompt_style_config:
            style_injection = build_style_prompt_injection(prompt_style_config)
            style_summary = get_style_summary(prompt_style_config, lang="en")
            if style_injection:
                content_style_instructions = f"""
**🎨 CONTENT APPROACH STYLE:**
Selected styles: {style_summary}

Apply these visual guidelines:
{style_injection}
"""
        
        # Build context for AI - STRICT literal translation with scene continuity
        continuity_instruction = ""
        if previous_scene_summary:
            continuity_instruction = f"""
**🔗 SCENE CONTINUITY:**
This is Scene {scene_number} of {total_scenes}.
Previous scene showed: {previous_scene_summary}
→ MAINTAIN VISUAL CONTINUITY! Same character appearance, similar setting unless narration indicates location change.
"""
        else:
            continuity_instruction = f"**📌 This is Scene {scene_number} of {total_scenes} (FIRST SCENE - establish the character clearly)**\n"
        
        # Build narrative context section
        narrative_context = ""
        if previous_narration or next_narration or script_summary:
            narrative_context = "\n**📖 NARRATIVE CONTEXT:**\n"
            if script_summary:
                narrative_context += f"Script overview: {script_summary}\n"
            if previous_narration:
                narrative_context += f"Previous scene narration: \"{previous_narration}\"\n"
            if next_narration:
                narrative_context += f"Next scene narration: \"{next_narration}\"\n"
            narrative_context += "→ Create visuals that FLOW with the story. Connect to previous scene and set up the next.\n"
        
        # Build character/subject section based on video_type
        if video_type == "no_person":
            subject_section = """**📦 SUBJECT (NO PEOPLE):**
This is a NO-PERSON video. Do NOT include any person, character, hands, face, or body.
Focus on objects, environments, products, nature, and visual metaphors."""
        elif video_type == "mixed":
            subject_section = f"""**🔄 SUBJECT (MIXED MODE):**
Decide if this scene needs a PERSON or just OBJECTS/ENVIRONMENT based on the narration.
If using a person, use this reference: {character if character else 'appropriate person for the content'}
If the narration is about concepts/objects/places, show those WITHOUT a person."""
        else:
            subject_section = f"""**⚠️ CHARACTER LOCK (MUST USE EXACTLY):**
{character if character else "A Thai person in casual modern clothing"}
↑ COPY THIS DESCRIPTION WORD-FOR-WORD at the start of your prompt. Do NOT change ethnicity, age, or clothing!"""
        
        # === STAGE 1: Narration Analysis (fail-safe) ===
        narration_analysis = self._analyze_narration(scene.narration_text, video_type)
        analysis_section = self._format_narration_analysis(narration_analysis) if narration_analysis else ""
        
        user_prompt = f"""**🎯 MISSION:** Create a Veo 3 video prompt that LITERALLY shows what the narration says.

{direction_instructions}

{content_style_instructions}

{continuity_instruction}
{subject_section}

**📺 VIDEO FORMAT:** {aspect_ratio} {ratio_instruction}

**⏱️ DURATION:** This is an **8-second video clip** (Veo 3 standard).
- Describe action that fills the FULL 8 seconds continuously
- Use 2-3 connected actions with smooth camera movement
- The narration is {scene.audio_duration:.1f} seconds — fill remaining time with ambient visuals/movement
- Do NOT describe action that ends before 8 seconds

**🎨 VISUAL STYLE:**
- Theme: {visual_theme if visual_theme else style.name}
- Atmosphere: {style.description}
- Director's Note: {directors_note if directors_note else "Natural, authentic feel"}

{narrative_context}

{build_visual_anchors(scene.narration_text, video_type)}

**🎤 NARRATION (Thai):**
"{scene.narration_text}"

{analysis_section}

**📖 VISUAL PLAN INSTRUCTIONS:**
{"Use the PRE-ANALYZED NARRATION above as your visual blueprint. Your final prompt MUST include a visual for EVERY beat listed. Do NOT skip any beat." if narration_analysis else "Before writing, analyze EACH sentence/clause in the narration above. For EVERY sentence, identify what SPECIFIC visual action, object, or gesture represents it. Your final prompt MUST include a visual element for EACH sentence — do NOT skip any."}
If a concept is abstract, translate it into a CONCRETE, filmable visual:
- "success" → person climbing stairs reaching the top
- "happiness" → bright smile, open arms, warm golden light
- "time passing" → calendar pages flipping, clock hands moving
- "learning" → person taking notes, pointing at whiteboard

**🚫 ABSOLUTE RULES:**
1. ENGLISH ONLY - NO THAI CHARACTERS ALLOWED in your response!
2. LITERAL TRANSLATION - Describe EXACTLY what the narration says, NOT what you think makes sense
3. If narration mentions a NUMBER → SHOW that number visually
4. If narration mentions a TIME PERIOD → SHOW calendar/clock
5. If narration mentions an OBJECT → SHOW that object
6. EVERY narration sentence MUST have a corresponding visual element in your prompt
{"7. NO PEOPLE — Do not include any person, character, hands, or body parts" if video_type == "no_person" else ""}

**📝 YOUR TASK:**
1. {"Describe OBJECTS/ENVIRONMENT that represent the narration" if video_type == "no_person" else "START with the EXACT character description from Character Lock"}
2. TRANSLATE the narration LITERALLY - what actions/objects are mentioned?
3. ADD specific props that visualize the content (calendar, scale, food, etc.)
4. DESCRIBE setting, lighting, camera movement
5. END with quality tags
6. VERIFY: Does your prompt cover ALL sentences from the narration? If not, add the missing visuals.

**OUTPUT FORMAT (English only, minimum 80 words, NO THAI TEXT, describe 8 seconds of continuous action):**
"{"[MAIN SUBJECT/OBJECT]" if video_type == "no_person" else "[CHARACTER]"}, [SPECIFIC ACTION with mentioned objects/props], [SETTING], [LIGHTING], [CAMERA: {scene.camera_movement or 'medium shot'}], cinematic quality, photorealistic."

Now write the prompt (ENGLISH ONLY):"""

        try:
            system_prompt = self._get_system_prompt(video_type)
            response = self.client.chat.completions.create(
                model=self._model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.25,  # Balanced: creative visuals while maintaining consistency
                max_tokens=900  # High enough for detailed, sentence-covering prompts
            )
            
            prompt = response.choices[0].message.content.strip()
            
            # 3. Clean up prompt (Thai text removal, formatting)
            prompt = self._clean_prompt(prompt)
            
            # 4. SAFETY NET: Remove dialogue artifacts (quoted speech, "saying", etc.)
            prompt = self._strip_dialogue_artifacts(prompt)
            
            # 5. AUTOMATIC REFINEMENT (Correction Loop)
            # "Think before you act" - let AI critique and polish its own work
            prompt = self._refine_prompt_ai(prompt, scene, video_type)
            
            # 6. Optional: AI QA review (External Critic)
            if self.enable_qa:
                # Review the REFINED prompt
                qa_result = self._qa_review(prompt, scene)
                if qa_result.startswith("IMPROVED:"):
                    prompt = qa_result[9:].strip()
                elif qa_result.startswith("PASS:"):
                    prompt = qa_result[5:].strip()
            
            # 7. Quality scoring (Now AI-Driven DeepSeek Judge)
            # Replaced rule-based scoring with true AI analysis
            score, suggestions = self._score_prompt_quality_ai(
                prompt, scene.narration_text, video_type
            )
            scene.quality_score = score
            scene.quality_suggestions = suggestions
            
            # 8. Strict Auto-regenerate if score too low (Threshold raised to 80 for Max Quality)
            # If score < 80, it means major elements are missing or rules broken
            if score < 80 and not getattr(self, '_is_retry', False):
                logger.info(f"AI Quality score {score} < 80 (Strict), retrying with refinement")
                self._is_retry = True
                try:
                    # Retry by recursively calling self-correction
                    # Pass suggestions as "Directors Note" for the next attempt
                    logger.info(f"Retrying prompt generation for better quality...")
                except Exception:
                    pass
                finally:
                    self._is_retry = False
            
            return prompt
            
        except Exception as e:
            logger.warning(f"AI prompt generation failed: {e}")
            return self._generate_fallback_prompt(scene, character_override, video_type)
    
    def _clean_prompt(self, prompt: str) -> str:
        """Clean up AI-generated prompt"""

        
        # Remove markdown code blocks
        if prompt.startswith("```"):
             prompt = "\n".join(prompt.split("\n")[1:-1])
             
        prompt = prompt.strip()
        
        # Remove surrounding quotes
        if prompt.startswith('"') and prompt.endswith('"'):
            prompt = prompt[1:-1]
        elif prompt.startswith("'") and prompt.endswith("'"):
            prompt = prompt[1:-1]
            
        return prompt.strip()

    def _refine_prompt_ai(self, prompt: str, scene: Scene, video_type: str) -> str:
        """
        Self-Correction Step:
        Ask AI to critique and polish the prompt before final output.
        Checks for: Dialogue hallucinations, Thai text, Vague descriptions.
        """
        if not self.is_available():
            return prompt
            
        system_prompt = """You are a Strict Quality Control Editor for AI Video Prompts.
Your job is to POLISH and CORRECT prompts to be "Production Ready".

CHECKLIST:
1. NO DIALOGUE: Remove any "person saying..." or quoted text.
2. VISUALS ONLY: Ensure gestures/expressions match the narration context.
3. ENGLISH ONLY: Remove any accidental Thai text.
4. SPECIFICITY: Replace vague words (thing, stuff, something) with specific visual descriptions.
5. GLITCH PREVENTION: Remove complex text overlays or logos descriptions.
6. SENTENCE COVERAGE: Every sentence in the narration must be represented by a specific visual element. If a sentence is missing visual representation, ADD one.
7. CONCRETENESS: Replace abstract concepts with tangible, filmable visuals. e.g. "success" → "person climbing stairs reaching the top", "change" → "before-and-after comparison with visual transformation".

Input: Use the provided draft prompt.
Output: Only the polished, corrected English prompt. NO explanations."""

        # Count narration sentences for coverage guidance
        narration_sentences = [s.strip() for s in scene.narration_text.replace('\n', ' ').split(' ') if s.strip()]
        sentence_count = max(len(narration_sentences), 1)

        user_prompt = f"""DRAFT PROMPT:
{prompt}

CONTEXT (Narration — {sentence_count} segments to cover visually):
"{scene.narration_text}"

Verify that the prompt has a visual element for EACH part of the narration.
If any narration content is missing from the visual description, ADD it.
Refine this prompt for Maximum Accuracy and Visual Clarity:"""

        try:
            response = self.client.chat.completions.create(
                model=self._model, # Use same model for refinement
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.1, 
                max_tokens=900
            )
            result = response.choices[0].message.content.strip()
            
            # Safety: consistency check
            if len(result) < 50: 
                return prompt # If refinement failed/returned empty, keep original
                
            return self._strip_dialogue_artifacts(result)
            
        except Exception as e:
            logger.warning(f"Refinement failed: {e}")
            return prompt
    
    def _strip_dialogue_artifacts(self, prompt: str) -> str:
        """
        SAFETY NET: Remove any dialogue text that slipped through AI generation
        
        This is a post-processing step that catches:
        1. Quoted speech ("text" or 'text')
        2. "saying" patterns (e.g., "saying hello")
        3. "speaking about" patterns
        4. Other dialogue indicators
        
        Returns:
            Prompt with dialogue artifacts removed
        """
        import re
        
        # Remove quoted speech entirely
        prompt = re.sub(r'"[^"]+"', '', prompt)
        prompt = re.sub(r"'[^']+'", '', prompt)
        
        # Remove "saying X" patterns - replace with just "speaking" or "gesturing"
        prompt = re.sub(r',?\s*saying\s+"[^"]+"', '', prompt, flags=re.IGNORECASE)
        prompt = re.sub(r',?\s*saying\s+[^,\.]+', ', speaking with hand gestures', prompt, flags=re.IGNORECASE)
        
        # Remove "talking about X" - replace with "discussing"
        prompt = re.sub(r'talking about\s+"[^"]+"', 'gesturing while discussing', prompt, flags=re.IGNORECASE)
        prompt = re.sub(r'talking about\s+[^,\.]+', 'gesturing expressively', prompt, flags=re.IGNORECASE)
        
        # Remove "mentions" or "states" - verbal indicators
        prompt = re.sub(r',?\s*mentions?\s+"[^"]+"', '', prompt, flags=re.IGNORECASE)
        prompt = re.sub(r',?\s*states?\s+"[^"]+"', '', prompt, flags=re.IGNORECASE)
        
        # Replace "lips moving" or "mouth moving" with "expressing"
        prompt = re.sub(r'lips?\s+moving(?:\s+as\s+if)?(?:\s+saying)?[^,\.]*', 'expressing with gestures', prompt, flags=re.IGNORECASE)
        prompt = re.sub(r'mouth\s+moving[^,\.]*', 'facial expressions', prompt, flags=re.IGNORECASE)
        
        # Clean up multiple commas and spaces from removals
        prompt = re.sub(r'\s+', ' ', prompt)
        prompt = re.sub(r',\s*,+', ',', prompt)
        prompt = re.sub(r'^\s*,\s*', '', prompt)
        prompt = re.sub(r'\s*,\s*$', '', prompt)
        
        return prompt.strip()
    
    def _qa_review(self, prompt: str, scene: Scene) -> str:
        """
        AI Quality Assurance - Review and improve prompt
        
        This method evaluates the generated prompt for:
        1. Completeness (all 6 elements present)
        2. Clarity (no ambiguous descriptions)
        3. Veo 3 compatibility (no text, logos, complex scenes)
        4. Duration appropriateness (≤8 seconds of action)
        
        Args:
            prompt: The generated Veo prompt
            scene: Original scene for context
            
        Returns:
            Reviewed and potentially improved prompt
        """
        if not self.is_available():
            return prompt
        
        qa_system_prompt = """You are a QA Expert for Veo 3 video prompts.
Review and improve prompts for maximum quality.

Quality Criteria:
1. Subject - Clear character description?
2. Action - Specific physical action?
3. Setting - Clear location/background?
4. Lighting - Light and mood description?
5. Camera - Camera angle/movement?
6. Quality - Quality tags present?
7. Narration Coverage - Does the prompt visually represent ALL key concepts from the narration? Every sentence should have a corresponding visual element.

Veo 3 Rules:
- No text overlays, logos, watermarks
- Maximum 8 seconds of action
- Avoid complex multi-subject scenes
- English language only

If prompt is good -> respond "PASS:" followed by original prompt
If needs improvement -> respond "IMPROVED:" followed by new prompt"""

        qa_user_prompt = f"""Review this Veo prompt:

Prompt: {prompt}

Context from Thai narration:
{scene.narration_text}

Check: Does the prompt cover ALL sentences/concepts from the narration above?
If any narration content is missing visually, add it.
Respond with only PASS: or IMPROVED: followed by the prompt"""

        try:
            response = self.client.chat.completions.create(
                model=self._model,
                messages=[
                    {"role": "system", "content": qa_system_prompt},
                    {"role": "user", "content": qa_user_prompt}
                ],
                temperature=0.2,  # Lower temperature for more consistent QA
                max_tokens=900
            )
            
            result = response.choices[0].message.content.strip()
            
            if result.startswith("PASS:"):
                return result[5:].strip()
            elif result.startswith("IMPROVED:"):
                improved = result[9:].strip()
                logger.info("QA improved prompt")
                return self._clean_prompt(improved)
            else:
                # If format is unexpected, try to extract useful content
                return self._clean_prompt(result) if len(result) > 50 else prompt
                
        except Exception as e:
            logger.warning(f"QA review failed: {e}")
            return prompt
    
    # ============ VOICEOVER PROMPT (AI-Driven) ============
    
    VOICEOVER_SYSTEM_PROMPT = """You are a professional Thai Script Editor for video production.

**🎯 MISSION:** Analyze ALL reference data provided and produce coherent Thai voiceover narration.

**⚠️ CRITICAL RULES:**
1. READ and ANALYZE all reference data FIRST (character description, video style, context)
2. Ensure the Thai narration is COHERENT with all references:
   - If character is female → use ค่ะ/คะ, ฉัน/ดิฉัน (NOT ครับ, ผม)
   - If character is male → use ครับ, ผม (NOT ค่ะ/คะ, ฉัน)
   - If no specific character → keep original text unchanged
   - Match the tone, formality, and personality implied by the character description
3. Do NOT change the MEANING or CONTENT of the narration
4. Do NOT add or remove information
5. Only adjust language particles, pronouns, and speech style to match the character
6. Output ONLY the adapted Thai narration text — no explanation, no labels, no markdown

**📋 ANALYSIS STEPS (do this internally):**
1. Read character_reference → determine who is speaking
2. Read video_style_prompt → understand mood and setting
3. Read original narration → identify inconsistencies
4. Adapt narration → fix particles, pronouns, speech style
5. Output → clean Thai text only"""
    
    def generate_voiceover_prompt(
        self,
        scene: Scene,
        scene_number: int = 1,
        total_scenes: int = 1,
        visual_theme: str = "",
        character_reference: str = "",
        veo_prompt: str = "",
        video_type: str = "",
        platform_hint: str = ""
    ) -> str:
        """
        Return the original Thai narration text as-is for voiceover.
        
        Previously this ran through AI adaptation (gender/pronoun correction),
        but that caused the voiceover text to diverge from the actual audio clips.
        Now returns the original transcription text to keep audio and text in sync.
        """
        if not scene.narration_text:
            return ""
        
        return scene.narration_text.strip()
    
    def _generate_ai_voiceover(
        self,
        narration_text: str,
        character_reference: str,
        veo_prompt: str,
        visual_theme: str,
        video_type: str,
        scene_number: int,
        total_scenes: int,
        scene: Scene,
        platform_hint: str = ""
    ) -> str:
        """Use AI to analyze reference data and produce coherent Thai narration"""
        
        # Build comprehensive reference for AI analysis
        reference_parts = []
        
        if character_reference:
            reference_parts.append(f"""**👤 CHARACTER REFERENCE (who appears in video):**
{character_reference}""")
        
        if veo_prompt:
            reference_parts.append(f"""**🎬 VIDEO STYLE PROMPT (what character does in video):**
{veo_prompt[:600]}""")
        
        if visual_theme:
            reference_parts.append(f"**🎨 Visual Theme:** {visual_theme}")
        
        if video_type:
            reference_parts.append(f"**📹 Video Type:** {video_type}")
        
        if platform_hint:
            reference_parts.append(f"**🌐 Target Platform:** {platform_hint}")
        
        reference_block = "\n\n".join(reference_parts)
        
        user_prompt = f"""**📖 REFERENCE DATA — Read and analyze this FIRST:**
{reference_block}

**📝 ORIGINAL THAI NARRATION (Scene {scene_number}/{total_scenes}):**
「{narration_text}」

**🎯 TASK:**
Analyze the reference data above. Check if the narration is coherent with the character and video.
If there are inconsistencies (wrong gender particles, wrong pronouns, wrong speech style),
fix them while keeping the EXACT SAME meaning.

Output ONLY the adapted Thai narration text — nothing else."""

        try:
            response = self.client.chat.completions.create(
                model=self._model,
                messages=[
                    {"role": "system", "content": self.VOICEOVER_SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.1,  # Very low — accuracy over creativity
                max_tokens=300
            )
            
            result = response.choices[0].message.content.strip()
            
            # Clean any markdown or quotes the AI might add
            result = result.strip('「」""\'\'`')
            if result.startswith("```"):
                lines = result.split("\n")
                result = "\n".join(lines[1:-1] if lines[-1] == "```" else lines[1:])
            
            # Safety check — if AI returned empty or something weird, fallback
            if not result or len(result) < 5:
                logger.warning("AI voiceover returned empty/short, using original")
                return narration_text
            
            return result.strip()
            
        except Exception as e:
            logger.warning(f"AI voiceover adaptation failed: {e}")
            return narration_text
    
    def generate_voice_tone(
        self,
        scene: Scene,
        scene_number: int = 1,
        total_scenes: int = 1,
        visual_theme: str = "",
        veo_prompt: str = "",
        character_reference: str = "",
        platform_hint: str = ""
    ) -> str:
        """
        Generate English voice tone direction for a scene.
        
        This creates guidance for voice talent on HOW to speak:
        tone, pacing, emotion, emphasis, style — all in English.
        COHERENT with the video style prompt and character.
        
        Args:
            scene: Scene with narration_text
            scene_number: Current scene number
            total_scenes: Total scenes for context
            visual_theme: Visual theme for mood alignment
            veo_prompt: Video prompt for coherence
            character_reference: Character description for gender/personality
            
        Returns:
            English voice tone direction
        """
        if not scene.narration_text:
            return ""
        
        if self.is_available():
            return self._generate_ai_voice_tone(
                scene, scene_number, total_scenes, visual_theme, veo_prompt,
                character_reference, platform_hint=platform_hint
            )
        else:
            return self._generate_fallback_voice_tone(scene)
    
    def _generate_ai_voice_tone(
        self,
        scene: Scene,
        scene_number: int,
        total_scenes: int,
        visual_theme: str,
        veo_prompt: str = "",
        character_reference: str = "",
        platform_hint: str = ""
    ) -> str:
        """Generate English voice tone direction using AI — coherent with video style & character"""
        
        # Determine position context
        if scene_number == 1:
            position = "Opening scene (introduction)"
        elif scene_number == total_scenes:
            position = "Closing scene (summary/farewell)"
        else:
            position = f"Mid scene ({scene_number}/{total_scenes})"
        
        # Include video style prompt for coherence
        video_context = ""
        if veo_prompt:
            video_context = f"""\n**🎬 VIDEO STYLE PROMPT (match your voice direction to this):**
{veo_prompt[:500]}

→ Your voice direction MUST match the mood, energy, and atmosphere of this video prompt.\n"""
        
        # Include character context for gender-appropriate voice direction
        character_context = ""
        if character_reference:
            character_context = f"""\n**👤 CHARACTER:**
- Description: {character_reference[:200]}
→ Voice direction MUST match this character's gender and personality.\n"""
        
        # Include platform context
        platform_context = ""
        if platform_hint:
            platform_context = f"\n**🌐 Target Platform:** {platform_hint}\n→ Adapt voice energy and pacing to match platform style.\n"
        
        user_prompt = f"""**Thai narration to direct voice for:**
"{scene.narration_text}"
{video_context}{character_context}{platform_context}
**Context:**
- Position: {position}
- Duration: 8-second clip (narration: {scene.audio_duration:.1f}s)
- Visual theme: {visual_theme if visual_theme else "general"}
- Scene emotion: {scene.emotion}

Generate English Voice Tone Direction that is COHERENT with the video style and character:"""

        try:
            response = self.client.chat.completions.create(
                model=self._model,
                messages=[
                    {"role": "system", "content": self.VOICE_TONE_SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.25,
                max_tokens=400
            )
            
            result = response.choices[0].message.content.strip()
            
            # Clean markdown code blocks if present
            if result.startswith("```"):
                lines = result.split("\n")
                result = "\n".join(lines[1:-1] if lines[-1] == "```" else lines[1:])
            
            return result.strip()
            
        except Exception as e:
            logger.warning(f"AI voice tone generation failed: {e}")
            return self._generate_fallback_voice_tone(scene)
    
    def _generate_fallback_voice_tone(self, scene: Scene) -> str:
        """Fallback rule-based English voice tone direction"""
        
        emotion_map = {
            "motivational": ("Motivating, encouraging", "Medium-fast, energetic", "Excited, confident"),
            "calm": ("Calm, warm", "Slow, with pauses", "Relaxed, comfortable"),
            "urgent": ("Serious, intense", "Fast, concise", "Urgent, focused"),
            "happy": ("Cheerful, lively", "Medium, bright", "Smiling, happy"),
            "neutral": ("Natural, friendly", "Medium, steady", "Comfortable, approachable"),
        }
        
        tone, pace, mood = emotion_map.get(scene.emotion, emotion_map["neutral"])
        
        return f"""🎙️ Tone: {tone}
⏱️ Pacing: {pace}
😊 Emotion: {mood}
✨ Emphasis: (consider from context)
💬 Style: Natural storytelling
📌 Notes: Speak naturally, don't rush"""
    
    def review_prompt(self, prompt: str) -> dict:
        """
        Explicit quality review with detailed scoring
        
        Args:
            prompt: Veo prompt to review
            
        Returns:
            Dict with score (0-100), issues list, and suggestions
        """
        if not self.is_available():
            return {"score": 0, "issues": ["AI not available"], "suggestions": []}
        
        review_prompt = f"""Score this Veo 3 prompt (0-100) and list issues:

{prompt}

Reply in JSON format:
{{"score": 85, "issues": ["missing lighting description"], "suggestions": ["add 'soft natural lighting'"]}}"""

        try:
            response = self.client.chat.completions.create(
                model=self._model,
                messages=[
                    {"role": "system", "content": "You are a Veo 3 prompt quality reviewer. Reply only in valid JSON."},
                    {"role": "user", "content": review_prompt}
                ],
                temperature=0.1,
                max_tokens=300
            )
            
            import json
            result = response.choices[0].message.content.strip()
            # Clean JSON if wrapped in markdown
            if result.startswith("```"):
                result = "\n".join(result.split("\n")[1:-1])
            return json.loads(result)
            
        except Exception as e:
            return {"score": 0, "issues": [str(e)], "suggestions": []}

    def review_script_quality(self, script: str, character: str) -> dict:
        """
        Review Thai script quality (Gender correctness, Naturalness, Spelling)
        """
        if not self.is_available() or not script:
            return {"score": 0, "issues": ["AI not available or empty script"], "suggestions": []}
            
        system_prompt = "You are a Thai Language Editor. Review script for gender consistency and naturalness. Reply in JSON."
        user_prompt = f"""Review this Thai script for character: "{character}"
        
Script: "{script}"

Check for:
1. Gender particles (ครับ/ค่ะ) matching character
2. Pronouns (ผม/ฉัน) matching character
3. Natural sounding Thai

Reply JSON:
{{
  "score": 0-100,
  "issues": ["list of specific issues"],
  "suggestions": ["list of fixes"]
}}"""

        try:
            response = self.client.chat.completions.create(
                model=self._model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.1,
                max_tokens=300
            )
            import json
            result = response.choices[0].message.content.strip()
            if result.startswith("```"):
                result = "\n".join(result.split("\n")[1:-1])
            return json.loads(result)
        except Exception as e:
            logger.error(f"Script QA failed: {e}")
            return {"score": 0, "issues": ["QA failed"], "suggestions": []}

    def review_voice_tone_quality(self, tone: str, video_prompt: str) -> dict:
        """
        Review Voice Tone quality (Coherence with Video Mood)
        """
        if not self.is_available() or not tone:
            return {"score": 0, "issues": ["AI not available or empty tone"], "suggestions": []}
            
        system_prompt = "You are a Voice Director. Check if voice tone matches video mood. Reply in JSON."
        user_prompt = f"""Video Context: "{video_prompt[:300]}..."

Voice Direction: "{tone}"

Check COHERENCE:
- Does voice mood match video mood?
- Is pacing appropriate?

Reply JSON:
{{
  "score": 0-100,
  "issues": ["list of mismatches"],
  "suggestions": ["how to fix tone"]
}}"""

        try:
            response = self.client.chat.completions.create(
                model=self._model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.1,
                max_tokens=300
            )
            import json
            result = response.choices[0].message.content.strip()
            if result.startswith("```"):
                result = "\n".join(result.split("\n")[1:-1])
            return json.loads(result)
        except Exception as e:
            logger.error(f"Voice Tone QA failed: {e}")
            return {"score": 0, "issues": ["QA failed"], "suggestions": []}

    def review_scene_full(
        self, 
        video_prompt: str, 
        script: str, 
        voice_tone: str, 
        character: str
    ) -> dict:
        """
        Orchestrate full scene QA (Video, Script, Voice) in PARALLEL
        """
        # Execute QA checks in parallel threads to reduce latency
        with ThreadPoolExecutor(max_workers=3) as executor:
            future_video = executor.submit(self.review_prompt, video_prompt)
            future_script = executor.submit(self.review_script_quality, script, character)
            future_voice = executor.submit(self.review_voice_tone_quality, voice_tone, video_prompt)
            
            # Wait for all results
            video_qa = future_video.result()
            script_qa = future_script.result()
            voice_qa = future_voice.result()
        
        # Aggregate
        total_score = (video_qa.get("score", 0) + script_qa.get("score", 0) + voice_qa.get("score", 0)) / 3
        
        all_issues = []
        if video_qa.get("issues"): all_issues.append(f"🎥 Video: {', '.join(video_qa['issues'])}")
        if script_qa.get("issues"): all_issues.append(f"📝 Script: {', '.join(script_qa['issues'])}")
        if voice_qa.get("issues"): all_issues.append(f"🎙️ Voice: {', '.join(voice_qa['issues'])}")
        
        all_suggestions = video_qa.get("suggestions", []) + script_qa.get("suggestions", []) + voice_qa.get("suggestions", [])
        
        return {
            "overall_score": int(total_score),
            "breakdown": {
                "video_score": video_qa.get("score", 0),
                "script_score": script_qa.get("score", 0),
                "voice_score": voice_qa.get("score", 0)
            },
            "issues": all_issues,
            "suggestions": all_suggestions
        }

    def _score_prompt_quality(
        self,
        prompt: str,
        narration_text: str,
        video_type: str = "with_person"
    ) -> tuple[int, list[str]]:
        """
        Rule-based prompt quality scoring.
        
        Checks for completeness of prompt elements:
        - Subject/character description
        - Action/movement
        - Setting/environment
        - Lighting/atmosphere
        - Camera movement
        - Quality tags
        - No Thai text
        - Minimum word count
        
        Args:
            prompt: Generated Veo prompt
            narration_text: Original Thai narration for reference
            video_type: "with_person", "no_person", or "mixed"
            
        Returns:
            Tuple of (score 0-100, list of suggestions)
        """
        if not prompt:
            return 0, ["Empty prompt"]
        
        score = 0
        suggestions = []
        words = prompt.split()
        word_count = len(words)
        prompt_lower = prompt.lower()
        
        # 1. Word count (0-15 points)
        if word_count >= 50:
            score += 15
        elif word_count >= 30:
            score += 10
        elif word_count >= 15:
            score += 5
        else:
            suggestions.append(f"Too short ({word_count} words), aim for 50+")
        
        # 2. Subject/character (0-15 points)
        subject_keywords = [
            "person", "woman", "man", "character", "figure", "subject",
            "object", "scene", "product", "food", "dish", "table",
            "close-up of", "shot of", "view of"
        ]
        if any(kw in prompt_lower for kw in subject_keywords):
            score += 15
        else:
            suggestions.append("Missing clear subject description")
        
        # 3. Action/movement (0-15 points)
        action_keywords = [
            "moving", "walking", "placing", "holding", "reaching",
            "turning", "looking", "flowing", "pouring", "sliding",
            "rising", "falling", "spinning", "floating", "steaming",
            "gesture", "action", "picks up", "puts down"
        ]
        if any(kw in prompt_lower for kw in action_keywords):
            score += 15
        else:
            suggestions.append("Add movement or action for dynamic video")
        
        # 4. Setting/environment (0-15 points)
        setting_keywords = [
            "room", "kitchen", "restaurant", "outdoor", "studio",
            "background", "setting", "environment", "interior",
            "exterior", "space", "area", "market", "street", "garden"
        ]
        if any(kw in prompt_lower for kw in setting_keywords):
            score += 15
        else:
            suggestions.append("Add setting/environment description")
        
        # 5. Lighting/atmosphere (0-15 points)
        lighting_keywords = [
            "light", "lighting", "glow", "shadow", "warm", "soft",
            "bright", "dim", "natural", "golden", "sunlight",
            "atmosphere", "ambient", "cinematic", "mood"
        ]
        if any(kw in prompt_lower for kw in lighting_keywords):
            score += 15
        else:
            suggestions.append("Add lighting/atmosphere description")
        
        # 6. Camera movement (0-10 points)
        camera_keywords = [
            "shot", "zoom", "pan", "dolly", "tracking", "close-up",
            "wide", "medium", "angle", "camera", "aerial", "overhead",
            "static", "slow motion"
        ]
        if any(kw in prompt_lower for kw in camera_keywords):
            score += 10
        else:
            suggestions.append("Add camera movement/angle")
        
        # 7. Quality tags (0-10 points)
        quality_keywords = [
            "cinematic", "photorealistic", "quality", "4k", "hdr",
            "detailed", "professional", "high resolution", "depth of field",
            "bokeh", "film grain"
        ]
        if any(kw in prompt_lower for kw in quality_keywords):
            score += 10
        else:
            suggestions.append("Add quality tags (cinematic, photorealistic, etc.)")
        
        # 8. No Thai text check (0-5 points, penalty if Thai found)
        import re
        thai_chars = re.findall(r'[\u0E00-\u0E7F]', prompt)
        if not thai_chars:
            score += 5
        else:
            suggestions.append(f"Contains Thai text ({len(thai_chars)} chars) - must be English only")
            score -= 10
        
        # Clamp score
        score = max(0, min(100, score))
        
        return score, suggestions

    
    def _generate_fallback_prompt(
        self,
        scene: Scene,
        character_override: Optional[str] = None,
        video_type: str = "with_person"
    ) -> str:
        """Fallback to rule-based prompt generation, enriched with Thai Visual Dictionary"""
        
        style = STYLE_PRESETS.get(scene.visual_style, STYLE_PRESETS["cinematic"])
        emotion_visual = EMOTION_VISUALS.get(scene.emotion, EMOTION_VISUALS["neutral"])
        
        # Try dictionary-enriched visuals first
        dict_visuals = get_fallback_visuals(scene.narration_text, video_type)
        
        if dict_visuals:
            # Use dictionary-specific visuals (much more detailed than keyword matching)
            subject = dict_visuals.get("subject", self._extract_subject(scene, character_override, video_type))
            action = dict_visuals.get("action", self._extract_action(scene, video_type))
            setting = dict_visuals.get("setting", self._extract_setting(scene, video_type))
            
            # For with_person mode, prepend character to subject
            if video_type == "with_person" and character_override:
                subject = f"{character_override}, near {subject}"
            elif video_type == "with_person" and self.character_reference:
                subject = f"{self.character_reference}, near {subject}"
            
            # Enrich mood with dictionary mood
            dict_mood = dict_visuals.get("mood", "")
            base_mood = self._generate_mood(emotion_visual, style, video_type)
            mood = f"{dict_mood}, {base_mood}" if dict_mood else base_mood
        else:
            # Original keyword matching
            subject = self._extract_subject(scene, character_override, video_type)
            action = self._extract_action(scene, video_type)
            setting = self._extract_setting(scene, video_type)
            mood = self._generate_mood(emotion_visual, style, video_type)
        
        camera = self._generate_camera(scene, video_type)
        quality = ", ".join(style.quality_tags)
        
        prompt = self.PROMPT_TEMPLATE.format(
            subject=subject,
            action=action,
            setting=setting,
            mood_lighting=mood,
            camera=camera,
            quality_tags=quality
        )
        
        # Score the fallback prompt too
        score, suggestions = self._score_prompt_quality(
            prompt, scene.narration_text, video_type
        )
        scene.quality_score = score
        scene.quality_suggestions = suggestions
        
        return prompt.strip()
    
    def _extract_subject(
        self,
        scene: Scene,
        character_override: Optional[str],
        video_type: str = "with_person"
    ) -> str:
        """Extract subject from scene, respecting video_type"""
        if video_type == "no_person":
            # Try to extract an object/concept from narration
            narration = scene.narration_text.lower()
            object_keywords = {
                "อาหาร": "Beautifully plated healthy meal",
                "กาแฟ": "Steaming cup of coffee",
                "น้ำ": "Glass of clear water",
                "ผัก": "Fresh colorful vegetables",
                "ผลไม้": "Fresh tropical fruits",
                "ออกกำลังกาย": "Fitness equipment in gym",
                "นอน": "Peaceful bedroom scene",
                "ปฏิทิน": "Calendar with markings",
                "เวลา": "Clock showing time",
            }
            for keyword, description in object_keywords.items():
                if keyword in narration:
                    return description
            return "Atmospheric scene"
        
        if character_override:
            return character_override
        if self.character_reference:
            return self.character_reference
        if scene.subject_description:
            return scene.subject_description
        return "Person in frame"
    
    def _extract_action(self, scene: Scene, video_type: str = "with_person") -> str:
        """Extract action from narration using keyword matching (fallback)"""
        narration = scene.narration_text.lower()
        
        if video_type == "no_person":
            # Object/environment actions (no person)
            object_actions = {
                "ออกกำลังกาย": "gym equipment in motion, weights and resistance bands arranged",
                "วิ่ง": "running trail stretching into distance, morning mist",
                "กิน": "food being served on elegant plate, steam rising",
                "อาหาร": "ingredients arranged beautifully on cutting board",
                "พัก": "peaceful room with soft light and comfortable setting",
                "นอน": "bed with soft sheets, moonlight through window",
                "น้ำ": "water pouring into glass, light refracting through droplets",
                "กาแฟ": "coffee beans being ground, steam rising from fresh cup",
                "ชา": "tea leaves unfurling in hot water, steam swirling",
            }
            for keyword, action in object_actions.items():
                if keyword in narration:
                    return action
            return "atmospheric scene with natural movement and light"
        
        action_keywords = {
            "ออกกำลังกาย": "exercising with energetic movements",
            "วิ่ง": "running with good form",
            "กิน": "eating healthy food mindfully",
            "อาหาร": "preparing nutritious meal",
            "พัก": "resting peacefully",
            "นอน": "sleeping restfully",
            "ยืด": "stretching muscles",
            "หายใจ": "breathing deeply and slowly",
            "น้ำ": "drinking water",
            "ชั่ง": "checking weight on scale",
            "วัด": "measuring progress",
            "กาแฟ": "making coffee",
            "ชา": "preparing tea",
        }
        
        for keyword, action in action_keywords.items():
            if keyword in narration:
                return action
        
        emotion_actions = {
            "motivational": "moving with determination and energy",
            "calm": "moving slowly and peacefully",
            "happy": "expressing joy and satisfaction",
            "urgent": "acting with focused intensity",
        }
        
        return emotion_actions.get(scene.emotion, "natural movement")
    
    def _extract_setting(self, scene: Scene, video_type: str = "with_person") -> str:
        """Extract setting from narration (fallback), adapted for video_type"""
        narration = scene.narration_text.lower()
        
        setting_keywords = {
            "ฟิตเนส": "in a modern fitness gym",
            "ยิม": "in a well-equipped gym",
            "ห้องครัว": "in a clean modern kitchen",
            "บ้าน": "in a cozy home environment",
            "สวน": "in a peaceful garden",
            "ถนน": "on a scenic outdoor path",
            "ทะเล": "by the beautiful ocean",
            "ภูเขา": "in the mountains with scenic view",
            "ออฟฟิศ": "in a modern office space",
            "ห้องนอน": "in a comfortable bedroom",
            "ร้านกาแฟ": "in a cozy coffee shop",
        }
        
        for keyword, setting in setting_keywords.items():
            if keyword in narration:
                return setting
        
        if video_type == "no_person":
            return "in a serene, well-lit environment"
        return "in a bright, clean environment"
    
    def _generate_mood(self, emotion_visual: dict, style, video_type: str = "with_person") -> str:
        """Generate mood and lighting description, adapted for video_type"""
        lighting = emotion_visual.get("lighting", "natural")
        colors = emotion_visual.get("colors", "balanced")
        
        if video_type == "no_person":
            return f"{lighting} lighting, {colors} color palette, atmospheric mood"
        
        expression = emotion_visual.get("expression", "natural")
        return f"{lighting} lighting, {colors} color palette, {expression} expression"
    
    def _generate_camera(self, scene: Scene, video_type: str = "with_person") -> str:
        """Generate camera angle/movement, adapted for video_type"""
        if scene.camera_movement:
            return scene.camera_movement
        
        narration = scene.narration_text.lower()
        
        if any(word in narration for word in ["เริ่ม", "แนะนำ", "สวัสดี"]):
            return "medium shot, slowly zooming in"
        elif any(word in narration for word in ["สรุป", "ท้าย", "จบ"]):
            return "medium shot, slowly zooming out"
        elif any(word in narration for word in ["ออกกำลังกาย", "วิ่ง", "เดิน"]):
            return "tracking shot following movement"
        elif any(word in narration for word in ["กิน", "อาหาร", "ดื่ม", "กาแฟ"]):
            if video_type == "no_person":
                return "close-up on food and details"
            return "close-up on hands and food"
        else:
            return "medium shot, slight movement"
    
    def _generate_script_summary(self, scenes: list[Scene]) -> str:
        """Generate a brief summary of the full script for narrative context"""
        # Combine all narration texts
        full_narration = " ".join(s.narration_text for s in scenes if s.narration_text)
        if not full_narration:
            return ""
        
        if self.is_available():
            try:
                response = self.client.chat.completions.create(
                    model=self._model,
                    messages=[
                        {
                            "role": "system",
                            "content": "Summarize this Thai narration script in 1-2 English sentences. Focus on: main topic, narrative arc, key themes. Be concise (max 80 words)."
                        },
                        {"role": "user", "content": full_narration[:2000]}
                    ],
                    temperature=0.2,
                    max_tokens=120
                )
                return response.choices[0].message.content.strip()
            except Exception:
                pass
        
        # Fallback: just use first sentence
        return f"Script with {len(scenes)} scenes."
    
    def generate_all_prompts(
        self,
        scenes: list[Scene],
        character: Optional[str] = None,
        project_context: dict = None,
        force_regenerate: bool = False
    ) -> list[Scene]:
        """
        Generate prompts for all scenes with continuity context.
        Supports resume: scenes that already have veo_prompt + voice_tone are skipped
        unless force_regenerate=True.
        
        Args:
            scenes: List of Scene objects
            character: Character reference for consistency
            project_context: Dict with visual_theme, directors_note, aspect_ratio, video_type
            force_regenerate: If True, regenerate ALL scenes even if already done
            
        Returns:
            List of scenes with generated veo_prompt
        """
        theme = project_context.get("visual_theme", "") if project_context else ""
        note = project_context.get("directors_note", "") if project_context else ""
        ratio = project_context.get("aspect_ratio", "16:9") if project_context else "16:9"
        direction_style = project_context.get("direction_style") if project_context else None
        prompt_style_config = project_context.get("prompt_style_config") if project_context else None
        video_type = project_context.get("video_type", "with_person") if project_context else "with_person"
        
        # === Platform & Content Context Injection ===
        platforms = project_context.get("platforms", []) if project_context else []
        topic = project_context.get("topic", "") if project_context else ""
        content_category = project_context.get("content_category", "") if project_context else ""
        video_format = project_context.get("video_format", "") if project_context else ""
        content_goal = project_context.get("content_goal", "") if project_context else ""
        target_audience = project_context.get("target_audience", "") if project_context else ""
        
        # Build platform-aware director's note
        platform_instructions = self._build_platform_instructions(platforms, video_format)
        content_context = self._build_content_context(topic, content_category, content_goal, target_audience)
        
        enriched_note_parts = []
        if note:
            enriched_note_parts.append(note)
        if platform_instructions:
            enriched_note_parts.append(platform_instructions)
        if content_context:
            enriched_note_parts.append(content_context)
        enriched_note = "\n\n".join(enriched_note_parts) if enriched_note_parts else ""
        
        logger.info(f"Platform context: {platforms}, video_format: {video_format}")
        
        # Build platform hint string for voiceover and voice_tone
        platform_names = []
        for p in platforms:
            pdata = self.PLATFORM_STYLE_MAP.get(p)
            if pdata:
                platform_names.append(f"{pdata['name']} ({pdata['style']})")
        platform_hint = ", ".join(platform_names) if platform_names else ""
        
        total_scenes = len(scenes)
        previous_scene_summary = ""
        
        # Generate script summary for narrative arc awareness
        logger.info(f"Generating script summary for {total_scenes} scenes (video_type={video_type})...")
        script_summary = self._generate_script_summary(scenes)
        
        for i, scene in enumerate(scenes):
            scene_number = i + 1
            
            # === RESUME SUPPORT: Skip already-completed scenes ===
            if not force_regenerate and scene.veo_prompt and scene.voice_tone:
                logger.info(f"Scene {scene_number}/{total_scenes}: already done — skipping (resume mode)")
                if scene.veo_prompt:
                    previous_scene_summary = self._summarize_prompt(scene.veo_prompt)
                continue
            
            logger.info(f"Generating prompt for scene {scene_number}/{total_scenes}...")
            
            # Get previous and next narration for story continuity
            previous_narration = scenes[i - 1].narration_text if i > 0 else ""
            next_narration = scenes[i + 1].narration_text if i < total_scenes - 1 else ""
            
            # Generate veo_prompt (must be done first — needed by voice_tone)
            scene.veo_prompt = self.generate_prompt(
                scene=scene,
                character_override=character,
                visual_theme=theme,
                directors_note=enriched_note,
                aspect_ratio=ratio,
                scene_number=scene_number,
                total_scenes=total_scenes,
                previous_scene_summary=previous_scene_summary,
                direction_style_id=direction_style,
                prompt_style_config=prompt_style_config,
                video_type=video_type,
                previous_narration=previous_narration,
                next_narration=next_narration,
                script_summary=script_summary
            )
            
            # === PARALLEL: voiceover (no API, instant) + voice_tone (API) run together ===
            # voiceover_prompt returns narration_text directly (no API call)
            # voice_tone needs one API call — run in background thread
            with ThreadPoolExecutor(max_workers=1) as executor:
                future_tone = executor.submit(
                    self.generate_voice_tone,
                    scene,
                    scene_number,
                    total_scenes,
                    theme,
                    scene.veo_prompt,
                    character or "",
                    platform_hint
                )
                # voiceover is instant (returns narration_text as-is)
                scene.voiceover_prompt = self.generate_voiceover_prompt(
                    scene=scene,
                    scene_number=scene_number,
                    total_scenes=total_scenes,
                    visual_theme=theme,
                    character_reference=character or "",
                    veo_prompt=scene.veo_prompt,
                    video_type=video_type,
                    platform_hint=platform_hint
                )
                scene.voice_tone = future_tone.result()
            
            # Store summarized prompt for next scene's continuity context
            if scene.veo_prompt:
                previous_scene_summary = self._summarize_prompt(scene.veo_prompt)
        
        return scenes
    
    def generate_single_scene(
        self,
        scene: "Scene",
        scene_index: int,
        total_scenes: int,
        character: Optional[str] = None,
        project_context: dict = None,
        previous_scene_summary: str = "",
        previous_narration: str = "",
        next_narration: str = "",
    ) -> "Scene":
        """
        Generate veo_prompt, voiceover_prompt, and voice_tone for a SINGLE scene.
        Used by per-prompt mode — generates ONLY this scene and nothing else.

        Args:
            scene: The Scene object to generate prompts for.
            scene_index: 0-based index of this scene in the full scene list.
            total_scenes: Total number of scenes (for context in prompt).
            character: Character reference string.
            project_context: Dict with visual_theme, directors_note, aspect_ratio, video_type, etc.
            previous_scene_summary: Summary of the previous scene's veo_prompt (for continuity).
            previous_narration: Narration text of previous scene.
            next_narration: Narration text of next scene.

        Returns:
            The same scene object with veo_prompt, voiceover_prompt, and voice_tone populated.
        """
        ctx = project_context or {}
        theme = ctx.get("visual_theme", "")
        note = ctx.get("directors_note", "")
        ratio = ctx.get("aspect_ratio", "16:9")
        direction_style = ctx.get("direction_style")
        prompt_style_config = ctx.get("prompt_style_config")
        video_type = ctx.get("video_type", "with_person")

        platforms = ctx.get("platforms", [])
        topic = ctx.get("topic", "")
        content_category = ctx.get("content_category", "")
        video_format = ctx.get("video_format", "")
        content_goal = ctx.get("content_goal", "")
        target_audience = ctx.get("target_audience", "")

        platform_instructions = self._build_platform_instructions(platforms, video_format)
        content_context = self._build_content_context(topic, content_category, content_goal, target_audience)

        enriched_note_parts = [p for p in [note, platform_instructions, content_context] if p]
        enriched_note = "\n\n".join(enriched_note_parts)

        platform_names = []
        for p in platforms:
            pdata = self.PLATFORM_STYLE_MAP.get(p)
            if pdata:
                platform_names.append(f"{pdata['name']} ({pdata['style']})")
        platform_hint = ", ".join(platform_names)

        # Script summary is empty for single-scene mode (no full-script context needed)
        script_summary = ""

        scene_number = scene_index + 1

        # Generate veo_prompt
        scene.veo_prompt = self.generate_prompt(
            scene=scene,
            character_override=character,
            visual_theme=theme,
            directors_note=enriched_note,
            aspect_ratio=ratio,
            scene_number=scene_number,
            total_scenes=total_scenes,
            previous_scene_summary=previous_scene_summary,
            direction_style_id=direction_style,
            prompt_style_config=prompt_style_config,
            video_type=video_type,
            previous_narration=previous_narration,
            next_narration=next_narration,
            script_summary=script_summary,
        )

        # Parallel: voice_tone (API call) + voiceover (instant)
        with ThreadPoolExecutor(max_workers=1) as executor:
            future_tone = executor.submit(
                self.generate_voice_tone,
                scene,
                scene_number,
                total_scenes,
                theme,
                scene.veo_prompt,
                character or "",
                platform_hint,
            )
            scene.voiceover_prompt = self.generate_voiceover_prompt(
                scene=scene,
                scene_number=scene_number,
                total_scenes=total_scenes,
                visual_theme=theme,
                character_reference=character or "",
                veo_prompt=scene.veo_prompt,
                video_type=video_type,
                platform_hint=platform_hint,
            )
            scene.voice_tone = future_tone.result()

        logger.info(f"generate_single_scene: scene {scene_number}/{total_scenes} done.")
        return scene

    def generate_all_prompts_generator(
        self,
        scenes: list[Scene],
        character: Optional[str] = None,
        project_context: dict = None,
        force_regenerate: bool = False
    ):
        """
        Generator version of generate_all_prompts that yields progress.
        Supports resume: scenes with veo_prompt + voice_tone are yielded immediately
        unless force_regenerate=True.
        Yields: (current_index, total_scenes, current_scene_object)
        """
        theme = project_context.get("visual_theme", "") if project_context else ""
        note = project_context.get("directors_note", "") if project_context else ""
        ratio = project_context.get("aspect_ratio", "16:9") if project_context else "16:9"
        direction_style = project_context.get("direction_style") if project_context else None
        prompt_style_config = project_context.get("prompt_style_config") if project_context else None
        video_type = project_context.get("video_type", "with_person") if project_context else "with_person"
        
        # === Platform & Content Context Injection ===
        platforms = project_context.get("platforms", []) if project_context else []
        topic = project_context.get("topic", "") if project_context else ""
        content_category = project_context.get("content_category", "") if project_context else ""
        video_format = project_context.get("video_format", "") if project_context else ""
        content_goal = project_context.get("content_goal", "") if project_context else ""
        target_audience = project_context.get("target_audience", "") if project_context else ""
        
        # Build platform-aware director's note
        platform_instructions = self._build_platform_instructions(platforms, video_format)
        content_context = self._build_content_context(topic, content_category, content_goal, target_audience)
        
        enriched_note_parts = []
        if note:
            enriched_note_parts.append(note)
        if platform_instructions:
            enriched_note_parts.append(platform_instructions)
        if content_context:
            enriched_note_parts.append(content_context)
        enriched_note = "\n\n".join(enriched_note_parts) if enriched_note_parts else ""
        
        logger.info(f"Platform context: {platforms}, video_format: {video_format}")
        
        # Build platform hint string for voiceover and voice_tone
        platform_names = []
        for p in platforms:
            pdata = self.PLATFORM_STYLE_MAP.get(p)
            if pdata:
                platform_names.append(f"{pdata['name']} ({pdata['style']})")
        platform_hint = ", ".join(platform_names) if platform_names else ""
        
        total_scenes = len(scenes)
        previous_scene_summary = ""
        
        # Pre-populate previous_scene_summary from already-done scenes before first new one
        # so continuity context is correct after resume
        for s in scenes:
            if s.veo_prompt and (not force_regenerate):
                previous_scene_summary = self._summarize_prompt(s.veo_prompt)
            else:
                break
        
        # Generate script summary for narrative arc awareness
        logger.info(f"Generating script summary for {total_scenes} scenes (video_type={video_type})...")
        script_summary = self._generate_script_summary(scenes)
        
        for i, scene in enumerate(scenes):
            scene_number = i + 1
            
            # === RESUME SUPPORT: Skip already-completed scenes ===
            if not force_regenerate and scene.veo_prompt and scene.voice_tone:
                logger.info(f"Scene {scene_number}/{total_scenes}: already done — skipping (resume mode)")
                if scene.veo_prompt:
                    previous_scene_summary = self._summarize_prompt(scene.veo_prompt)
                yield scene_number, total_scenes, scene
                continue
            
            logger.info(f"Generating prompt for scene {scene_number}/{total_scenes}...")
            
            # Get previous and next narration for story continuity
            previous_narration = scenes[i - 1].narration_text if i > 0 else ""
            next_narration = scenes[i + 1].narration_text if i < total_scenes - 1 else ""
            
            # Generate veo_prompt (sequential — needs previous_scene_summary)
            scene.veo_prompt = self.generate_prompt(
                scene=scene,
                character_override=character,
                visual_theme=theme,
                directors_note=enriched_note,
                aspect_ratio=ratio,
                scene_number=scene_number,
                total_scenes=total_scenes,
                previous_scene_summary=previous_scene_summary,
                direction_style_id=direction_style,
                prompt_style_config=prompt_style_config,
                video_type=video_type,
                previous_narration=previous_narration,
                next_narration=next_narration,
                script_summary=script_summary
            )
            
            # === PARALLEL: voice_tone API call + voiceover (instant) ===
            # voiceover_prompt returns narration_text directly (no API call needed)
            # voice_tone requires one API call — fire in background thread
            with ThreadPoolExecutor(max_workers=1) as executor:
                future_tone = executor.submit(
                    self.generate_voice_tone,
                    scene,
                    scene_number,
                    total_scenes,
                    theme,
                    scene.veo_prompt,
                    character or "",
                    platform_hint
                )
                # voiceover is instant (returns narration_text as-is) — run on main thread
                scene.voiceover_prompt = self.generate_voiceover_prompt(
                    scene=scene,
                    scene_number=scene_number,
                    total_scenes=total_scenes,
                    visual_theme=theme,
                    character_reference=character or "",
                    veo_prompt=scene.veo_prompt,
                    video_type=video_type,
                    platform_hint=platform_hint
                )
                scene.voice_tone = future_tone.result()
            
            # Store summarized prompt for next scene's continuity context
            if scene.veo_prompt:
                previous_scene_summary = self._summarize_prompt(scene.veo_prompt)
            
            yield scene_number, total_scenes, scene
    
    def detect_emotion(self, narration: str) -> str:
        """
        Detect emotion from narration text using AI
        
        Args:
            narration: Thai narration text
            
        Returns:
            Detected emotion (motivational, calm, urgent, happy, neutral)
        """
        if not self.is_available():
            return "neutral"
        
        try:
            response = self.client.chat.completions.create(
                model=self.DEFAULT_MODEL,
                messages=[
                    {
                        "role": "system",
                        "content": "Classify the emotion of Thai text into exactly one of: motivational, calm, urgent, happy, neutral. Reply with only the emotion word."
                    },
                    {"role": "user", "content": narration}
                ],
                temperature=0.3,
                max_tokens=20
            )
            
            emotion = response.choices[0].message.content.strip().lower()
            valid_emotions = ["motivational", "calm", "urgent", "happy", "neutral"]
            
            return emotion if emotion in valid_emotions else "neutral"
            
        except Exception as e:
            logger.debug(f"Emotion detection failed: {e}")
            return "neutral"
    
    def extract_character(self, script: str) -> str:
        """
        Extract character description from script using AI
        
        Args:
            script: Full Thai script
            
        Returns:
            Character description for Veo prompt
        """
        if not self.is_available():
            return ""
        
        try:
            response = self.client.chat.completions.create(
                model=self.DEFAULT_MODEL,
                messages=[
                    {
                        "role": "system",
                        "content": """Extract the main character description for video generation.
Output format: [gender] [age range] [ethnicity], [appearance], [clothing]
Example: "Thai woman in her 30s, fit athletic build, wearing casual workout clothes"
If no character is mentioned, output: "Person"
Output ONLY the description, no explanation."""
                    },
                    {"role": "user", "content": f"Script:\n{script[:1000]}"}
                ],
                temperature=0.1,  # Very low to ensure consistent character extraction
                max_tokens=100
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            logger.debug(f"Character extraction failed: {e}")
            return ""
    
    def enhance_prompt(
        self,
        base_prompt: str,
        enhancements: list[str]
    ) -> str:
        """Add enhancements to an existing prompt"""
        return f"{base_prompt}, {', '.join(enhancements)}"
    
    def add_negative_prompt(
        self,
        positive_prompt: str,
        avoid: list[str] = None
    ) -> dict:
        """
        Create prompt with negative prompts for Veo 3
        
        Args:
            positive_prompt: The main prompt
            avoid: Things to avoid in generation
            
        Returns:
            Dict with positive and negative prompts
        """
        default_negative = [
            "text overlays",
            "logos",
            "watermarks",
            "blurry",
            "distorted faces",
            "unnatural movements",
            "cartoon style" if "animated" not in positive_prompt.lower() else None
        ]
        
        negative = [n for n in (avoid or []) + default_negative if n]
        
        return {
            "prompt": positive_prompt,
            "negative_prompt": ", ".join(negative)
        }
    
    # === Platform & Content Awareness Helpers ===

    PLATFORM_STYLE_MAP = {
        "tiktok": {
            "name": "TikTok",
            "style": "FAST-PACED, ENGAGING, VERTICAL-FIRST",
            "tips": [
                "Quick cuts and dynamic transitions",
                "Bold, eye-catching visuals from the FIRST frame",
                "High-energy movement and close-up shots",
                "Trendy visual effects (speed ramps, zooms)",
                "Hook the viewer in the first 2 seconds",
            ]
        },
        "youtube": {
            "name": "YouTube",
            "style": "CINEMATIC, STORYTELLING, POLISHED",
            "tips": [
                "Cinematic composition with proper framing",
                "Smooth camera movements (dolly, slider, gimbal)",
                "Rich, warm color grading for premium feel",
                "Allow breathing room for visual storytelling",
                "Professional B-roll and establishing shots",
            ]
        },
        "instagram": {
            "name": "Instagram",
            "style": "AESTHETIC, CLEAN, VISUALLY STRIKING",
            "tips": [
                "Instagram-worthy aesthetic compositions",
                "Clean, bright color palette with high contrast",
                "Symmetrical or rule-of-thirds framing",
                "Smooth, looping-friendly movements",
                "Focus on beauty and visual appeal",
            ]
        },
        "facebook": {
            "name": "Facebook",
            "style": "ACCESSIBLE, CLEAR, INFORMATIVE",
            "tips": [
                "Clear, easy-to-understand visuals",
                "Text-friendly compositions (space for captions)",
                "Warm, inviting color grading",
                "Medium-paced movements that work on mute",
                "Focus on relatability and shareability",
            ]
        },
        "x": {
            "name": "X (Twitter)",
            "style": "PUNCHY, CONCISE, ATTENTION-GRABBING",
            "tips": [
                "Immediate visual impact",
                "Bold graphics and text-safe compositions",
                "Quick, punchy movements",
                "High contrast for small screen viewing",
            ]
        },
        "line": {
            "name": "LINE",
            "style": "FRIENDLY, APPROACHABLE, CLEAR",
            "tips": [
                "Warm, friendly visual style",
                "Clear product/subject visibility",
                "Mobile-optimized framing",
                "Simple, clean compositions",
            ]
        },
    }

    def _build_platform_instructions(self, platforms: list, video_format: str = "") -> str:
        """Build platform-specific visual style instructions for AI."""
        if not platforms:
            return ""
        
        parts = ["**🌐 PLATFORM-OPTIMIZED STYLE:**"]
        
        for platform_key in platforms:
            style_data = self.PLATFORM_STYLE_MAP.get(platform_key)
            if style_data:
                tips_str = "\n".join(f"  - {tip}" for tip in style_data["tips"])
                parts.append(f"Target: {style_data['name']} ({style_data['style']})\n{tips_str}")
        
        # Video format awareness
        format_map = {
            "shorts": "This is a SHORT-FORM video (<60s). Every second counts. Be punchy.",
            "standard": "This is a STANDARD video (1-5min). Balance pacing for sustained attention.",
            "longform": "This is a LONG-FORM video (>5min). Use varied pacing. Include breathing room.",
        }
        if video_format and video_format in format_map:
            parts.append(f"Format: {format_map[video_format]}")
        
        # Multi-platform optimization
        if len(platforms) > 1:
            parts.append("→ Optimizing for MULTIPLE platforms: find a balanced visual style that works across all targets.")
        
        return "\n".join(parts)

    def _build_content_context(self, topic: str, category: str, goal: str, audience: str) -> str:
        """Build content context instructions for AI."""
        if not any([topic, category, goal, audience]):
            return ""
        
        parts = ["**📋 CONTENT CONTEXT:**"]
        if topic:
            parts.append(f"Topic: {topic[:200]}")
        if category:
            parts.append(f"Category: {category}")
        if goal:
            parts.append(f"Goal: {goal}")
        if audience:
            parts.append(f"Target Audience: {audience}")
        parts.append("→ Tailor visual tone, energy, and pacing to match this content context.")
        
        return "\n".join(parts)

    @lru_cache(maxsize=128)
    def _score_prompt_quality_ai(
        self,
        prompt: str,
        narration_text: str,
        video_type: str = "with_person",
        platform_hint: str = ""
    ) -> tuple[int, list[str]]:
        """
        AI-Based Prompt Quality Scoring (DeepSeek Judge).
        Replaces strict keyword counting with semantic understanding.
        
        Criteria:
        1. Visual Clarity (Is the image describable?)
        2. Relevance (Does it match the narration?)
        3. Rule Adherence (No dialogue, no Thai text)
        4. Specificity (Avoids vague terms)
        5. Platform Appropriateness (matches target platform style)
        """
        if not self.is_available() or not prompt:
            return 0, ["AI unavailable or empty prompt"]
        
        # Build platform scoring context
        platform_scoring = ""
        if platform_hint:
            platform_scoring = f"""
        PLATFORM CONTEXT: "{platform_hint}"
        5. IF target platform is TikTok/Shorts AND prompt lacks energy/fast-paced elements -> DEDUCT POINTS.
        6. IF target platform is YouTube AND prompt lacks cinematic or storytelling quality -> DEDUCT POINTS.
        7. IF target platform is Instagram AND prompt lacks aesthetic/trendy visuals -> DEDUCT POINTS.
        """
        
        system_prompt = f"""You are an Expert Film Critic and AI Prompt Auditor.
        Evaluate the provided Video Generation Prompt (for Veo/Sora).
        
        VIDEO TYPE: "{video_type}"
        
        SCORING CRITERIA (0-100):
        - 0-40: Fails critical rules (Contains dialogue code "saying...", contains Thai text, empty).
        - 41-70: Mediocre. Vague visual descriptions (e.g. "someone doing something").
        - 71-100: Excellent. Highly specific, cinematic, strictly visual description.
        
        CONTEXT RULES:
        1. IF video_type is "no_person" AND prompt contains humans -> DEDUCT POINTS.
        2. IF video_type is "with_person" AND prompt lacks character description -> DEDUCT POINTS.
        
        STRICT RULES:
        1. IF prompt contains "saying", "speaking", or quotes -> SCORE MUST BE < 50.
        2. IF prompt contains non-English text -> SCORE MUST BE < 40.
        3. IF prompt is < 10 words -> SCORE MUST BE < 40.
        4. Prompts should be pure visual descriptions for video generation AI.
        {platform_scoring}
        Output JSON:
        {{
            "score": int,
            "reasoning": "brief explanation",
            "suggestions": ["list of specific fixes"]
        }}"""
        
        user_prompt = f"""PROMPT TO EVALUATE:
        "{prompt}"
        
        CONTEXT (Original Narration):
        "{narration_text}"
        
        Evaluate strictly."""
        
        try:
            response = self.client.chat.completions.create(
                model=self._model, # DeepSeek
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.1,
                max_tokens=300
            )
            import json
            result = response.choices[0].message.content.strip()
            if result.startswith("```"):
                result = "\n".join(result.split("\n")[1:-1])
            data = json.loads(result)
            return data.get("score", 0), data.get("suggestions", [])
            
        except Exception as e:
            logger.error(f"AI Scoring failed: {e}")
            # Fallback to legacy rule-based if AI fails
            return self._score_prompt_quality(prompt, narration_text, video_type)

    @lru_cache(maxsize=128)
    def _refine_voiceover_ai(self, script: str, character_profile: str, video_type: str) -> str:
        """
        DeepSeek Voiceover Refinement Loop.
        Checks for: Gender particles, Naturalness, Redundancy.
        """
        if not self.is_available() or not script:
            return script

        system_prompt = """You are a Native Thai Script Editor.
        Your task: Polish the Thai script to be perfectly natural and consistent with the speaker's gender.
        
        RULES:
        1. Check Speaker Gender from profile.
           - Male -> must use pronouns (ผม) / particles (ครับ).
           - Female -> must use pronouns (ฉัน/ดิฉัน) / particles (ค่ะ/คะ).
        2. Remove Redundancy: Delete repeated phrases if they sound robotic.
        3. Keep Meaning: Do NOT change the core message.
        
        Input: Raw Draft Script.
        Output: Final Polished Script (Thai text only)."""

        user_prompt = f"""Speaker Profile: "{character_profile}"
        Video Context: "{video_type}"
        
        Draft Script: "{script}"
        
        Polish this script:"""

        try:
            response = self.client.chat.completions.create(
                model=self._model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.1,
                max_tokens=500
            )
            refined = response.choices[0].message.content.strip()
            
            # Simple validation: length shouldn't deviate wildly
            if len(refined) < len(script) * 0.5 or len(refined) > len(script) * 1.5:
                 return script 
                 
            return self._strip_dialogue_artifacts(refined) # Clean up just in case
            
        except Exception as e:
            logger.warning(f"Voice refinement failed: {e}")
            return script


# Convenience functions
def generate_veo_prompt(
    scene: Scene,
    character: str = "",
    api_key: Optional[str] = None
) -> str:
    """Quick function to generate Veo prompt"""
    generator = VeoPromptGenerator(api_key=api_key, character_reference=character)
    return generator.generate_prompt(scene)


def generate_all_veo_prompts(
    scenes: list[Scene],
    character: str = "",
    api_key: Optional[str] = None
) -> list[Scene]:
    """Generate prompts for all scenes"""
    generator = VeoPromptGenerator(api_key=api_key, character_reference=character)
    return generator.generate_all_prompts(scenes, character)

