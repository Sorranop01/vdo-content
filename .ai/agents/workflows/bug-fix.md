---
description: Bug fix workflow for VDO Content
executable: true
---

# Bug Fix Workflow

## Trigger Pattern
- "Fix [bug]"
- "แก้ไข [bug]"

---

## Phase 1: Analysis → Agent-3
```
1. Query KB for similar bugs
2. Identify root cause
3. Plan fix
```

## Phase 2: Fix → Agent-3
```
1. Implement fix
2. Test locally
```

## Phase 3: Review → Agent-4
```
ruff check .
pytest tests/
```

## Phase 4: Deploy → Agent-5
```
docker-compose restart
```

## Phase 5: Learning → Agent-6
```
knowledge__remember({
  category: "bug-fix",
  fact: "Bug: [desc] | Fix: [fix]"
})
```

---

## Handoff Chain
```
3 → 4 → 5 → 6
```
