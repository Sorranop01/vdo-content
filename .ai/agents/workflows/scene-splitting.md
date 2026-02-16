---
description: Scene splitting workflow for VDO Content
executable: true
---

# Scene Splitting Workflow (VDO-Specific)

## Trigger Pattern
- "Split scenes"
- "แบ่งฉาก"
- "Scene timing"

---

## Key Rule
**Each scene MUST be ≤8 seconds** (Veo 3 limit)

---

## Splitting Logic

```python
MAX_SCENE_DURATION = 8  # seconds

def split_script(narration: str, total_duration: float) -> list:
    sentences = narration.split('.')
    scenes = []
    current_scene = ""
    current_duration = 0
    
    for sentence in sentences:
        sentence_duration = estimate_duration(sentence)
        
        if current_duration + sentence_duration <= MAX_SCENE_DURATION:
            current_scene += sentence + "."
            current_duration += sentence_duration
        else:
            scenes.append({
                "narration": current_scene.strip(),
                "duration": current_duration
            })
            current_scene = sentence + "."
            current_duration = sentence_duration
    
    return scenes
```

---

## Workflow

1. Receive Thai script
2. Estimate sentence durations
3. Split into ≤8s scenes
4. Generate Veo 3 prompt per scene
5. Output scene list

---

**Status:** Active
