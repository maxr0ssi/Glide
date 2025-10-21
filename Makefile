# Glide Makefile
PYTHON := python3.10
VENV := venv
PIP := $(VENV)/bin/pip
PYTHON_VENV := $(VENV)/bin/python

# Default target
.DEFAULT_GOAL := help

# Help target
.PHONY: help
help:
	@echo "Glide Development Commands:"
	@echo "  make setup        - Create virtual environment and install dependencies"
	@echo "  make run          - Run both backend and HUD together"
	@echo "  make run-backend  - Run Python backend only (with preview)"
	@echo "  make run-headless - Run Python backend headless"
	@echo "  make run-hud      - Run Swift HUD only"
	@echo "  make build-hud    - Build Swift HUD"
	@echo "  make lint         - Run linters (ruff, black, mypy)"
	@echo "  make format       - Auto-format code"
	@echo "  make test         - Run tests"
	@echo "  make clean        - Clean build artifacts"
	@echo "  make models       - Download MediaPipe models"

# Setup virtual environment and dependencies
.PHONY: setup
setup: $(VENV)/bin/activate models

$(VENV)/bin/activate: requirements.txt requirements-macos.txt
	$(PYTHON) -m venv $(VENV)
	$(PIP) install --upgrade pip
	$(PIP) install -r requirements.txt
	$(PIP) install -r requirements-macos.txt
	@echo "✓ Virtual environment created and dependencies installed"
	@echo "Run 'source venv/bin/activate' to activate"

# Download MediaPipe models
.PHONY: models
models:
	$(PYTHON_VENV) setup_models.py

# Run backend with preview
.PHONY: run-backend
run-backend:
	$(PYTHON_VENV) -m glide.app.main

# Run backend headless
.PHONY: run-headless
run-headless:
	$(PYTHON_VENV) -m glide.app.main --headless

# Build Swift HUD
.PHONY: build-hud
build-hud:
	cd apps/hud-macos && swift build --configuration release

# Run Swift HUD
.PHONY: run-hud
run-hud:
	cd apps/hud-macos && swift run --configuration release

# Run both backend and HUD
.PHONY: run
run:
	@echo "Starting Glide with HUD..."
	@./scripts/run_with_hud.sh

# Development dependencies
.PHONY: dev-setup
dev-setup: setup
	@if [ -f requirements-dev.txt ]; then \
		$(PIP) install -r requirements-dev.txt; \
		echo "✓ Development dependencies installed"; \
	else \
		echo "⚠ No requirements-dev.txt found"; \
	fi

# Linting
.PHONY: lint
lint: dev-setup
	@echo "Running linters..."
	@if command -v $(VENV)/bin/ruff > /dev/null; then \
		$(VENV)/bin/ruff check glide/ tests/; \
	else \
		echo "⚠ ruff not installed - run 'make dev-setup'"; \
	fi
	@if command -v $(VENV)/bin/black > /dev/null; then \
		$(VENV)/bin/black --check --diff glide/ tests/; \
	else \
		echo "⚠ black not installed - run 'make dev-setup'"; \
	fi
	@if command -v $(VENV)/bin/mypy > /dev/null; then \
		$(VENV)/bin/mypy glide/; \
	else \
		echo "⚠ mypy not installed - run 'make dev-setup'"; \
	fi

# Auto-format code
.PHONY: format
format: dev-setup
	@echo "Formatting code..."
	@if command -v $(VENV)/bin/black > /dev/null; then \
		$(VENV)/bin/black glide/ tests/; \
	else \
		echo "⚠ black not installed - run 'make dev-setup'"; \
	fi
	@if command -v $(VENV)/bin/ruff > /dev/null; then \
		$(VENV)/bin/ruff check --fix glide/ tests/; \
	else \
		echo "⚠ ruff not installed - run 'make dev-setup'"; \
	fi

# Run tests
.PHONY: test
test: dev-setup
	@echo "Running tests..."
	@if command -v $(VENV)/bin/pytest > /dev/null; then \
		$(VENV)/bin/pytest tests/ -v; \
	else \
		echo "⚠ pytest not installed - run 'make dev-setup'"; \
	fi

# Clean build artifacts
.PHONY: clean
clean:
	@echo "Cleaning build artifacts..."
	@find . -type d -name "__pycache__" -exec rm -rf {} +
	@find . -type f -name "*.pyc" -delete
	@find . -type f -name "*.pyo" -delete
	@find . -type f -name ".DS_Store" -delete
	@rm -rf .pytest_cache
	@rm -rf .mypy_cache
	@rm -rf .ruff_cache
	@rm -rf build/ dist/ *.egg-info
	@cd apps/hud-macos && swift package clean
	@echo "✓ Cleaned"

# Kill any running processes on port 8765
.PHONY: kill-port
kill-port:
	@echo "Killing processes on port 8765..."
	@lsof -ti:8765 | xargs kill -9 2>/dev/null || true

# Watch for file changes (requires fswatch)
.PHONY: watch
watch:
	@if command -v fswatch > /dev/null; then \
		fswatch -o glide/ | xargs -n1 -I{} make lint; \
	else \
		echo "Install fswatch to use watch mode: brew install fswatch"; \
	fi
