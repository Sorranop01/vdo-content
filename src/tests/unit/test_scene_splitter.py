"""
Unit Tests for SceneSplitter
VDO Content V2 Test Suite
"""

import pytest
from core.scene_splitter import SceneSplitter, split_script
from core.models import Scene


class TestSceneSplitterInit:
    """Test SceneSplitter initialization"""
    
    def test_default_initialization(self):
        """Test default values"""
        splitter = SceneSplitter()
        assert splitter.max_duration == 8.0
        assert splitter.language == "th"
    
    def test_custom_initialization(self):
        """Test custom values"""
        splitter = SceneSplitter(max_duration=10.0, language="en")
        assert splitter.max_duration == 10.0
        assert splitter.language == "en"


class TestCalculateDuration:
    """Test duration calculation methods"""
    
    def test_thai_duration_calculation(self):
        """Test Thai text duration (10 chars/sec)"""
        splitter = SceneSplitter(language="th")
        # 50 characters (excluding spaces) = 5.0 seconds
        text = "ก" * 50
        duration = splitter.calculate_duration(text)
        assert duration == 5.0
    
    def test_thai_duration_ignores_spaces(self):
        """Test that spaces are not counted for Thai"""
        splitter = SceneSplitter(language="th")
        text = "ก ก ก ก ก"  # 5 chars + 4 spaces
        duration = splitter.calculate_duration(text)
        assert duration == 0.5  # Only 5 chars counted
    
    def test_english_duration_calculation(self):
        """Test English text duration (2.5 words/sec)"""
        splitter = SceneSplitter(language="en")
        # 10 words = 4.0 seconds
        text = "one two three four five six seven eight nine ten"
        duration = splitter.calculate_duration(text)
        assert duration == 4.0
    
    def test_empty_text_duration(self):
        """Test empty text returns zero"""
        splitter = SceneSplitter(language="th")
        assert splitter.calculate_duration("") == 0.0
        assert splitter.calculate_duration("   ") == 0.0


class TestCalculateMaxCharsWords:
    """Test max chars/words calculation"""
    
    def test_max_chars_default(self):
        """Test max chars for 8s (default)"""
        splitter = SceneSplitter()
        assert splitter.calculate_max_chars() == 80
    
    def test_max_chars_custom(self):
        """Test max chars for custom duration"""
        splitter = SceneSplitter(max_duration=10.0)
        assert splitter.calculate_max_chars() == 100
    
    def test_max_words_default(self):
        """Test max words for 8s (default)"""
        splitter = SceneSplitter()
        assert splitter.calculate_max_words() == 20
    
    def test_max_words_custom(self):
        """Test max words for custom duration"""
        splitter = SceneSplitter(max_duration=10.0)
        assert splitter.calculate_max_words() == 25


class TestSplitIntoSentences:
    """Test sentence splitting"""
    
    def test_split_on_newlines(self):
        """Test splitting on newlines"""
        splitter = SceneSplitter()
        text = "ประโยคแรก\nประโยคที่สอง\nประโยคที่สาม"
        sentences = splitter.split_into_sentences(text)
        assert len(sentences) == 3
    
    def test_split_on_periods(self):
        """Test splitting on periods"""
        splitter = SceneSplitter()
        text = "First sentence. Second sentence. Third sentence."
        sentences = splitter.split_into_sentences(text)
        assert len(sentences) == 3
    
    def test_split_on_question_marks(self):
        """Test splitting on question marks"""
        splitter = SceneSplitter()
        text = "What is this? Why is it here? How does it work?"
        sentences = splitter.split_into_sentences(text)
        assert len(sentences) == 3
    
    def test_empty_text_returns_empty_list(self):
        """Test empty text returns empty list"""
        splitter = SceneSplitter()
        assert splitter.split_into_sentences("") == []
        assert splitter.split_into_sentences("   ") == []
    
    def test_mixed_newlines_and_periods(self):
        """Test mixed delimiters"""
        splitter = SceneSplitter()
        text = "Line one. Line two.\nLine three! Line four?"
        sentences = splitter.split_into_sentences(text)
        assert len(sentences) == 4


class TestSplitScript:
    """Test main script splitting functionality"""
    
    def test_short_script_single_scene(self):
        """Test short script creates single scene"""
        splitter = SceneSplitter(language="th")
        # 40 chars = 4 seconds (under 8s limit)
        script = "ก" * 40
        scenes = splitter.split_script(script)
        assert len(scenes) == 1
        assert scenes[0].order == 1
    
    def test_long_script_multiple_scenes(self):
        """Test long script creates multiple scenes"""
        splitter = SceneSplitter(language="th")
        # Create script that will need multiple scenes
        # Each sentence is ~30 chars, 3 sentences = 9s > 8s limit
        script = "ประโยคแรกที่ยาวมากๆๆๆๆๆๆๆๆๆๆ\nประโยคที่สองที่ยาวมากๆๆๆๆๆๆๆ\nประโยคที่สามที่ยาวมากๆๆๆๆ"
        scenes = splitter.split_script(script)
        assert len(scenes) >= 2
    
    def test_scene_order_increments(self):
        """Test scene order increments correctly"""
        splitter = SceneSplitter(language="th")
        script = "ก" * 100 + "\n" + "ข" * 100  # Forces split
        scenes = splitter.split_script(script)
        for i, scene in enumerate(scenes, 1):
            assert scene.order == i
    
    def test_default_emotion_and_style(self):
        """Test default emotion and style are applied"""
        splitter = SceneSplitter()
        scenes = splitter.split_script("Test", default_emotion="happy", default_style="documentary")
        assert scenes[0].emotion == "happy"
        assert scenes[0].visual_style == "documentary"
    
    def test_empty_script_returns_empty_list(self):
        """Test empty script returns empty list"""
        splitter = SceneSplitter()
        scenes = splitter.split_script("")
        assert scenes == []
    
    def test_scene_has_estimated_duration(self):
        """Test each scene has estimated_duration set"""
        splitter = SceneSplitter()
        scenes = splitter.split_script("This is a test sentence")
        for scene in scenes:
            assert scene.estimated_duration > 0
    
    def test_scene_has_word_count(self):
        """Test each scene has word_count set"""
        splitter = SceneSplitter()
        scenes = splitter.split_script("One two three four five")
        assert scenes[0].word_count == 5


