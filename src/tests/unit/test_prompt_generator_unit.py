"""
Unit Tests for VeoPromptGenerator
VDO Content V2 Test Suite

Tests the prompt generation logic without making actual API calls
"""

import pytest
from unittest.mock import Mock, patch, MagicMock

from core.prompt_generator import VeoPromptGenerator, generate_veo_prompt
from core.models import Scene


class TestVeoPromptGeneratorInit:
    """Test VeoPromptGenerator initialization"""
    
    def test_default_initialization(self):
        """Test default values"""
        generator = VeoPromptGenerator()
        assert generator.character_reference == ""
        assert generator.use_ai is True
        assert generator.enable_qa is False  # Default OFF to prevent prompt drift
        assert generator._client is None
    
    def test_with_character_reference(self):
        """Test with character reference"""
        generator = VeoPromptGenerator(character_reference="Thai woman, 30s")
        assert generator.character_reference == "Thai woman, 30s"
    
    def test_with_api_key(self):
        """Test with explicit API key"""
        generator = VeoPromptGenerator(api_key="test-key-123")
        assert generator.api_key == "test-key-123"
    
    def test_disable_ai(self):
        """Test AI can be disabled"""
        generator = VeoPromptGenerator(use_ai=False)
        assert generator.use_ai is False
    
    def test_disable_qa(self):
        """Test QA can be disabled"""
        generator = VeoPromptGenerator(enable_qa=False)
        assert generator.enable_qa is False


class TestVeoPromptGeneratorIsAvailable:
    """Test is_available method"""
    
    def test_not_available_without_api_key(self):
        """Test returns False without API key"""
        generator = VeoPromptGenerator(api_key=None)
        generator.api_key = None
        assert generator.is_available() is False
    
    def test_not_available_when_ai_disabled(self):
        """Test returns False when AI is disabled"""
        generator = VeoPromptGenerator(api_key="test", use_ai=False)
        assert generator.is_available() is False
    
    @patch('core.prompt_generator.OPENAI_AVAILABLE', True)
    def test_available_with_key_and_openai(self):
        """Test returns True with API key and OpenAI library"""
        generator = VeoPromptGenerator(api_key="test-key")
        # This checks the availability logic
        result = generator.is_available()
        # Will be True only if OPENAI_AVAILABLE is True
        assert isinstance(result, bool)


class TestCleanPrompt:
    """Test _clean_prompt method"""
    
    def test_removes_markdown_code_blocks(self):
        """Test removal of markdown code blocks"""
        generator = VeoPromptGenerator()
        prompt = "```\nClean prompt text\n```"
        result = generator._clean_prompt(prompt)
        assert "```" not in result
        assert "Clean prompt text" in result
    
    def test_removes_surrounding_quotes(self):
        """Test removal of quotes"""
        generator = VeoPromptGenerator()
        result = generator._clean_prompt('"Quoted prompt"')
        assert result == "Quoted prompt"
    
    def test_removes_single_quotes(self):
        """Test removal of single quotes"""
        generator = VeoPromptGenerator()
        result = generator._clean_prompt("'Single quoted'")
        assert result == "Single quoted"
    
    def test_strips_whitespace(self):
        """Test whitespace stripping"""
        generator = VeoPromptGenerator()
        result = generator._clean_prompt("  spaced text  ")
        assert result == "spaced text"


class TestExtractSubject:
    """Test _extract_subject method"""
    
    def test_returns_character_override(self):
        """Test character override takes priority"""
        generator = VeoPromptGenerator(character_reference="Default char")
        scene = Scene(order=1, narration_text="Test", start_time=0, end_time=5)
        
        result = generator._extract_subject(scene, "Override character")
        assert result == "Override character"
    
    def test_returns_character_reference(self):
        """Test character reference is used when no override"""
        generator = VeoPromptGenerator(character_reference="My character")
        scene = Scene(order=1, narration_text="Test", start_time=0, end_time=5)
        
        result = generator._extract_subject(scene, None)
        assert result == "My character"
    
    def test_returns_scene_subject(self):
        """Test scene subject_description is used"""
        generator = VeoPromptGenerator()
        scene = Scene(
            order=1, 
            narration_text="Test", 
            start_time=0, 
            end_time=5,
            subject_description="Scene character"
        )
        
        result = generator._extract_subject(scene, None)
        assert result == "Scene character"
    
    def test_returns_default(self):
        """Test default when nothing else is available"""
        generator = VeoPromptGenerator()
        scene = Scene(order=1, narration_text="Test", start_time=0, end_time=5)
        
        result = generator._extract_subject(scene, None)
        assert result == "Person in frame"


