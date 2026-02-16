import sys
import os
from unittest.mock import MagicMock, patch

# Add src to path
sys.path.append(os.getcwd())

from src.core.transcriber import AudioTranscriber, TranscriptSegment

def test_segmentation():
    print("Testing Audio Segmentation Logic...")
    
    # Mock WhisperModel
    mock_model = MagicMock()
    
    # Create valid segments representing a long audio (20s) in one chunk
    # emulate faster_whisper segment
    Segment = MagicMock()
    Segment.start = 0.0
    Segment.end = 20.0
    Segment.text = "This is a very long sentence that should be split into multiple parts because it exceeds the eight second limit imposed by the video generation model."
    Segment.avg_logprob = -0.5
    
    # Mock transcribe return
    mock_model.transcribe.return_value = ([Segment], None)
    
    # Initialize transcriber with mocked availability
    with patch("src.core.transcriber.WHISPER_AVAILABLE", True):
        with patch("src.core.transcriber.WhisperModel", return_value=mock_model):
            transcriber = AudioTranscriber()
            
            # Mock file existence check
            with patch("os.path.exists", return_value=True):
                # Run transcribe with split_to_scenes=True
                result = transcriber.transcribe(
                    "dummy.mp3", 
                    language="en", 
                    split_to_scenes=True
                )
                
                print(f"\nOriginal Duration: 20.0s")
                print(f"Result Segments: {len(result)}")
                
                for i, seg in enumerate(result):
                    duration = seg.end - seg.start
                    print(f"  Segment {i+1}: {seg.start:.1f}s - {seg.end:.1f}s ({duration:.1f}s) | Text: {seg.text[:20]}...")
                    
                    if duration > 8.0:
                        print(f"❌ FAILED: Segment {i+1} exceeds 8s limit!")
                        sys.exit(1)
                
                if len(result) < 3:
                    print("❌ FAILED: Did not split 20s audio into enough parts (expected >= 3)")
                    sys.exit(1)
                    
                print("\n✅ SUCCESS: Segmentation logic works correctly (< 8s per segment)")

if __name__ == "__main__":
    test_segmentation()
