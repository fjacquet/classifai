.PHONY: help install dev test lint format check clean run watch web docs

# Default target
help:
	@echo "ClassifAI - Development Commands"
	@echo ""
	@echo "Setup:"
	@echo "  make install    Install production dependencies"
	@echo "  make dev        Install development dependencies"
	@echo ""
	@echo "Quality:"
	@echo "  make test       Run tests with coverage"
	@echo "  make lint       Run linter (ruff check)"
	@echo "  make format     Format code (ruff format)"
	@echo "  make check      Run lint + test"
	@echo ""
	@echo "Run:"
	@echo "  make run        Show CLI help"
	@echo "  make watch      Start file watcher"
	@echo "  make web        Start Streamlit UI"
	@echo ""
	@echo "Docs:"
	@echo "  make docs       Build documentation"
	@echo "  make docs-serve Serve documentation locally"
	@echo ""
	@echo "Misc:"
	@echo "  make clean      Remove build artifacts"

# Setup
install:
	uv pip install -e .

dev:
	uv pip install -e ".[dev]"

# Quality
test:
	uv run pytest

lint:
	uv run ruff check .

format:
	uv run ruff format .

check: lint test

# Run
run:
	uv run classifai --help

watch:
	@echo "Usage: make watch SRC=/path/to/source DEST=/path/to/dest"
	@test -n "$(SRC)" || (echo "Error: SRC not set" && exit 1)
	uv run classifai watch --source-dir "$(SRC)" --destination-dir "$(DEST)"

web:
	uv run streamlit run src/classifai/classifai_app.py

# Docs
docs:
	uv run mkdocs build

docs-serve:
	uv run mkdocs serve

# Cleanup
clean:
	rm -rf build/ dist/ *.egg-info/ .pytest_cache/ .ruff_cache/
	rm -rf .coverage coverage.xml htmlcov/ site/
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
