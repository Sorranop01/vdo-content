---
description: Feature development workflow for VDO Content
executable: true
---

# Feature Development Workflow

## Trigger Pattern
- "Add/Create [feature]"
- "เพิ่ม [feature]"

---

## Phase 1: Requirements → Agent-1
```
1. Analyze requirements
2. Identify affected modules
3. Output: Requirements doc
```

## Phase 2: Planning → Agent-2
```
1. Design module structure
2. Plan prompt templates
3. Output: Blueprint
```

## Phase 3: Implementation → Agent-3
```
cd /home/agent/workspace/vdo-content
source venv/bin/activate

# Implement modules
# Test locally
streamlit run app.py
```

## Phase 4: Review → Agent-4
```
ruff check .
pytest tests/
```

## Phase 5: Deploy → Agent-5
```
docker-compose up -d
```

## Phase 6: Learning → Agent-6
```
knowledge__remember({ category: "pattern", fact: "..." })
```

---

## Handoff Chain
```
1 → 2 → 3 → 4 → 5 → 6
```
