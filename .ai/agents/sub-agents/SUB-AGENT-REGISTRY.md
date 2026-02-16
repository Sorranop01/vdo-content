# Sub-Agent Registry (VDO Content)

> **Single Source of Truth** for Parent Agent ↔ Sub-Agent relationships

---

## Overview

| Parent Agent | Sub-Agents | Responsibility |
|--------------|------------|----------------|
| **agent-3** | `sub-ai-prompts`, `sub-streamlit`, `sub-media`, `sub-database` | Implementation |
| **agent-4** | `sub-testing` | QA |
| **agent-5** | `sub-devops` | Deployment |
| **agent-6** | `sub-documentation`, `sub-research` | Knowledge |

---

## VDO-Specific Sub-Agents

### sub-ai-prompts
```yaml
id: sub-ai-prompts
parent: agent-3
purpose: AI prompt engineering for DeepSeek and Veo 3
triggers:
  - Prompt template creation
  - AI response tuning
  - Script generation optimization
```

### sub-streamlit
```yaml
id: sub-streamlit
parent: agent-3
purpose: Streamlit UI components
triggers:
  - Dashboard creation
  - UI widgets
  - Page layouts
```

### sub-media
```yaml
id: sub-media
parent: agent-3
purpose: FFmpeg and media processing
triggers:
  - Audio analysis
  - Video processing
  - Thumbnail generation
```

---

## Standard Sub-Agents

### sub-database
```yaml
id: sub-database
parent: agent-3
purpose: SQLite operations
```

### sub-testing
```yaml
id: sub-testing
parent: agent-4
purpose: Python testing (pytest)
```

### sub-devops
```yaml
id: sub-devops
parent: agent-5
purpose: Docker and deployment
```

### sub-documentation
```yaml
id: sub-documentation
parent: agent-6
purpose: README and docs
```

### sub-research
```yaml
id: sub-research
parent: agent-6
purpose: Pattern research
```

---

**Total Sub-Agents:** 8
**Version:** 1.0.0
