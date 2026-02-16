import sys
import os
from unittest.mock import MagicMock, patch
from contextlib import contextmanager

# Add src to path
sys.path.append(os.getcwd())

# --- IMPROVED MOCK SETUP ---
# Create a main mock for streamlit
mock_st = MagicMock()

# Configure context managers
@contextmanager
def mock_context(*args, **kwargs):
    yield [MagicMock() for _ in range(10)] # Return list for columns

mock_st.columns = MagicMock(side_effect=mock_context)
mock_st.expander = MagicMock(side_effect=mock_context)
mock_st.spinner = MagicMock(side_effect=mock_context)
mock_st.container = MagicMock(side_effect=mock_context)
mock_st.form = MagicMock(side_effect=mock_context)

# Mock components submodule
mock_components = MagicMock()
sys.modules["streamlit.components.v1"] = mock_components

# Mock session state
mock_session_state = MagicMock()
mock_st.session_state = mock_session_state

# Apply the mock to sys.modules
sys.modules["streamlit"] = mock_st

# --- END MOCK SETUP ---

# Now import the modules under test
from src.frontend.pages import step3_script
from src.core.models import Project

def test_ui_logic():
    print("Testing Step 3 UI Logic...")
    
    # Setup Mock Project
    project = Project(
        project_id="test_project_123",
        title="Test Project",
        audio_path="/tmp/test_audio.mp3",
        status="step3_script"
    )
    
    # Setup Session State
    mock_st.session_state.current_project = project
    mock_st.session_state.page = 2
    mock_st.session_state.get.return_value = "dummy_api_key" # For API key check
    
    # Mock helpers
    step3_script.show_step_guard = MagicMock(return_value=True)
    step3_script.check_step_requirements = MagicMock(return_value=(True, ""))
    step3_script._show_step2_context = MagicMock()
    step3_script._build_script_context = MagicMock(return_value="Context")
    
    # Mock file existence
    with patch("os.path.exists", return_value=True):
        # Mock Transcriber availability
        with patch("src.frontend.pages.step3_script.TRANSCRIPTION_AVAILABLE", True):
            # Mock Transcriber class
            mock_transcriber_class = MagicMock()
            mock_transcriber_instance = MagicMock()
            mock_transcriber_class.return_value = mock_transcriber_instance
            
            # Mock Transcriber result
            # Return a dict as expected by the code (not an object)
            mock_result = {
                "segments": [
                    MagicMock(start=0, end=5, text="Hello"),
                    MagicMock(start=5, end=8, text="World")
                ],
                "full_text": "Hello World",
                "total_duration": 8.0
            }
            mock_transcriber_instance.transcribe_with_summary.return_value = mock_result
            
            with patch("src.frontend.pages.step3_script.AudioTranscriber", mock_transcriber_class):
                # --- TEST ---
                
                # Configure button mock to return True when "เริ่มซอย" is in the label
                def button_side_effect(label, **kwargs):
                    if "เริ่มซอย" in label:
                        return True
                    return False
                mock_st.button.side_effect = button_side_effect
                
                print("\n--- Simulating 'Split' button click ---")
                
                # Run render
                try:
                    step3_script.render()
                except Exception as e:
                    # Ignore rerun exception as it's expected
                    if "RerunData" not in str(e) and "rerun" not in str(e):
                        print(f"❌ Unexpected error during render: {e}")
                        import traceback
                        traceback.print_exc()
                        sys.exit(1)
                
                # Verification
                # 1. Check Model Initialization
                if mock_transcriber_class.called:
                    args, kwargs = mock_transcriber_class.call_args
                    print(f"✅ AudioTranscriber init called with: {kwargs}")
                    if kwargs.get("model_size") != "small":
                        print(f"❌ Expected model_size='small', got '{kwargs.get('model_size')}'")
                        sys.exit(1)
                else:
                    print("❌ AudioTranscriber NOT initialized!")
                    sys.exit(1)

                # 2. Check Transcribe Call
                if mock_transcriber_instance.transcribe_with_summary.called:
                    print("✅ Transcriber was called!")
                    args, kwargs = mock_transcriber_instance.transcribe_with_summary.call_args
                    print(f"   Called with kwargs: {kwargs}")
                    
                    if "initial_prompt" not in kwargs or not kwargs["initial_prompt"]:
                        print("❌ 'initial_prompt' missing or empty!")
                        sys.exit(1)
                        
                    if "ภาษาไทย" not in kwargs["initial_prompt"]:
                        print(f"❌ 'initial_prompt' does not contain Thai keywords. Got: {kwargs['initial_prompt'][:20]}...")
                        sys.exit(1)
                else:
                    print("❌ Transcriber was NOT called!")
                    # Debug: print button calls
                    print("Button calls:", mock_st.button.call_args_list)
                    sys.exit(1)
                    
                # Check if project was updated
                # Note: We can't easily check 'project' object update because of how mocks might handle assignment,
                # but we can check if auto_save_project was called which implies state update flow reached
                
                if step3_script.auto_save_project.called:
                     print("✅ auto_save_project called (Success flow reached)")
                else:
                     # It might not be called if we mock it?
                     pass

                # Check if project.audio_segments was set
                if project.audio_segments:
                     print(f"✅ Project segments updated: {len(project.audio_segments)} segments")
                else:
                     print(f"❌ Project segments NOT updated. Count: {len(project.audio_segments)}")
                     sys.exit(1)

                print("\n✅ UI Logic Verified: Button click triggers segmentation.")

if __name__ == "__main__":
    test_ui_logic()
