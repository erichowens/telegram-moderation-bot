.PHONY: help install test lint format security build deploy clean

# Variables
PYTHON := python3
PIP := $(PYTHON) -m pip
PYTEST := $(PYTHON) -m pytest
BLACK := $(PYTHON) -m black
FLAKE8 := $(PYTHON) -m flake8
BANDIT := $(PYTHON) -m bandit
DOCKER := docker
COMPOSE := docker-compose

help: ## Show this help message
	@echo 'Usage: make [target]'
	@echo ''
	@echo 'Available targets:'
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  %-15s %s\n", $$1, $$2}' $(MAKEFILE_LIST)

install: ## Install dependencies
	$(PIP) install --upgrade pip
	$(PIP) install -r requirements.txt
	$(PIP) install pre-commit
	pre-commit install

test: ## Run all tests
	$(PYTEST) tests/ --ignore=tests/test_gui.py -v

test-coverage: ## Run tests with coverage report
	$(PYTEST) tests/ --ignore=tests/test_gui.py --cov=src --cov-report=html --cov-report=term

test-security: ## Run security tests only
	$(PYTEST) tests/test_security.py -v

lint: ## Run linters
	$(BLACK) --check src/ tests/
	$(FLAKE8) src/ tests/ --max-line-length=100 --extend-ignore=E203,W503
	$(PYTHON) -m mypy src/ --ignore-missing-imports

format: ## Format code with Black
	$(BLACK) src/ tests/

security: ## Run security checks
	$(BANDIT) -r src/ -ll
	$(PYTHON) -m safety check
	$(PYTHON) scripts/check_tokens.py

build: ## Build Docker image
	$(DOCKER) build -t telegram-mod-bot:latest .

build-no-cache: ## Build Docker image without cache
	$(DOCKER) build --no-cache -t telegram-mod-bot:latest .

run-docker: ## Run bot in Docker
	$(COMPOSE) up -d

stop-docker: ## Stop Docker containers
	$(COMPOSE) down

logs: ## Show Docker logs
	$(COMPOSE) logs -f telegram-bot

deploy-staging: ## Deploy to staging environment
	./scripts/deploy.sh staging

deploy-production: ## Deploy to production environment
	./scripts/deploy.sh production

clean: ## Clean up generated files
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	rm -rf .pytest_cache
	rm -rf htmlcov
	rm -rf .coverage
	rm -rf .mypy_cache
	rm -rf dist
	rm -rf build
	rm -rf *.egg-info

pre-commit: ## Run pre-commit hooks
	pre-commit run --all-files

setup-hooks: ## Setup git hooks
	pre-commit install
	pre-commit install --hook-type commit-msg

health-check: ## Check bot health (requires running bot)
	@echo "Checking bot health..."
	@curl -s http://localhost:8080/health || echo "Bot is not running or health endpoint not available"

monitor: ## Start monitoring stack (Prometheus + Grafana)
	$(COMPOSE) --profile monitoring up -d

backup: ## Backup bot data and configuration
	@echo "Creating backup..."
	@mkdir -p backups
	@tar -czf backups/backup-$$(date +%Y%m%d-%H%M%S).tar.gz config/ logs/ models/
	@echo "Backup created in backups/"

restore: ## Restore from latest backup
	@echo "Restoring from latest backup..."
	@tar -xzf $$(ls -t backups/*.tar.gz | head -1)
	@echo "Restore complete"

update-deps: ## Update dependencies to latest versions
	$(PIP) list --outdated
	$(PIP) install --upgrade -r requirements.txt

check-deps: ## Check for security vulnerabilities in dependencies
	$(PIP) install pip-audit
	pip-audit

generate-docs: ## Generate documentation
	$(PIP) install sphinx sphinx-rtd-theme
	sphinx-quickstart docs/
	sphinx-apidoc -o docs/source src/
	cd docs && make html

version: ## Show version information
	@echo "Python version:"
	@$(PYTHON) --version
	@echo "\nInstalled packages:"
	@$(PIP) list | grep -E "(telegram|torch|transformers)"

.DEFAULT_GOAL := help