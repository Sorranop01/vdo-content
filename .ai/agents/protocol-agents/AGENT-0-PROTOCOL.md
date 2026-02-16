# Agent-0 Protocol: Orchestrator

**ID:** `agent-0-orchestrator`
**Version:** 1.0.0

---

## Boot Sequence
```typescript
agent__boot({ agent_id: "agent-0-orchestrator", format: "full" });
```

## Routing Table

| Task Type | Pipeline |
|-----------|----------|
| NEW_FEATURE | 1→2→3→4→5→6 |
| BUG_FIX | 3→4→5→6 |
| PROMPT_TUNING | 2→3→4 |
| UI_ENHANCEMENT | 3→4→5 |

## Keywords → Domain

| Keywords | Domain |
|----------|--------|
| script, บท | script-gen |
| scene, ฉาก | scene-split |
| veo, prompt | prompt-gen |
| streamlit, ui | frontend |

---

**Status:** Active
