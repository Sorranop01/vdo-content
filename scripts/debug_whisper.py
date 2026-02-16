
import sys
import os

print("Testing Faster Whisper Import and Init...")

try:
    from faster_whisper import WhisperModel
    print("Import successful.")
except Exception as e:
    print(f"Import failed: {e}")
    sys.exit(1)

print("Attempting to initialize model with device='auto'...")
try:
    model = WhisperModel("base", device="auto", compute_type="int8")
    print("Init 'auto' successful.")
except Exception as e:
    print(f"Init 'auto' failed: {e}")
    
    print("Attempting to initialize model with device='cpu'...")
    try:
        model = WhisperModel("base", device="cpu", compute_type="int8")
        print("Init 'cpu' successful.")
    except Exception as e2:
        print(f"Init 'cpu' failed: {e2}")
