.PHONY: help dev api install clean test

VENV = .venv/bin
PYTHON = $(VENV)/python
PIP = $(VENV)/pip

help: ## Show this help message
	@echo 'Usage: make [target]'
	@echo ''
	@echo 'Available targets:'
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  %-15s %s\n", $$1, $$2}' $(MAKEFILE_LIST)

install: ## Install dependencies
	$(PIP) install -r requirements.txt

dev: ## Run Streamlit dev server (accessible from external networks)
	$(VENV)/streamlit run app.py --server.address=0.0.0.0 --server.port=8501

api: ## Run FastAPI backend
	$(VENV)/uvicorn api.main:app --reload --port 8000

run: ## Run both dev and api (in background)
	@echo "Starting Streamlit on http://localhost:8501..."
	@$(VENV)/streamlit run app.py &
	@echo "Starting API on http://localhost:8000..."
	@$(VENV)/uvicorn api.main:app --reload --port 8000 &
	@echo "Both servers are running. Press Ctrl+C to stop."

test: ## Run tests
	$(VENV)/pytest tests/ -v

clean: ## Clean up temporary files
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name ".pytest_cache" -exec rm -rf {} +
