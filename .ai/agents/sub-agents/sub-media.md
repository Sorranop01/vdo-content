# Sub-Agent: Media (VDO-Specific)

**ID:** `sub-media`
**Parent:** `agent-3-execution`

---

## Purpose

FFmpeg and media processing for audio/video.

---

## Responsibilities

1. Audio duration analysis
2. Video processing
3. Thumbnail generation

---

## FFmpeg Patterns

### Get Audio Duration
```python
import subprocess

def get_duration(file_path: str) -> float:
    result = subprocess.run([
        'ffprobe', '-v', 'error',
        '-show_entries', 'format=duration',
        '-of', 'default=noprint_wrappers=1:nokey=1',
        file_path
    ], capture_output=True, text=True)
    return float(result.stdout.strip())
```

---

**Status:** Active
