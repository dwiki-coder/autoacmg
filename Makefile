.PHONY: install dev-install test lint format clean build docker-build docker-run help

SHELL := /bin/bash
PROJECT_NAME := autoacmg
PYTHON := python3
PYTEST := pytest

install: ## Install dependencies
	$(PYTHON) -m pip install .

dev-install: ## Install in development mode with dev dependencies
	$(PYTHON) -m pip install -e ".[dev,api,report]"

test: ## Run tests
	$(PYTEST) tests/ -v --tb=short

test-cov: ## Run tests with coverage
	$(PYTEST) tests/ -v --tb=short --cov=$(PROJECT_NAME) --cov-report=html

lint: ## Run linters
	ruff check $(PROJECT_NAME)/
	mypy $(PROJECT_NAME)/

format: ## Format code
	black $(PROJECT_NAME)/ tests/
	ruff check $(PROJECT_NAME)/ --fix

clean: ## Clean build artifacts
	rm -rf build/ dist/ *.egg-info .pytest_cache .mypy_cache __pycache__
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

docker-build: ## Build Docker image
	docker build -t $(PROJECT_NAME):latest .

docker-run: ## Run the API server in Docker
	docker-compose up -d

docker-stop: ## Stop Docker containers
	docker-compose down

demo: ## Run a demo classification
	autoacmg classify data/sample_input.vcf -o demo_results.json -f json --no-annotate
	autoacmg report demo_results.json -o demo_report.html -f html

help: ## Show help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

.DEFAULT_GOAL := help
