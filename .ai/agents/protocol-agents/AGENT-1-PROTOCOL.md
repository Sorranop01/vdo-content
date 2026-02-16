# Agent-1 Protocol: Ideation

**ID:** `agent-1-ideation`
**Version:** 1.0.0

---

## Boot Sequence
```typescript
agent__boot({ agent_id: "agent-1-ideation", format: "full" });
```

## VDO Content Domains
- Script Generation (Thai narration)
- Scene Splitting (≤8s scenes)
- Prompt Generation (Veo 3 English)
- UI/Dashboard (Streamlit)

## Handoff → Agent-2
```markdown
@agent-2 Requirements ready:
**Feature:** [name]
**Affected Modules:** [list]
```

---

**Status:** Active
