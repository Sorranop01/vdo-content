# Strategy Engine — AI Content Strategy & Topic Planning Engine

> 🧠 The "Brain" upstream of the vdo-content production pipeline.

## What This Does

Takes raw, unstructured user research (e.g., scraped competitor comments) and runs a **Multi-Agent AI pipeline** to generate an optimized, interconnected **Content Blueprint** — then dispatches it to the existing production system via webhook.

```
Raw Research Text → [Agent 1: Intent] → [Agent 2: SEO/GEO] → [Agent 3: Cluster] → [HITL Review] → JSON → Production
```

## Architecture

- **Strictly decoupled** from `vdo-content` — zero shared code, zero shared DB
- **One-way webhook** to production system (`POST /api/strategy/ingest`)
- **Human-in-the-loop** — pipeline pauses for human review before dispatch

## Tech Stack

| Component | Technology |
|-----------|-----------|
| Backend | FastAPI + Python 3.12 |
| Agent Orchestration | LangGraph |
| LLM | OpenAI GPT-4o / DeepSeek |
| Structured Output | Pydantic v2 + instructor |
| Vector DB (RAG) | Qdrant |
| Database | PostgreSQL |
| Frontend | Next.js 14 + shadcn/ui |

## Quick Start

```bash
# 1. Copy environment config
cp .env.example .env
# Edit .env with your API keys

# 2. Start all services
docker compose up -d

# 3. API is at http://localhost:8000
# 4. Docs at http://localhost:8000/docs

# Or run locally (backend only):
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/pipeline/start` | Start a new agent pipeline run |
| `GET` | `/api/pipeline/{run_id}/status` | Get pipeline run status |
| `GET` | `/api/pipeline/{run_id}/blueprint` | Get generated blueprint |
| `POST` | `/api/pipeline/{run_id}/approve` | Approve & trigger dispatch |
| `GET` | `/api/blueprints/` | List all blueprints |
| `GET` | `/api/blueprints/{id}` | Get a specific blueprint |
| `PUT` | `/api/blueprints/{id}` | Update (edit) a blueprint |
| `DELETE` | `/api/blueprints/{id}` | Delete a blueprint |
| `GET` | `/health` | Health check |

## Project Structure

```
strategy-engine/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI entry
│   │   ├── config.py            # Pydantic BaseSettings
│   │   ├── models/schemas.py    # SSOT Pydantic schemas
│   │   ├── agents/
│   │   │   ├── intent_extractor.py  # Agent 1
│   │   │   ├── seo_strategist.py    # Agent 2
│   │   │   ├── cluster_builder.py   # Agent 3
│   │   │   └── graph.py            # LangGraph orchestrator
│   │   ├── services/
│   │   │   └── webhook_service.py   # Production dispatch
│   │   └── routers/
│   │       ├── pipeline.py      # Pipeline endpoints
│   │       └── blueprints.py    # Blueprint CRUD
│   ├── tests/
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/                    # Next.js dashboard (Phase 3)
├── docker-compose.yml
└── .env.example
```

## Implementation Phases

- [x] **Phase 0** — Foundation & Project Setup
- [ ] **Phase 1** — Agent Pipeline Core (LLM integration)
- [ ] **Phase 2** — RAG & Memory (Qdrant + content registry)
- [ ] **Phase 3** — Dashboard UI & HITL (Next.js)
- [ ] **Phase 4** — Production Hardening (retries, auth, monitoring)
