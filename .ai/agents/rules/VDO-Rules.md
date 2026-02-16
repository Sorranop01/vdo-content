# VDO Content Rules

**Version:** 1.0.0

---

## 🎬 VDO-Specific Rules

### 1. Scene Duration Limit
```
Maximum: 8 seconds per scene
```
Veo 3 has a maximum clip length of 8 seconds.

---

### 2. Language Separation
```
Thai Script → DeepSeek API
English Prompts → Veo 3
```

---

### 3. Prompt Quality

**For Veo 3 prompts:**
- Use descriptive English
- Include: cinematic, 4K, lighting
- Describe camera movement
- Specify mood/atmosphere

```
Good: "Cinematic wide shot of golden temple at sunset, 
       warm lighting, slow dolly movement, peaceful atmosphere"

Bad:  "Temple video"
```

---

### 4. Audio Sync

Thai narration timing must match scene duration for seamless integration.

---

### 5. File Organization

```
data/
├── projects/          # SQLite DB
├── exports/           # Generated prompts
└── cache/             # Temporary files
```

---

**Status:** Active
