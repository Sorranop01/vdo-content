import sys
import os
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.transcriber import AudioTranscriber, TranscriptSegment

def test_scene_optimization():
    print("Testing Scene Optimization Logic...")
    
    # Initialize transcriber (mocking model to avoid loading)
    transcriber = AudioTranscriber(model_size="base")
    # We don't need the actual model for this test, just the logic method
    
    # Test Case 1: Simple segments that fit
    segments = [
        TranscriptSegment(0.0, 3.0, "สวัสดีครับ"),
        TranscriptSegment(3.0, 6.0, "วันนี้เราจะมาคุยกัน"),
        TranscriptSegment(6.0, 10.0, "เรื่องสุขภาพ") # This ends at 10.0, so duration from 0 is > 8
    ]
    
    print("\n--- Test Case 1: Merging small segments ---")
    optimized = transcriber._optimize_for_scenes(segments)
    for i, seg in enumerate(optimized):
        duration = seg.end - seg.start
        print(f"Segment {i+1}: {seg.start}-{seg.end} ({duration}s) - {seg.text}")
        assert duration <= 8.0, f"Segment {i+1} duration {duration}s exceeds 8s"
    
    # Test Case 2: Long segment that needs splitting (Thai)
    # 12 seconds of text
    long_segment = TranscriptSegment(0.0, 12.0, "นี่คือประโยคที่ยาวมากและไม่มีช่องว่างให้ตัดเลยจริงๆนะเนี่ยยาวมากๆเลยครับพี่น้องครับยาวจริงๆนะ")
    
    print("\n--- Test Case 2: Splitting long Thai segment ---")
    optimized_long = transcriber._optimize_for_scenes([long_segment])
    for i, seg in enumerate(optimized_long):
        duration = seg.end - seg.start
        print(f"Segment {i+1}: {seg.start}-{seg.end} ({duration}s) - {seg.text}")
        assert duration <= 8.0, f"Segment {i+1} duration {duration}s exceeds 8s"
        
    # Test Case 3: Mixed bag
    segments_mixed = [
        TranscriptSegment(0.0, 2.0, "สั้นๆ"),
        TranscriptSegment(2.0, 11.0, "ยาวมากๆเลยนะอันนี้ยาวจริงๆไม่ได้โม้เลยนะจะบอกให้ยาวไปไหนเนี่ย"), # 9s duration
        TranscriptSegment(11.0, 13.0, "จบ")
    ]
    
    print("\n--- Test Case 3: Mixed segments ---")
    optimized_mixed = transcriber._optimize_for_scenes(segments_mixed)
    for i, seg in enumerate(optimized_mixed):
        duration = seg.end - seg.start
        print(f"Segment {i+1}: {seg.start}-{seg.end} ({duration}s) - {seg.text}")
        assert duration <= 8.0, f"Segment {i+1} duration {duration}s exceeds 8s"

    print("\n✅ All tests passed!")

if __name__ == "__main__":
    test_scene_optimization()