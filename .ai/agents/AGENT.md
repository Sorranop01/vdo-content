# 🎬 VDO Content Project - Agent Configuration

> **⚠️ THIS IS THE SINGLE SOURCE OF TRUTH (SSOT) FOR VDO CONTENT PROJECT**
> 
> **File:** `AGENT.md` (This file)
> **Synced to:** `GEMINI.md`, `CLAUDE.md`
> **Location:** `agents/projects/agent-vdo/`
> 
> **DO NOT EDIT** `GEMINI.md` or `CLAUDE.md` directly. Edit this file and run sync.

---

## 🏢 Project Identity

| Key | Value |
|-----|-------|
| **Name** | VDO Content |
| **Purpose** | AI Content Pipeline (Video Scripts & Veo 3 Prompts) |
| **Target** | Content Creators, Media Teams |
| **Vision** | Streamlined video content workflow |
| **Value Prop** | "From idea to Veo 3 prompt, seamlessly." |
| **Workspace** | `/home/agent/workspace/vdo-content` (Server 222) |

---

## 📂 Project Structure

```
/home/agent/workspace/vdo-content/
├── app.py                    # Streamlit main app
├── core/
│   ├── script_generator.py   # Thai script generation (DeepSeek)
│   ├── scene_splitter.py     # Scene splitting (≤8s)
│   ├── prompt_generator.py   # Veo 3 prompts (English)
│   ├── audio_analyzer.py     # Audio duration analysis
│   ├── aistudio_generator.py # AI Studio integration
│   ├── story_analyzer.py     # Story analysis
│   ├── database.py           # SQLite operations
│   └── models.py             # Data models
├── ui/                       # UI components
├── templates/                # Prompt templates
├── data/                     # SQLite database
└── docker-compose.yml
```

---

## 🛠️ Technology Stack

| Aspect | Technology |
|--------|------------|
| **Language** | Python 3.11+ |
| **UI** | Streamlit |
| **AI Services** | DeepSeek API, Google AI Studio |
| **Database** | SQLite |
| **Processing** | FFmpeg (audio/video) |
| **Containerization** | Docker |

---

## 🔄 AI Pipeline

```
User Input (Topic)
      ↓
DeepSeek → Thai Narration Script
      ↓
Scene Splitter → ≤8s segments
      ↓
Prompt Generator → Veo 3 English Prompts
      ↓
Export/Copy for Veo 3
```

---

## 🔒 Iron Rules (VDO-Specific)

### 1. Scene Duration Limit
- **Maximum: 8 seconds** per scene (Veo 3 limit)

### 2. Language Separation
- **Thai:** Script narration (DeepSeek)
- **English:** Veo 3 video prompts

### 3. API Key Security
- Store in `.env`, never commit
- Use `os.getenv()` for access

---

## 📦 Domain Modules

| Category | Modules |
|----------|---------|
| **Script** | `script_generator`, `story_analyzer` |
| **Scene** | `scene_splitter`, `audio_analyzer` |
| **Prompts** | `prompt_generator`, `aistudio_generator` |
| **Data** | `database`, `models` |
| **UI** | `app.py`, `ui/` |

---

## 🤖 Agent Squad

| Agent | Role | Responsibility |
|-------|------|----------------|
| **agent-0** | Orchestrator | Task routing |
| **agent-1** | Ideation | Content requirements |
| **agent-2** | Planning | Pipeline design |
| **agent-3** | Execution | Python/Streamlit code |
| **agent-4** | Review | QA, testing |
| **agent-5** | Deployment | Docker, deploy |
| **agent-6** | Evolution | Prompt patterns |
| **agent-7** | Librarian | Context injection |
| **agent-8** | Reporter | Thai summaries |
| **agent-9** | Audit | Code quality |

---

## 📄 Related Files

| Directory | Purpose |
|-----------|---------|
| `master-agents/` | Agent persona definitions (10 files) |
| `protocol-agents/` | Agent protocols (10 files) |
| `sub-agents/` | Specialized sub-agents (9 files) |
| `workflows/` | Task workflows (4 files) |
| `rules/` | Project-specific rules (3 files) |

### VDO-Specific Components

**Sub-Agents:**
- `sub-ai-prompts` - AI prompt engineering
- `sub-streamlit` - Streamlit UI
- `sub-media` - FFmpeg processing

**Workflows:**
- `prompt-tuning.md` - Improve AI prompts
- `scene-splitting.md` - Scene timing

---

## ✅ Pre-Coding Checklist

Before writing any code:

- [ ] Query MCP KB for existing patterns
- [ ] Check scene duration (≤8s)
- [ ] Verify API key handling
- [ ] Use Python type hints
- [ ] Run ruff linting

---

## 🔗 Sync Information

```bash
# Sync command (from this directory)
cp AGENT.md GEMINI.md && cp AGENT.md CLAUDE.md
```

---

**Last Updated:** 2026-01-28
**Version:** 1.0.0
