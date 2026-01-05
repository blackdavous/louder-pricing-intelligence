.PHONY: help install dev test lint format clean run docker-up docker-down migrate mlflow

help: ## Show this help message
	@echo 'Usage: make [target]'
	@echo ''
	@echo 'Available targets:'
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  %-20s %s\n", $$1, $$2}' $(MAKEFILE_LIST)

# Environment Setup
install: ## Install dependencies with UV
	uv pip install -e .

dev: ## Install dev dependencies
	uv pip install -e ".[dev]"

sync: ## Sync dependencies from lockfile
	uv pip sync

# Code Quality
lint: ## Run linting (ruff + mypy)
	ruff check app tests
	mypy app

format: ## Format code with black and ruff
	black app tests
	ruff check --fix app tests

test: ## Run tests
	pytest tests/ -v --cov=app --cov-report=html

test-unit: ## Run unit tests only
	pytest tests/unit -v

test-integration: ## Run integration tests
	pytest tests/integration -v

# Database
migrate: ## Run database migrations
	cd backend && alembic upgrade head

migrate-create: ## Create new migration
	cd backend && alembic revision --autogenerate -m "$(msg)"

migrate-rollback: ## Rollback last migration
	cd backend && alembic downgrade -1

# Running Services
run: ## Run FastAPI backend
	cd backend && uvicorn app.main:app --reload --port 8000

run-frontend: ## Run Streamlit frontend
	cd frontend && streamlit run app.py

run-celery: ## Run Celery worker
	cd backend && celery -A app.tasks.celery_app worker --loglevel=info

run-celery-beat: ## Run Celery beat scheduler
	cd backend && celery -A app.tasks.celery_app beat --loglevel=info

# Docker
docker-up: ## Start all Docker services
	docker-compose up -d

docker-down: ## Stop all Docker services
	docker-compose down

docker-build: ## Build Docker images
	docker-compose build

docker-logs: ## View Docker logs
	docker-compose logs -f

# MLflow
mlflow: ## Start MLflow UI
	mlflow ui --backend-store-uri sqlite:///mlflow.db --port 5000

mlflow-serve: ## Serve a model
	mlflow models serve -m models:/pricing-model/Production -p 5001

# Data
download-data: ## Download sample data
	python scripts/download_sample_data.py

process-data: ## Process raw data
	python scripts/process_data.py

# Monitoring
metrics: ## View Prometheus metrics
	@echo "Metrics available at http://localhost:8000/metrics"

# Cleanup
clean: ## Clean build artifacts
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name ".ruff_cache" -exec rm -rf {} +
	find . -type d -name "htmlcov" -exec rm -rf {} +
	find . -type f -name ".coverage" -delete
	find . -type f -name "coverage.xml" -delete

clean-all: clean ## Clean everything including venv and data
	rm -rf .venv
	rm -rf data/processed/*
	rm -rf models/*

# Pre-commit
pre-commit: ## Run pre-commit hooks
	pre-commit run --all-files

pre-commit-install: ## Install pre-commit hooks
	pre-commit install

# All-in-one commands
setup: install migrate ## Complete setup (install + migrate)

dev-setup: dev pre-commit-install ## Complete dev setup

check: lint test ## Run all checks (lint + test)

deploy: check docker-build docker-up ## Deploy (check + build + up)
