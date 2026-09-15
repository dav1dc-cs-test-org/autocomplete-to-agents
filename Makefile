.DEFAULT_GOAL := help
PY ?= python3
VENV := .venv
BIN := $(VENV)/bin

.PHONY: help
help: ## Show available targets
	@grep -E '^[a-zA-Z_-]+:.*?## ' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-14s\033[0m %s\n", $$1, $$2}'

$(BIN)/python:
	$(PY) -m venv $(VENV)
	$(BIN)/python -m pip install --quiet --upgrade pip

.PHONY: setup
setup: $(BIN)/python ## Create venv and install the project with dev + api extras
	$(BIN)/python -m pip install --quiet -e ".[dev,api]"
	@echo "ready: source $(VENV)/bin/activate"

.PHONY: test
test: ## Run the test suite
	$(BIN)/pytest

.PHONY: cov
cov: ## Run tests with coverage
	$(BIN)/pytest --cov=freightline --cov-report=term-missing

.PHONY: lint
lint: ## Lint with ruff
	$(BIN)/ruff check src tests scripts

.PHONY: typecheck
typecheck: ## Type-check with mypy
	$(BIN)/mypy

.PHONY: check
check: lint typecheck test ## Everything CI runs

.PHONY: seed
seed: ## Rebuild var/freightline.db with demo data
	$(BIN)/python scripts/seed_data.py

.PHONY: serve
serve: ## Run the HTTP API on :8000
	$(BIN)/uvicorn freightline.api.app:app --reload --port 8000

.PHONY: clean
clean: ## Remove caches and the local database
	rm -rf .pytest_cache .mypy_cache .ruff_cache htmlcov .coverage var
	find . -name __pycache__ -type d -prune -exec rm -rf {} +
