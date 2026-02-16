# Sub-Agent: AI Prompts (VDO-Specific)

**ID:** `sub-ai-prompts`
**Parent:** `agent-3-execution`

---

## Purpose

AI prompt engineering for DeepSeek (Thai scripts) and Veo 3 (English video prompts).

---

## Responsibilities

1. Design prompt templates
2. Tune AI responses
3. Optimize script generation
4. Create effective Veo 3 prompts

---

## Prompt Patterns

### DeepSeek (Thai Script)
```python
prompt = f"""
คุณคือนักเขียนบทภาษาไทย สร้างสคริปต์เสียงพากย์สำหรับวิดีโอ
หัวข้อ: {topic}
ความยาว: {duration} นาที
สไตล์: {style}
"""
```

### Veo 3 (English Video)
```python
prompt = f"""
Cinematic shot, 4K quality, {scene_description},
smooth camera movement, professional lighting,
{mood} atmosphere, {style} style
"""
```

---

## Common Gotchas

- DeepSeek needs clear Thai instructions
- Veo 3 prefers descriptive English
- Scene ≤8 seconds for Veo 3

---

**Status:** Active