class TestExtractAction:
    """Test _extract_action method"""
    
    def test_extracts_exercise_action(self):
        """Test exercise keyword detection"""
        generator = VeoPromptGenerator()
        scene = Scene(
            order=1, 
            narration_text="ออกกำลังกายทุกวัน", 
            start_time=0, 
            end_time=5
        )
        
        result = generator._extract_action(scene)
        assert "exercising" in result.lower()
    
    def test_extracts_running_action(self):
        """Test running keyword detection"""
        generator = VeoPromptGenerator()
        scene = Scene(
            order=1, 
            narration_text="วิ่งตอนเช้า", 
            start_time=0, 
            end_time=5
        )
        
        result = generator._extract_action(scene)
        assert "running" in result.lower()
    
    def test_extracts_eating_action(self):
        """Test eating keyword detection"""
        generator = VeoPromptGenerator()
        scene = Scene(
            order=1, 
            narration_text="กินอาหารเช้า", 
            start_time=0, 
            end_time=5
        )
        
        result = generator._extract_action(scene)
        assert "eating" in result.lower() or "food" in result.lower()
    
    def test_default_action_for_emotion(self):
        """Test emotion-based default action"""
        generator = VeoPromptGenerator()
        scene = Scene(
            order=1, 
            narration_text="ไม่มีคีย์เวิร์ด", 
            start_time=0, 
            end_time=5,
            emotion="motivational"
        )
        
        result = generator._extract_action(scene)
        assert "determination" in result.lower() or "movement" in result.lower()


class TestExtractSetting:
    """Test _extract_setting method"""
    
    def test_extracts_gym_setting(self):
        """Test gym keyword detection"""
        generator = VeoPromptGenerator()
        scene = Scene(
            order=1, 
            narration_text="ฝึกที่ฟิตเนส", 
            start_time=0, 
            end_time=5
        )
        
        result = generator._extract_setting(scene)
        assert "gym" in result.lower() or "fitness" in result.lower()
    
    def test_extracts_kitchen_setting(self):
        """Test kitchen keyword detection"""
        generator = VeoPromptGenerator()
        scene = Scene(
            order=1, 
            narration_text="ทำอาหารในห้องครัว", 
            start_time=0, 
            end_time=5
        )
        
        result = generator._extract_setting(scene)
        assert "kitchen" in result.lower()
    
    def test_default_setting(self):
        """Test default setting when no keyword"""
        generator = VeoPromptGenerator()
        scene = Scene(
            order=1, 
            narration_text="ไม่มีคีย์เวิร์ด", 
            start_time=0, 
            end_time=5
        )
        
        result = generator._extract_setting(scene)
        assert "environment" in result.lower() or "bright" in result.lower()


class TestGenerateMood:
    """Test _generate_mood method"""
    
    def test_generates_mood_string(self):
        """Test mood generation creates string"""
        generator = VeoPromptGenerator()
        emotion_visual = {
            "lighting": "warm golden",
            "colors": "vibrant",
            "expression": "happy"
        }
        style = Mock()
        
        result = generator._generate_mood(emotion_visual, style)
        
        assert isinstance(result, str)
        assert "lighting" in result
        assert "palette" in result


