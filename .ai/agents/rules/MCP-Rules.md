# MCP Rules (VDO Content)

**Version:** 1.0.0

---

## Unified Tool Names

| Category | Tools |
|----------|-------|
| Knowledge | `kb__search`, `kb__code` |
| Agent | `agent__route`, `agent__boot` |
| Memory | `memory__manage` |
| Librarian | `librarian__context` |

---

## Boot Sequence

```typescript
agent__boot({ agent_id: "agent-X", format: "full" });
```

---

## Context Injection

```typescript
librarian__context({
  action: "inject",
  prompt: "vdo content task"
});
```

---

**Status:** Active
