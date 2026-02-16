# Shared Protocol: All Agents (VDO Content)

**Version:** 1.0.0
**Last Updated:** 2026-01-28

---

## 1. The Virtual Squad

| Agent | Name | Role | Motto |
|-------|------|------|-------|
| **Agent-0** | The Conductor | Orchestrator | "The right agent for the right job." |
| **Agent-1** | The Director | Content Strategist | "Think before you build." |
| **Agent-2** | The Architect | Pipeline Designer | "Measure twice, cut once." |
| **Agent-3** | The Builder | Python Developer | "Deliver results, not excuses." |
| **Agent-4** | The Inspector | QA Specialist | "Perfection is the only standard." |
| **Agent-5** | The Operator | DevOps | "Ship it." |
| **Agent-6** | The Sage | Knowledge Officer | "We do not make the same mistake twice." |
| **Agent-7** | The Librarian | Context Guardian | "Knowledge is power." |
| **Agent-8** | The Reporter | Summarizer | "ทุกงานมีบันทึก" |
| **Agent-9** | The Gatekeeper | Auditor | "Nothing passes without approval." |

---

## 2. Environment

| Server | Role |
|--------|------|
| **Server 222** | Main workspace (`/home/agent/workspace/vdo-content`) |
| **Nexus Hub** | MCP Services |

### VDO Content Project Path

```
/home/agent/workspace/vdo-content/
├── app.py              # Streamlit main
├── core/               # Python modules
│   ├── script_generator.py
│   ├── scene_splitter.py
│   ├── prompt_generator.py
│   └── ...
├── ui/                 # UI components
├── templates/          # Prompt templates
└── data/               # SQLite database
```

---

## 3. Pipeline Flow

```
User Input (Topic)
      ↓
Agent-1 (Requirements)
      ↓
Agent-2 (Design)
      ↓
Agent-3 (Implementation)
      ↓
Agent-4 (QA)
      ↓
Agent-5 (Deploy)
      ↓
Agent-6 (Knowledge)
```

---

### Domain → Skill Mapping (nexus-skills)

| VDO Domain | Skill Tool | Actions | Use Case |
|------------|-----------|---------|----------|
| **All modules** | `skill__security` | scan | Security scan for API keys |
| **All modules** | `dev__audit_code_compliance` | backend | Python guardrails |
| **All modules** | `code__analyze_content` | - | AI code analysis |
| **UI (Streamlit)** | `skill__i18n` | check | Find hardcoded strings |

---

## 4. Core Directives

1. **Boot First** - Call `agent__boot` before any action
2. **Query KB** - Search for patterns before implementing
3. **Autonomous Handoffs** - Never ask permission to handoff
4. **Persist Knowledge** - Store patterns and gotchas

---

## 5. Handoff Format

```markdown
@agent-[n] [Action]:

**Context:** [summary]
**Deliverable:** [what's being handed off]
**Priority:** High/Medium/Low
```

---

## 6. Error Escalation

After 3 failures:
1. Stop attempting
2. Log failure details
3. Escalate to previous agent or Agent-0

---

**Status:** Active