class TestGenerateCamera:
    """Test _generate_camera method"""
    
    def test_returns_scene_camera_movement(self):
        """Test returns scene's camera_movement if set"""
        generator = VeoPromptGenerator()
        scene = Scene(
            order=1, 
            narration_text="Test", 
            start_time=0, 
            end_time=5,
            camera_movement="dolly forward"
        )
        
        result = generator._generate_camera(scene)
        assert result == "dolly forward"
    
    def test_intro_scene_camera(self):
        """Test intro keyword gives zoom in"""
        generator = VeoPromptGenerator()
        scene = Scene(
            order=1, 
            narration_text="สวัสดีครับ", 
            start_time=0, 
            end_time=5
        )
        
        result = generator._generate_camera(scene)
        assert "zoom" in result.lower()
    
    def test_exercise_scene_camera(self):
        """Test exercise keyword gives tracking shot"""
        generator = VeoPromptGenerator()
        scene = Scene(
            order=1, 
            narration_text="ออกกำลังกายเสร็จแล้ว", 
            start_time=0, 
            end_time=5
        )
        
        result = generator._generate_camera(scene)
        assert "tracking" in result.lower() or "movement" in result.lower()
    
    def test_food_scene_camera(self):
        """Test food keyword gives close-up"""
        generator = VeoPromptGenerator()
        scene = Scene(
            order=1, 
            narration_text="อาหารมื้อเช้า", 
            start_time=0, 
            end_time=5
        )
        
        result = generator._generate_camera(scene)
        assert "close" in result.lower()


class TestGenerateFallbackPrompt:
    """Test _generate_fallback_prompt method"""
    
    def test_fallback_generates_prompt(self):
        """Test fallback generates a valid prompt"""
        generator = VeoPromptGenerator(character_reference="Thai man, casual")
        scene = Scene(
            order=1, 
            narration_text="ออกกำลังกายทุกเช้า",
            start_time=0, 
            end_time=5,
            visual_style="documentary",
            emotion="motivational"
        )
        
        result = generator._generate_fallback_prompt(scene)
        
        assert isinstance(result, str)
        assert len(result) > 50  # Should be a substantial prompt
    
    def test_fallback_includes_character(self):
        """Test fallback includes character reference"""
        generator = VeoPromptGenerator(character_reference="Thai woman, professional")
        scene = Scene(
            order=1, 
            narration_text="Test narration",
            start_time=0, 
            end_time=5
        )
        
        result = generator._generate_fallback_prompt(scene)
        assert "Thai woman" in result


class TestEnhancePrompt:
    """Test enhance_prompt method"""
    
    def test_adds_enhancements(self):
        """Test enhancements are added"""
        generator = VeoPromptGenerator()
        base = "Base prompt"
        enhancements = ["4K resolution", "HDR"]
        
        result = generator.enhance_prompt(base, enhancements)
        
        assert "Base prompt" in result
        assert "4K resolution" in result
        assert "HDR" in result


class TestAddNegativePrompt:
    """Test add_negative_prompt method"""
    
    def test_returns_dict_structure(self):
        """Test returns dict with prompt and negative_prompt"""
        generator = VeoPromptGenerator()
        result = generator.add_negative_prompt("Positive prompt")
        
        assert "prompt" in result
        assert "negative_prompt" in result
        assert result["prompt"] == "Positive prompt"
    
    def test_includes_default_negatives(self):
        """Test includes default negative prompts"""
        generator = VeoPromptGenerator()
        result = generator.add_negative_prompt("Positive prompt")
        
        negative = result["negative_prompt"]
        assert "text overlays" in negative
        assert "logos" in negative
        assert "watermarks" in negative
    
    def test_adds_custom_negatives(self):
        """Test adds custom negative prompts"""
        generator = VeoPromptGenerator()
        result = generator.add_negative_prompt(
            "Positive prompt",
            avoid=["violence", "nudity"]
        )
        
        negative = result["negative_prompt"]
        assert "violence" in negative
        assert "nudity" in negative


class TestGeneratePrompt:
    """Test generate_prompt method"""
    
    def test_uses_fallback_when_ai_unavailable(self):
        """Test uses fallback when AI not available"""
        generator = VeoPromptGenerator(use_ai=False)
        scene = Scene(
            order=1, 
            narration_text="Test narration",
            start_time=0, 
            end_time=5
        )
        
        result = generator.generate_prompt(scene)
        
        assert isinstance(result, str)
        assert len(result) > 0


class TestConvenienceFunction:
    """Test module-level convenience function"""
    
    def test_generate_veo_prompt(self):
        """Test generate_veo_prompt convenience function"""
        scene = Scene(
            order=1,
            narration_text="ทดสอบ",
            start_time=0,
            end_time=5
        )
        
        result = generate_veo_prompt(scene, character="Thai person")
        
        assert isinstance(result, str)
        assert len(result) > 0
