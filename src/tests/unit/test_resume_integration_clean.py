import asyncio
from unittest.mock import MagicMock, patch
from src.core.prompt_generator import VeoPromptGenerator
from src.core.models import Scene

def test_resume_and_parallel():
    generator = VeoPromptGenerator()
    
    # Mock the LLM calls to be fast and track calls
    generator.generate_prompt = MagicMock(return_value="Mocked Veo Prompt")
    generator.generate_voice_tone = MagicMock(return_value="Mocked Voice Tone")
    generator.generate_voiceover_prompt = MagicMock(return_value="Mocked Voiceover")
    
    scene1 = Scene(id="1", video_segment_id="v1", order=1, narration="Hello world", narration_text="Hello", translation="Hello", visual_context="A person waving")
    scene2 = Scene(id="2", video_segment_id="v2", order=2, narration="Bye world", narration_text="Bye", translation="Bye", visual_context="A person leaving")
    
    scenes = [scene1, scene2]
    char = "A test user"
    
    # 1. First run: Should generate for all scenes
    print("--- First Run ---")
    gen1 = generator.generate_all_prompts_generator(scenes, char, force_regenerate=False)
    for num, total, s in gen1:
        print(f"Generated Scene {num}/{total}: {s.veo_prompt[:10]}... | {s.voice_tone[:10]}...")
        
    assert generator.generate_prompt.call_count == 2, "generate_prompt should be called twice"
    assert generator.generate_voice_tone.call_count == 2, "generate_voice_tone should be called twice"
    
    # Reset mock counts
    generator.generate_prompt.reset_mock()
    generator.generate_voice_tone.reset_mock()
    
    # 2. Second run: Resume (force_regenerate=False). Should use existing prompts and NOT call API
    print("\\n--- Second Run (Resume) ---")
    gen2 = generator.generate_all_prompts_generator(scenes, char, force_regenerate=False)
    for num, total, s in gen2:
        print(f"Resumed Scene {num}/{total}: {s.veo_prompt[:10]}... | {s.voice_tone[:10]}...")
        
    assert generator.generate_prompt.call_count == 0, "generate_prompt should NOT be called on resume"
    assert generator.generate_voice_tone.call_count == 0, "generate_voice_tone should NOT be called on resume"
    
    # 3. Third run: Force Regenerate (force_regenerate=True). Should call API again.
    print("\\n--- Third Run (Force Regenerate) ---")
    gen3 = generator.generate_all_prompts_generator(scenes, char, force_regenerate=True)
    for num, total, s in gen3:
        print(f"Force Gen Scene {num}/{total}: {s.veo_prompt[:10]}... | {s.voice_tone[:10]}...")
        
    assert generator.generate_prompt.call_count == 2, "generate_prompt SHOULD be called on force_regenerate"
    assert generator.generate_voice_tone.call_count == 2, "generate_voice_tone SHOULD be called on force_regenerate"
    
    print("\\nAll tests passed successfully!")

if __name__ == "__main__":
    test_resume_and_parallel()
