# Sub-Agent: DevOps

**ID:** `sub-devops`
**Parent:** `agent-5-deployment`

---

## Purpose

Docker and deployment.

---

## Docker

```yaml
services:
  vdo-content:
    build: .
    ports:
      - "8501:8501"
    environment:
      - DEEPSEEK_API_KEY=${DEEPSEEK_API_KEY}
```

---

**Status:** Active
