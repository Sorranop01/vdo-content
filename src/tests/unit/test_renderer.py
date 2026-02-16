
import sys
import os
import shutil
from pathlib import Path
from unittest.mock import MagicMock

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.models import Project, Scene
from core.video_renderer import VideoRenderer

def test_video_rendering():
    print("🚀 Testing Video Renderer (FFmpeg Integration)")
    print("=" * 50)
    
    # 1. Setup Mock Project
    print("1️⃣ Setting up Mock Project...")
    
    # Create dummy audio file (5 seconds of silence)
    # Using ffmpeg to generate silence audio
    audio_path = Path("test_audio_silence.mp3")
    import subprocess
    subprocess.run(
        ["ffmpeg", "-y", "-f", "lavfi", "-i", "anullsrc=r=44100:cl=mono",
         "-t", "5", "-q:a", "9", str(audio_path)],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
    )
    
    if not os.path.exists(audio_path):
        print("❌ Failed to create dummy audio file. Is ffmpeg installed?")
        return

    project = Project(
        title="Test_Render_Project",
        topic="Test Topic",
        audio_path=str(audio_path),  # Convert PosixPath to str for Pydantic
        scenes=[
            Scene(order=1, narration_text="Scene 1 Hello", veo_prompt="A cat", estimated_duration=2.0),
            Scene(order=2, narration_text="Scene 2 World", veo_prompt="A dog", estimated_duration=3.0)
        ]
    )
    # Manually sync audio duration props
    project.scenes[0].audio_duration # will be 0.0 initially
    # Hack to force audio_duration calculation mock
    project.scenes[0].start_time = 0.0
    project.scenes[0].end_time = 2.0
    project.scenes[1].start_time = 2.0
    project.scenes[1].end_time = 5.0

    # 2. Initialize Renderer
    output_dir = "tests/test_renders"
    renderer = VideoRenderer(output_dir=output_dir)
    
    # 3. Run Render
    print(f"2️⃣ Rendering video to {output_dir}...")
    try:
        output_path = renderer.render_draft(project)
        print(f"✅ Render call completed. Output: {output_path}")
    except Exception as e:
        print(f"❌ Render Failed: {e}")
        # Clean up
        if os.path.exists(audio_path): os.remove(audio_path)
        sys.exit(1)

    # 4. Verify Output
    print("3️⃣ Verifying Output File...")
    if os.path.exists(output_path):
        size = os.path.getsize(output_path)
        print(f"   File exists! Size: {size/1024:.2f} KB")
        
        if size > 1000: # Should be somewhat substantial > 1KB
            print("✅ SUCCESS: Valid video file generated.")
        else:
            print("❌ FAILURE: File is too small (likely empty or corrupted).")
    else:
        print("❌ FAILURE: Output file not found.")

    # Cleanup
    if os.path.exists(audio_path): os.remove(audio_path)
    # shutil.rmtree(output_dir) # Keep for inspection

    print("=" * 50)

if __name__ == "__main__":
    test_video_rendering()
