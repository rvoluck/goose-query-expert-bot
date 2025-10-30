# Makefile for Goose Slackbot
# Provides convenient commands for development, testing, and deployment

.PHONY: help install test lint format clean docker migrate backup monitor

# Default target
.DEFAULT_GOAL := help

# Colors for output
BLUE := \033[0;34m
GREEN := \033[0;32m
YELLOW := \033[1;33m
RED := \033[0;31m
NC := \033[0m # No Color

help: ## Show this help message
	@echo "$(GREEN)Goose Slackbot - Available Commands$(NC)"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  $(BLUE)%-20s$(NC) %s\n", $$1, $$2}'
	@echo ""

# Installation and Setup
install: ## Install all dependencies
	@echo "$(YELLOW)Installing dependencies...$(NC)"
	pip install -r requirements.txt
	pip install -r tests/requirements.txt
	@echo "$(GREEN)✓ Dependencies installed$(NC)"

install-dev: ## Install development dependencies
	@echo "$(YELLOW)Installing development dependencies...$(NC)"
	pip install -r requirements.txt
	pip install -r tests/requirements.txt
	pip install black flake8 pylint mypy isort pre-commit
	pre-commit install
	@echo "$(GREEN)✓ Development environment ready$(NC)"

setup: ## Initial project setup
	@echo "$(YELLOW)Setting up project...$(NC)"
	cp .env.example .env || true
	mkdir -p logs backups archives migrations
	@echo "$(GREEN)✓ Project setup complete$(NC)"
	@echo "$(YELLOW)⚠ Remember to configure .env file$(NC)"

# Testing
test: ## Run all tests
	@echo "$(YELLOW)Running all tests...$(NC)"
	./scripts/run_tests.sh all

test-unit: ## Run unit tests only
	@echo "$(YELLOW)Running unit tests...$(NC)"
	./scripts/run_tests.sh unit

test-integration: ## Run integration tests only
	@echo "$(YELLOW)Running integration tests...$(NC)"
	./scripts/run_tests.sh integration

test-load: ## Run load tests
	@echo "$(YELLOW)Running load tests...$(NC)"
	./scripts/run_tests.sh load

test-parallel: ## Run tests in parallel
	@echo "$(YELLOW)Running tests in parallel...$(NC)"
	./scripts/run_tests.sh parallel

test-coverage: ## Run tests with coverage report
	@echo "$(YELLOW)Running tests with coverage...$(NC)"
	./scripts/run_tests.sh coverage
	@echo "$(GREEN)✓ Coverage report: htmlcov/index.html$(NC)"

test-watch: ## Run tests in watch mode
	@echo "$(YELLOW)Running tests in watch mode...$(NC)"
	pytest-watch

# Code Quality
lint: ## Run all linters
	@echo "$(YELLOW)Running linters...$(NC)"
	./scripts/run_tests.sh lint

format: ## Format code with black and isort
	@echo "$(YELLOW)Formatting code...$(NC)"
	black .
	isort .
	@echo "$(GREEN)✓ Code formatted$(NC)"

format-check: ## Check code formatting
	@echo "$(YELLOW)Checking code formatting...$(NC)"
	black --check .
	isort --check-only .

type-check: ## Run type checking with mypy
	@echo "$(YELLOW)Running type checks...$(NC)"
	mypy . --ignore-missing-imports

security-check: ## Run security checks
	@echo "$(YELLOW)Running security checks...$(NC)"
	pip-audit || true
	bandit -r . -ll || true

# Database Management
db-migrate: ## Run database migrations
	@echo "$(YELLOW)Running database migrations...$(NC)"
	./scripts/db_migrate.py up
	@echo "$(GREEN)✓ Migrations applied$(NC)"

db-rollback: ## Rollback last migration
	@echo "$(YELLOW)Rolling back migration...$(NC)"
	./scripts/db_migrate.py down
	@echo "$(GREEN)✓ Migration rolled back$(NC)"

db-status: ## Show migration status
	@echo "$(YELLOW)Database migration status:$(NC)"
	./scripts/db_migrate.py status

db-create-migration: ## Create new migration (use NAME=migration_name)
	@echo "$(YELLOW)Creating new migration...$(NC)"
	@if [ -z "$(NAME)" ]; then \
		echo "$(RED)Error: NAME parameter required$(NC)"; \
		echo "Usage: make db-create-migration NAME=add_user_roles"; \
		exit 1; \
	fi
	./scripts/db_migrate.py create --name "$(NAME)"

# User Management
users-list: ## List all users
	./scripts/user_manager.py list

users-create: ## Create new user (requires SLACK_ID and INTERNAL_ID)
	@if [ -z "$(SLACK_ID)" ] || [ -z "$(INTERNAL_ID)" ]; then \
		echo "$(RED)Error: SLACK_ID and INTERNAL_ID required$(NC)"; \
		echo "Usage: make users-create SLACK_ID=U123 INTERNAL_ID=user123"; \
		exit 1; \
	fi
	./scripts/user_manager.py create --slack-user-id $(SLACK_ID) --internal-user-id $(INTERNAL_ID)

users-export: ## Export users to CSV
	@echo "$(YELLOW)Exporting users...$(NC)"
	./scripts/user_manager.py export --file users_$(shell date +%Y%m%d).csv
	@echo "$(GREEN)✓ Users exported$(NC)"

# Monitoring
monitor: ## Run health checks
	@echo "$(YELLOW)Running health checks...$(NC)"
	./scripts/monitor.py check

monitor-metrics: ## Show system metrics
	./scripts/monitor.py metrics

monitor-continuous: ## Start continuous monitoring
	@echo "$(YELLOW)Starting continuous monitoring...$(NC)"
	./scripts/monitor.py monitor --interval 60

# Backup and Restore
backup: ## Create database backup
	@echo "$(YELLOW)Creating database backup...$(NC)"
	./scripts/backup_restore.py backup --compress
	@echo "$(GREEN)✓ Backup created$(NC)"

backup-list: ## List available backups
	./scripts/backup_restore.py list

backup-restore: ## Restore from backup (use FILE=backup_file)
	@if [ -z "$(FILE)" ]; then \
		echo "$(RED)Error: FILE parameter required$(NC)"; \
		echo "Usage: make backup-restore FILE=backups/backup_20240101.sql.gz"; \
		exit 1; \
	fi
	./scripts/backup_restore.py restore --file $(FILE)

backup-cleanup: ## Clean up old backups
	@echo "$(YELLOW)Cleaning up old backups...$(NC)"
	./scripts/backup_restore.py cleanup --keep-days 30 --keep-count 10

archive-data: ## Archive old data
	@echo "$(YELLOW)Archiving old data...$(NC)"
	./scripts/backup_restore.py archive-queries --archive-days 90
	./scripts/backup_restore.py archive-sessions --archive-days 180
	@echo "$(GREEN)✓ Data archived$(NC)"

# Docker Operations
docker-build: ## Build Docker image
	@echo "$(YELLOW)Building Docker image...$(NC)"
	docker build -t goose-slackbot:latest .
	@echo "$(GREEN)✓ Docker image built$(NC)"

docker-up: ## Start services with docker-compose
	@echo "$(YELLOW)Starting services...$(NC)"
	docker-compose up -d
	@echo "$(GREEN)✓ Services started$(NC)"

docker-down: ## Stop services
	@echo "$(YELLOW)Stopping services...$(NC)"
	docker-compose down
	@echo "$(GREEN)✓ Services stopped$(NC)"

docker-logs: ## Show service logs
	docker-compose logs -f

docker-ps: ## Show running containers
	docker-compose ps

docker-clean: ## Remove all containers and volumes
	@echo "$(YELLOW)Cleaning up Docker resources...$(NC)"
	docker-compose down -v
	docker system prune -f
	@echo "$(GREEN)✓ Docker resources cleaned$(NC)"

# Development
dev: ## Start development server
	@echo "$(YELLOW)Starting development server...$(NC)"
	python slack_bot.py

dev-watch: ## Start development server with auto-reload
	@echo "$(YELLOW)Starting development server with auto-reload...$(NC)"
	watchmedo auto-restart --patterns="*.py" --recursive -- python slack_bot.py

shell: ## Start Python shell with project context
	@echo "$(YELLOW)Starting Python shell...$(NC)"
	python -i -c "from config import settings; from database import *; print('Project context loaded')"

# Load Testing
load-test: ## Run load tests with Locust
	@echo "$(YELLOW)Starting Locust load test...$(NC)"
	@echo "$(GREEN)Open http://localhost:8089 in your browser$(NC)"
	cd tests/load && locust -f locustfile.py --host http://localhost:3000

load-test-headless: ## Run headless load test
	@echo "$(YELLOW)Running headless load test...$(NC)"
	cd tests/load && locust -f locustfile.py \
		--host http://localhost:3000 \
		--users 100 \
		--spawn-rate 10 \
		--run-time 5m \
		--headless

# Deployment
deploy-staging: ## Deploy to staging environment
	@echo "$(YELLOW)Deploying to staging...$(NC)"
	./scripts/deploy.sh staging
	@echo "$(GREEN)✓ Deployed to staging$(NC)"

deploy-production: ## Deploy to production environment
	@echo "$(RED)⚠ Deploying to production...$(NC)"
	@read -p "Are you sure? [y/N] " -n 1 -r; \
	echo; \
	if [[ $$REPLY =~ ^[Yy]$$ ]]; then \
		./scripts/deploy.sh production; \
		echo "$(GREEN)✓ Deployed to production$(NC)"; \
	else \
		echo "$(YELLOW)Deployment cancelled$(NC)"; \
	fi

# Kubernetes
k8s-apply: ## Apply Kubernetes manifests
	@echo "$(YELLOW)Applying Kubernetes manifests...$(NC)"
	kubectl apply -f k8s/
	@echo "$(GREEN)✓ Manifests applied$(NC)"

k8s-status: ## Show Kubernetes deployment status
	kubectl get all -n goose-slackbot

k8s-logs: ## Show Kubernetes logs
	kubectl logs -f -n goose-slackbot deployment/goose-slackbot

k8s-delete: ## Delete Kubernetes resources
	@echo "$(YELLOW)Deleting Kubernetes resources...$(NC)"
	kubectl delete -f k8s/
	@echo "$(GREEN)✓ Resources deleted$(NC)"

# Cleanup
clean: ## Clean up generated files
	@echo "$(YELLOW)Cleaning up...$(NC)"
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name ".coverage" -delete
	rm -rf htmlcov/ .pytest_cache/ .mypy_cache/ dist/ build/
	@echo "$(GREEN)✓ Cleanup complete$(NC)"

clean-all: clean docker-clean ## Clean everything including Docker resources
	@echo "$(GREEN)✓ Full cleanup complete$(NC)"

# Documentation
docs: ## Generate documentation
	@echo "$(YELLOW)Generating documentation...$(NC)"
	@echo "$(YELLOW)Documentation generation not yet implemented$(NC)"

docs-serve: ## Serve documentation locally
	@echo "$(YELLOW)Serving documentation...$(NC)"
	@echo "$(YELLOW)Documentation server not yet implemented$(NC)"

# Utilities
logs: ## Show application logs
	tail -f logs/app.log

logs-error: ## Show error logs only
	tail -f logs/app.log | grep ERROR

version: ## Show version information
	@echo "$(GREEN)Goose Slackbot$(NC)"
	@echo "Python: $$(python --version)"
	@echo "PostgreSQL: $$(psql --version | head -1)"
	@echo "Redis: $$(redis-cli --version)"
	@echo "Docker: $$(docker --version)"

env-check: ## Check environment configuration
	@echo "$(YELLOW)Checking environment...$(NC)"
	@python -c "from config import validate_required_settings; validate_required_settings(); print('$(GREEN)✓ Environment configured correctly$(NC)')" || echo "$(RED)✗ Environment configuration issues$(NC)"

# Quick commands
quick-test: test-unit ## Quick test (unit tests only)

quick-check: format-check lint ## Quick code quality check

ci: quick-check test-coverage ## Run CI pipeline locally

# All-in-one commands
all: install test lint ## Install, test, and lint

init: setup install db-migrate ## Initialize project from scratch
	@echo "$(GREEN)✓ Project initialized successfully$(NC)"
	@echo "$(YELLOW)Next steps:$(NC)"
	@echo "  1. Configure .env file"
	@echo "  2. Run 'make dev' to start development server"
	@echo "  3. Run 'make test' to verify setup"
