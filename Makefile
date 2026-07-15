.PHONY: _check-tools _sync setup clean upgrade test check lint format format-check typecheck build

.DEFAULT_GOAL := help

help: ## Show this help message
	@awk 'BEGIN {FS = ":.*## "; printf "Usage: make <target>\n\nTargets:\n"} /^[a-zA-Z0-9_-]+:.*## / {printf "  %-18s %s\n", $$1, $$2}' $(MAKEFILE_LIST)

# Internal target: install all project dependencies.
_sync:
	@uv sync --all-groups --all-extras

# Internal target: verify tools required by the setup workflow.
_check-tools:
	@set -e; \
	missing_tools=""; \
	for tool in uv git; do \
		if ! command -v $$tool >/dev/null 2>&1; then \
			echo "Error: prerequisite '$$tool' is not installed."; \
			missing_tools="$$missing_tools $$tool"; \
		fi; \
	done; \
	if [ -n "$$missing_tools" ]; then \
		echo "Install the missing prerequisite(s) and run 'make setup' again."; \
		exit 1; \
	fi

setup: _check-tools _sync ## Set up dependencies, Git, and prek hooks
	@if [ ! -d ".git" ]; then \
		echo "Setting up git..."; \
		git init -b main > /dev/null; \
	fi

	@echo "Setting up prek hooks..."
	@uv run prek install --hook-type pre-commit --hook-type commit-msg --hook-type pre-push

	@echo "Setup completed successfully!"

clean: ## Remove generated files and caches
	@echo "Cleaning up project artifacts..."
	@find . -type d \( -name .git -o -name .venv \) -prune -o \( \
		-name "__pycache__" -o \
		-name ".ipynb_checkpoints" -o \
		-name ".mypy_cache" -o \
		-name ".pytest_cache" -o \
		-name ".ruff_cache" -o \
		-name "build" -o \
		-name "dist" -o \
		-name "site" -o \
		-name "*.egg-info" -o \
		-name ".coverage" \) -print -exec rm -rf {} + 2>/dev/null || true
	@find . -type f \( -name ".coverage" -o -name ".coverage.*" \) -not -path "./.git/*" -not -path "./.venv/*" -delete 2>/dev/null || true
	@echo "Cleanup completed."

upgrade: ## Upgrade dependencies and prek hooks
	@echo "Upgrading dependencies..."
	@uv lock --upgrade
	@uv sync --all-groups --all-extras
	@echo "Upgrading prek hooks..."
	@uv run prek autoupdate
	@echo "Upgrade completed successfully!"

test: _sync ## Run tests with coverage
	@uv run pytest -v tests --cov=src --cov-report=term-missing

check: _sync ## Run all prek hooks against every file
	@uv run prek run --all-files

lint: _sync ## Check the code with Ruff
	@uv run ruff check .

format: _sync ## Format the code with Ruff
	@uv run ruff format .

format-check: _sync ## Check Ruff formatting without changing files
	@uv run ruff format --check .

typecheck: _sync ## Check types with Pyright
	@uv run pyright

build: _sync ## Build the package
	@uv build
