.PHONY: help dev api install clean test \
        se-up se-down se-api se-ui se-test se-logs se-restart \
        gcp-setup

VENV = .venv/bin
PYTHON = $(VENV)/python
PIP = $(VENV)/pip

help: ## Show this help message
	@echo 'Usage: make [target]'
	@echo ''
	@echo 'Available targets:'
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  %-20s %s\n", $$1, $$2}' $(MAKEFILE_LIST)

# ── vdo-content ───────────────────────────────────────────────────────────────

install: ## Install vdo-content dependencies
	$(PIP) install -r requirements.txt

dev: ## Run Streamlit dev server
	$(VENV)/streamlit run app.py --server.address=0.0.0.0 --server.port=8501

api: ## Run vdo-content FastAPI backend (port 8000)
	$(VENV)/uvicorn src.backend.api.main:app --reload --port 8000

test: ## Run vdo-content tests
	$(VENV)/pytest tests/ -v

clean: ## Clean up temporary files
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

# ── Strategy Engine ───────────────────────────────────────────────────────────

se-up: ## Start ALL services (vdo-content + Strategy Engine)
	docker compose up -d
	@echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
	@echo "  vdo-content (Streamlit) → http://localhost:8510"
	@echo "  vdo-content (API)       → http://localhost:8000"
	@echo "  Strategy Engine API     → http://localhost:8001"
	@echo "  Strategy Engine UI      → http://localhost:3000"
	@echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

se-down: ## Stop all services
	docker compose down

se-restart: ## Restart Strategy Engine services only
	docker compose restart strategy-api strategy-ui

se-api: ## Start only Strategy Engine API (+ its deps)
	docker compose up -d strategy-postgres strategy-qdrant strategy-api
	@echo "Strategy Engine API → http://localhost:8001/docs"

se-ui: ## Start only Strategy Engine UI
	docker compose up -d strategy-ui
	@echo "Strategy Engine UI → http://localhost:3000"

se-test: ## Run Strategy Engine tests (119 tests)
	cd strategy-engine/backend && \
	../../$(VENV)/python -m pytest tests/ -v --tb=short

se-logs: ## Follow Strategy Engine API logs
	docker compose logs -f strategy-api

# ── GCP Production Setup ─────────────────────────────────────────────────────

gcp-setup: ## Run one-time GCP production setup (Artifact Registry, Cloud Tasks, IAM, Secrets)
	@echo "🌏 Running GCP production setup..."
	chmod +x scripts/setup_gcp_resources.sh
	./scripts/setup_gcp_resources.sh

provision-db: ## Provision Cloud SQL PostgreSQL for strategy-engine (run once)
	@echo "🗄️  Provisioning Cloud SQL for strategy-engine..."
	chmod +x scripts/provision_cloudsql.sh
	./scripts/provision_cloudsql.sh

provision-qdrant: ## Deploy self-hosted Qdrant on Cloud Run for strategy-engine RAG (run once)
	@echo "🔍 Deploying Qdrant on Cloud Run..."
	chmod +x scripts/provision_qdrant.sh
	./scripts/provision_qdrant.sh