class TestMergeScenes:
    """Test scene merging"""
    
    def test_merge_short_scenes(self):
        """Test merging two short scenes"""
        splitter = SceneSplitter(language="th")
        scene1 = Scene(order=1, narration_text="ก" * 30, start_time=0, end_time=3)
        scene2 = Scene(order=2, narration_text="ข" * 30, start_time=3, end_time=6)
        
        merged = splitter.merge_scenes(scene1, scene2)
        assert merged is not None
        assert scene1.narration_text in merged.narration_text
        assert scene2.narration_text in merged.narration_text
    
    def test_cannot_merge_long_scenes(self):
        """Test merging returns None if too long"""
        splitter = SceneSplitter(language="th", max_duration=5.0)
        scene1 = Scene(order=1, narration_text="ก" * 40, start_time=0, end_time=4)  # 4s
        scene2 = Scene(order=2, narration_text="ข" * 40, start_time=4, end_time=8)  # 4s
        
        merged = splitter.merge_scenes(scene1, scene2)
        assert merged is None  # Combined 8s > 5s limit
    
    def test_merged_scene_keeps_first_order(self):
        """Test merged scene keeps first scene's order"""
        splitter = SceneSplitter(language="th")
        scene1 = Scene(order=5, narration_text="ก" * 20, start_time=0, end_time=2)
        scene2 = Scene(order=6, narration_text="ข" * 20, start_time=2, end_time=4)
        
        merged = splitter.merge_scenes(scene1, scene2)
        assert merged.order == 5


class TestSplitScene:
    """Test splitting a single scene"""
    
    def test_short_scene_unchanged(self):
        """Test short scene returns as-is"""
        splitter = SceneSplitter()
        scene = Scene(order=1, narration_text="Short text", start_time=0, end_time=2)
        scene.estimated_duration = 2.0
        
        result = splitter.split_scene(scene)
        assert len(result) == 1
    
    def test_long_scene_gets_split(self):
        """Test long scene gets split into multiple"""
        splitter = SceneSplitter(language="th", max_duration=5.0)
        # Create scene with text that would be ~10 seconds with sentence delimiters
        # split_scene uses split_script internally, which splits on sentence boundaries
        scene = Scene(order=1, narration_text="ก" * 50 + "\n" + "ข" * 50, start_time=0, end_time=10)
        scene.estimated_duration = 10.0
        
        result = splitter.split_scene(scene)
        assert len(result) >= 2


class TestReorderScenes:
    """Test scene reordering"""
    
    def test_reorder_updates_all_orders(self):
        """Test reordering updates all scene orders"""
        splitter = SceneSplitter()
        scenes = [
            Scene(order=5, narration_text="First", start_time=0, end_time=1),
            Scene(order=10, narration_text="Second", start_time=1, end_time=2),
            Scene(order=15, narration_text="Third", start_time=2, end_time=3),
        ]
        
        reordered = splitter.reorder_scenes(scenes)
        assert [s.order for s in reordered] == [1, 2, 3]
    
    def test_reorder_empty_list(self):
        """Test reordering empty list"""
        splitter = SceneSplitter()
        assert splitter.reorder_scenes([]) == []


class TestGetStats:
    """Test statistics calculation"""
    
    def test_stats_with_scenes(self, sample_scenes):
        """Test stats calculation with scenes"""
        splitter = SceneSplitter()
        # Set estimated_duration for test
        for scene in sample_scenes:
            scene.estimated_duration = 5.0
            scene.word_count = 10
        
        stats = splitter.get_stats(sample_scenes)
        
        assert stats["total_scenes"] == 3
        assert stats["total_duration"] == 15.0
        assert stats["avg_duration"] == 5.0
        assert stats["min_duration"] == 5.0
        assert stats["max_duration"] == 5.0
        assert stats["total_words"] == 30
    
    def test_stats_empty_list(self):
        """Test stats with empty list"""
        splitter = SceneSplitter()
        stats = splitter.get_stats([])
        
        assert stats["total_scenes"] == 0
        assert stats["total_duration"] == 0
        assert stats["avg_duration"] == 0


class TestConvenienceFunction:
    """Test module-level convenience function"""
    
    def test_split_script_function(self):
        """Test split_script convenience function"""
        scenes = split_script("Test sentence one. Test sentence two.", max_duration=8.0, language="en")
        assert isinstance(scenes, list)
        assert len(scenes) >= 1
    
    def test_split_script_function_thai(self):
        """Test split_script with Thai"""
        scenes = split_script("ประโยคภาษาไทย", max_duration=8.0, language="th")
        assert isinstance(scenes, list)
        assert len(scenes) >= 1
