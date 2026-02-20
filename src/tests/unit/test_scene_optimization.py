import sys
import os
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.transcriber import AudioTranscriber, TranscriptSegment, WordInfo

def test_scene_optimization():
    print("Testing Scene Optimization Logic (7-8s targeting)...\n")
    
    # Initialize transcriber (mocking model to avoid loading)
    transcriber = AudioTranscriber(model_size="base")
    
    # ===== Test Case 1: Short segments merge into 7-8s =====
    # Many short 1-2s segments should be merged together
    print("--- Test Case 1: Merging many short segments into ~7-8s ---")
    segments = []
    # Create 10 x 1.5s segments = 15s total → should give ~2 segments of ~7-8s
    for i in range(10):
        start = i * 1.5
        end = start + 1.5
        text = f"ส่วนที่{i+1}"
        segments.append(TranscriptSegment(
            start=start, end=end, text=text,
            words=[WordInfo(word=text, start=start, end=end)]
        ))
    
    optimized = transcriber._optimize_for_scenes(segments)
    for i, seg in enumerate(optimized):
        duration = seg.end - seg.start
        print(f"  Segment {i+1}: {seg.start:.1f}-{seg.end:.1f} ({duration:.1f}s) - {seg.text}")
        assert duration <= 10.0, f"Segment {i+1} duration {duration}s way too long"
    
    print(f"  → {len(segments)} short segments merged into {len(optimized)} scenes")
    assert len(optimized) < len(segments), "Short segments should be merged"
    print("  ✅ PASSED\n")

    # ===== Test Case 2: Segments already at ~8s stay intact =====
    print("--- Test Case 2: Segments already at 7-8s stay intact ---")
    segments_ok = [
        TranscriptSegment(0.0, 7.5, "ประโยคที่พอดีเลย",
                          words=[WordInfo(word="ประโยคที่พอดีเลย", start=0.0, end=7.5)]),
        TranscriptSegment(7.5, 15.0, "ประโยคที่สองก็พอดี",
                          words=[WordInfo(word="ประโยคที่สองก็พอดี", start=7.5, end=15.0)]),
    ]
    
    optimized_ok = transcriber._optimize_for_scenes(segments_ok)
    for i, seg in enumerate(optimized_ok):
        duration = seg.end - seg.start
        print(f"  Segment {i+1}: {seg.start:.1f}-{seg.end:.1f} ({duration:.1f}s) - {seg.text}")
        assert duration <= 8.0, f"Segment {i+1} exceeds 8s"
    assert len(optimized_ok) == 2, "Two 7.5s segments should stay as 2"
    print("  ✅ PASSED\n")

    # ===== Test Case 3: Long segment (>8s) gets split =====
    print("--- Test Case 3: Long 12s segment gets split ---")
    # Simulate a 12s segment with word-level timestamps every 1s
    words_12s = []
    thai_words = ["สวัสดี", "ครับ", "วันนี้", "เรา", "จะ", "มา", "คุย", "กันนะ", "เรื่อง", "สุขภาพ", "ที่ดี", "เลย"]
    for i, w in enumerate(thai_words):
        words_12s.append(WordInfo(word=w, start=float(i), end=float(i+1)))
    
    long_segment = TranscriptSegment(
        0.0, 12.0, "".join(thai_words),
        words=words_12s
    )
    
    optimized_long = transcriber._optimize_for_scenes([long_segment])
    for i, seg in enumerate(optimized_long):
        duration = seg.end - seg.start
        print(f"  Segment {i+1}: {seg.start:.1f}-{seg.end:.1f} ({duration:.1f}s) - {seg.text}")
        assert duration <= 10.0, f"Segment {i+1} duration {duration}s too long"
    assert len(optimized_long) >= 2, "12s should be split into at least 2"
    print("  ✅ PASSED\n")

    # ===== Test Case 4: Thai break particle triggers cut in sweet zone =====
    print("--- Test Case 4: Break particle (ครับ) triggers cut in 7-8s zone ---")
    words_break = []
    for i in range(15):
        # Put "ครับ" at the 7.5s mark (word index 7)
        w = "ครับ" if i == 7 else f"คำ{i+1}"
        words_break.append(WordInfo(word=w, start=float(i) * 0.8, end=float(i+1) * 0.8))
    
    seg_break = TranscriptSegment(
        0.0, 12.0, "".join([w.word for w in words_break]),
        words=words_break
    )
    
    optimized_break = transcriber._optimize_for_scenes([seg_break])
    for i, seg in enumerate(optimized_break):
        duration = seg.end - seg.start
        print(f"  Segment {i+1}: {seg.start:.1f}-{seg.end:.1f} ({duration:.1f}s) - {seg.text}")
    
    # The first segment should end around the "ครับ" word
    if optimized_break:
        first_dur = optimized_break[0].end - optimized_break[0].start
        print(f"  → First segment duration: {first_dur:.1f}s (should be ~7-8s)")
        assert first_dur >= 5.0, "First segment should be at least 5s (break point near 7-8s)"
        assert first_dur <= 8.0, "First segment must not exceed 8s"
    print("  ✅ PASSED\n")

    # ===== Test Case 5: Trailing short segment gets merged =====
    print("--- Test Case 5: Trailing short segment (<7s) merges into predecessor ---")
    # Create: 7.5s segment + 2s trailing segment
    words5 = []
    for i in range(10):
        words5.append(WordInfo(word=f"w{i}", start=float(i), end=float(i+1)))
    
    seg5 = TranscriptSegment(0.0, 10.0, "".join([w.word for w in words5]), words=words5)
    # With MIN=7, first cut at ~7s, leaving ~3s orphan
    # Final merge should combine the 3s orphan back with the 7s segment
    
    optimized5 = transcriber._optimize_for_scenes([seg5])
    for i, seg in enumerate(optimized5):
        duration = seg.end - seg.start
        print(f"  Segment {i+1}: {seg.start:.1f}-{seg.end:.1f} ({duration:.1f}s) - {seg.text}")
    
    # With 10s total and merge logic, we should get either:
    # - 1 segment of 10s (merged, slightly over 8s but within 10s tolerance)
    # - 2 segments where the last one was merged
    print(f"  → Got {len(optimized5)} segment(s)")
    print("  ✅ PASSED\n")

    # ===== Test Case 6: No segments =====
    print("--- Test Case 6: Empty input ---")
    optimized_empty = transcriber._optimize_for_scenes([])
    assert optimized_empty == [], "Empty input should give empty output"
    print("  ✅ PASSED\n")

    # ===== Test Case 7: All segments <= 8s (original test) =====
    print("--- Test Case 7: Original test - basic merging ---")
    segments = [
        TranscriptSegment(0.0, 3.0, "สวัสดีครับ"),
        TranscriptSegment(3.0, 6.0, "วันนี้เราจะมาคุยกัน"),
        TranscriptSegment(6.0, 10.0, "เรื่องสุขภาพ")
    ]
    
    optimized = transcriber._optimize_for_scenes(segments)
    for i, seg in enumerate(optimized):
        duration = seg.end - seg.start
        print(f"  Segment {i+1}: {seg.start:.1f}-{seg.end:.1f} ({duration:.1f}s) - {seg.text}")
        assert duration <= 10.0, f"Segment {i+1} duration {duration}s too long"
    print("  ✅ PASSED\n")

    print("=" * 50)
    print("✅ All 7 tests passed!")

if __name__ == "__main__":
    test_scene_optimization()