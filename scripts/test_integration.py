import sys
import os
from pathlib import Path
import time

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from core.transcriber import AudioTranscriber, TranscriptSegment

def mock_transcribe_result():
    """
    Mock functionality of whisper transcribe 
    since we might not have GPU/Model loaded in this CLI environment
    """
    # Simulate a long audio (20s) with continuous Thai speech
    # 0-5s: Short sentence
    # 5-18s: Very long sentence (13s) -> Must be split into at least 2 parts (8+5 or 6.5+6.5)
    # 18-20s: Short sentence
    
    return [
        TranscriptSegment(0.0, 5.0, "สวัสดีครับวันนี้เราจะมาทดสอบระบบกัน"),
        TranscriptSegment(5.0, 18.0, "และนี่คือประโยคที่ยาวมากๆยาวจนเกินแปดวินาทีแน่นอนเพื่อให้ระบบทำการตัดแบ่งอัตโนมัติโดยที่เราไม่ต้องทำเองเลยครับพี่น้อง"),
        TranscriptSegment(18.0, 20.0, "จบการทดสอบครับ")
    ]

def run_integration_test():
    print("🚀 Starting Integration Test: Scene Splitting Logic")
    print("=" * 50)
    
    # Initialize transcriber
    transcriber = AudioTranscriber(model_size="base")
    
    # Get mock raw segments
    raw_segments = mock_transcribe_result()
    print(f"📥 Input Raw Segments: {len(raw_segments)}")
    for s in raw_segments:
        print(f"   - {s.start}-{s.end} ({s.end-s.start:.1f}s): {s.text[:30]}...")
    
    print("\n🔄 Processing: optimizing for scenes (<= 8.0s)...")
    
    # Run optimization logic
    final_segments = transcriber._optimize_for_scenes(raw_segments)
    
    print("-" * 50)
    print(f"📤 Output Final Segments: {len(final_segments)}")
    
    failures = []
    
    for i, seg in enumerate(final_segments):
        duration = round(seg.end - seg.start, 2)
        status = "✅" if duration <= 8.0 else "❌"
        
        print(f"   {status} Scene {i+1}: {seg.start:.1f}s - {seg.end:.1f}s (Dur: {duration}s)")
        print(f"      Text: {seg.text}")
        
        if duration > 8.0:
            failures.append(f"Scene {i+1} exceeds 8s limit (Duration: {duration}s)")
            
    print("=" * 50)
    
    if failures:
        print(f"❌ TEST FAILED: Found {len(failures)} violations!")
        for f in failures:
            print(f"   - {f}")
        sys.exit(1)
    else:
        print("✅ TEST PASSED: All scenes are within 8 second limit.")
        print("   Logic for splitting long Thai sentences is working.")

if __name__ == "__main__":
    run_integration_test()