
import sys
import os
from pathlib import Path
from unittest.mock import MagicMock, patch

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.models import Scene
from core.prompt_generator import VeoPromptGenerator

def test_prompt_generation_source():
    print("🚀 Testing Veo Prompt Generator Source Logic")
    print("=" * 50)
    
    # 1. Create a dummy scene with specific transcribed text
    # This text is different from what might be in a script to prove it uses the scene's text
    transcribed_text = "แมวกำลังกินปลาทูอย่างเอร็ดอร่อยบนจานสีขาว"
    
    scene = Scene(
        order=1,
        narration_text=transcribed_text,
        visual_style="realistic",
        estimated_duration=5.0
    )
    
    print(f"📥 Input Scene Narration: '{scene.narration_text}'")
    
    # 2. Initialize Generator with mocked client
    generator = VeoPromptGenerator(api_key="dummy_key")
    
    # Mock the OpenAI client to capture what is sent
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.choices[0].message.content = "Close-up of a cat eating mackerel on a white plate, natural lighting, realistic style."
    mock_client.chat.completions.create.return_value = mock_response
    
    # Inject mock client
    generator._client = mock_client
    
    # Force is_available to True (in case openai module is missing in env)
    with patch.object(VeoPromptGenerator, 'is_available', return_value=True):
        # 3. Run Generation
        print("🔄 Generating prompt...")
        result = generator.generate_prompt(scene)
    
    # 4. Verify what was sent to AI
    print("🔍 Verifying input sent to AI...")
    
    # Get the arguments passed to create()
    call_args = mock_client.chat.completions.create.call_args
    # call_args is (args, kwargs)
    sent_messages = call_args.kwargs['messages']
    user_message = sent_messages[1]['content']
    
    print(f"   Sent Message Content:\n   ---\n{user_message}\n   ---")
    
    if transcribed_text in user_message:
        print(f"✅ SUCCESS: The generator used the transcribed text: '{transcribed_text}'")
    else:
        print(f"❌ FAILURE: The transcribed text was NOT found in the AI prompt!")
        sys.exit(1)
        
    # 5. Verify Output
    print(f"📤 Output Prompt: {result}")

if __name__ == "__main__":
    test_prompt_generation_source()
