# Agent-4 Protocol: Review

**ID:** `agent-4-review`
**Version:** 1.0.0

---

## Boot Sequence
```typescript
agent__boot({ agent_id: "agent-4-review", format: "full" });
```

## Testing
```bash
ruff check .
mypy .
pytest tests/
```

## Quality Checks
- [ ] Python linting passes
- [ ] AI prompts work correctly
- [ ] Scenes ≤8 seconds
- [ ] UI is functional

## Handoff → Agent-5
```markdown
@agent-5 QA approved:
**Tests:** All passed
**Status:** Ready for deploy
```

---

**Status:** Active
