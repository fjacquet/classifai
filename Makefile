# ClassifAI Development Makefile — fjacquet/ci standard interface (do not rename canonical targets)
.DEFAULT_GOAL := all
DIST ?= dist

.PHONY: all clean install tools lint format test build vuln sbom security docs coverage-upload release ci help dev run watch web docs-serve

help:
	@echo "ClassifAI - Development Commands"
	@echo ""
	@echo "Setup:"
	@echo "  make install    Sync all dependencies with uv"
	@echo "  make tools      Alias for install (fjacquet/ci canonical target)"
	@echo "  make dev        Install development dependencies (editable)"
	@echo ""
	@echo "Quality:"
	@echo "  make lint       Run ruff check + format --check"
	@echo "  make format     Format code (ruff format)"
	@echo "  make test       Run tests with coverage (xml + term-missing)"
	@echo "  make build      Build distributable wheel/sdist"
	@echo "  make all        clean + lint + test + build"
	@echo "  make ci         lint + test + build (CI alias)"
	@echo ""
	@echo "Security:"
	@echo "  make vuln       OSV vulnerability scan against uv.lock"
	@echo "  make sbom       Generate CycloneDX SBOM to dist/sbom.cdx.json"
	@echo "  make security   Semgrep SAST scan (advisory; non-blocking)"
	@echo "  make coverage-upload  Upload coverage.xml to Codecov"
	@echo ""
	@echo "Run:"
	@echo "  make run        Show CLI help"
	@echo "  make watch      Start file watcher (SRC=... DEST=...)"
	@echo "  make web        Start Streamlit UI"
	@echo ""
	@echo "Docs:"
	@echo "  make docs       Build MkDocs documentation (strict) to site/"
	@echo "  make docs-serve Serve documentation locally"
	@echo ""
	@echo "Misc:"
	@echo "  make clean      Remove build artifacts"

all: clean lint test build

clean:
	rm -rf $(DIST) site .coverage coverage.xml *.sarif build/ *.egg-info/ .pytest_cache/ .ruff_cache/ htmlcov/
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true

install:
	uv sync --all-extras --all-groups

tools: install

# Editable install for local development
dev:
	uv pip install -e ".[dev]"

lint:
	uv run ruff check .
	uv run ruff format --check .

format:
	uv run ruff format .

test:
	uv run pytest --cov --cov-report=xml --cov-report=term-missing

build:
	uv build

vuln:
	uvx osv-scanner scan --lockfile=uv.lock || true

sbom:
	mkdir -p $(DIST)
	uv run cyclonedx-py environment --output-format JSON --output-file $(DIST)/sbom.cdx.json

security:  # advisory: reports findings but never blocks the build (CodeQL/osv are the blocking gates)
	uvx semgrep scan --config auto --skip-unknown-extensions || true

docs:
	uv run mkdocs build --strict --site-dir site

coverage-upload:
	uvx --from codecov-cli codecov upload-process --file coverage.xml || true

release:
	uv build
	uv publish --trusted-publishing always

ci: lint test build

# --- Repo-specific run targets ---
run:
	uv run classifai --help

watch:
	@echo "Usage: make watch SRC=/path/to/source DEST=/path/to/dest"
	@test -n "$(SRC)" || (echo "Error: SRC not set" && exit 1)
	uv run classifai watch --source-dir "$(SRC)" --destination-dir "$(DEST)"

web:
	uv run streamlit run src/classifai/classifai_app.py

docs-serve:
	uv run mkdocs serve
