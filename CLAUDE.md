# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

ClassifAI is a Python application that automatically organizes files using hybrid rule-based logic and local AI models via Ollama. It classifies documents by extracting metadata (issuer, category, date, language) and organizes them into a structured folder hierarchy: `Language/Sector/Issuer/Category/Date_Title.ext`

## Commands

### Development Setup

```bash
uv pip install -e ".[dev]"   # Or: make dev
```

### Makefile Shortcuts

Preferred for common tasks — see `make help`:

```bash
make dev        # Install dev dependencies
make check      # Run lint + tests
make format     # Auto-format with ruff
make web        # Launch Streamlit UI
make watch SRC=/path DEST=/path   # Run watcher
```

### Running the Application

```bash
# CLI
uv run classifai run --source-dir /path/to/files --mode dry-run|move|copy

# Streamlit Web UI
streamlit run src/classifai/classifai_app.py

# Watch mode (monitor directory for new files)
uv run classifai watch --source-dir /path --destination-dir /path
```

### Testing

```bash
pytest                           # Run all tests with coverage
pytest tests/test_cli.py         # Run specific test file
pytest -k "test_function_name"   # Run specific test by name
pytest -x                        # Stop on first failure
```

### Linting and Formatting

```bash
ruff check .                     # Lint
ruff check --fix .               # Lint and auto-fix
ruff format .                    # Format code
yamlfix config/                  # Format YAML files
```

## Architecture

### Functional Pipeline Design

The codebase uses functional programming patterns with native Python exceptions for error handling. The main pipeline flows through:

1. **Rule-based classification** (`core/rules.py`) - Fast pattern matching via YAML rules
2. **File parsing** (`infrastructure/parsing.py`, `infrastructure/file_system.py`) - Extract text from PDFs, images (OCR), Office docs
3. **AI enrichment** (`infrastructure/llm.py`) - Ollama API calls with tenacity retry logic
4. **Knowledge base lookup** (`infrastructure/knowledge_base.py`) - Map issuers to sectors via `config/sector_issuer_mapping.yaml`
5. **Path determination** (`core/logic.py`) - Build final destination path

### Key Data Types

- `FileContext` (`core/types.py`) - Frozen Pydantic model carrying file state through the pipeline
- `AIResponse` (`core/types.py`) - Validated structure for LLM responses
- Custom exceptions (`exceptions.py`) - `ClassifAIError`, `ParsingError`, `LLMError`, `FileOperationError`, etc.

### Module Organization

```
src/classifai/
├── core/                 # Pure business logic (classification, rules, path logic)
├── infrastructure/       # I/O operations (LLM, file system, knowledge base)
├── app/                  # FastAPI routes
├── classifai_cli.py      # Typer CLI entry point (→ `classifai` console script)
├── classifai_app.py      # Streamlit UI entry point
├── pipeline.py           # Main orchestration
├── background_watcher.py # Watchdog-based directory monitor
├── entrypoint_utils.py   # Shared CLI/Streamlit helpers
├── localization.py       # User-facing string translations (FR/EN)
├── validation.py         # Input validation helpers
├── config.py             # Centralized config loading from YAML + env vars
├── defaults.py           # Shared defaults for CLI and Streamlit consistency
├── exceptions.py         # Custom exception hierarchy
└── utils.py              # Shared utilities (sanitize_filename, date parsing)
```

### Configuration

- **YAML configs** in `config/`: categories.yaml, rules.yaml, sectors.yaml, sector_issuer_mapping.yaml
- **Environment variables**: `OLLAMA_MODEL_NAME`, `OLLAMA_API_URL`, `OLLAMA_VISION_MODEL_NAME`
- Config is loaded once as frozen `AppConfig` dataclass in `config.py`

### Testing Patterns

- Uses `pytest-mock` for mocking infrastructure calls
- Property-based testing with `hypothesis` in `tests/property/`
- Test fixtures create temporary directories for file operations

## Code Style

- Line length: 110 characters
- Ruff rules: E, F, W, I, UP, N, B, A, COM, C4, DTZ, T20, PT, RET, SIM
- First-party imports: `classifai`
- French language used for UI text and category/sector translations

## Design Principles

This codebase adheres to **KISS**, **DRY**, and **FP** principles. All contributions must follow these guidelines.

### KISS (Keep It Simple, Stupid)

**Do:**

- One function, one responsibility
- Prefer explicit over clever code
- Use standard library solutions when available
- Keep function signatures simple (max 5 parameters)

**Don't:**

- Create duplicate implementations (use existing `pipeline.py`)
- Over-engineer with unnecessary abstractions
- Use complex nested code - extract to named functions instead

```python
# Bad: Complex inline code
result = [transform(process(item)) for item in data if validate(item)]

# Good: Named functions for clarity
def process_valid_items(data):
    valid_items = filter(validate, data)
    processed = map(process, valid_items)
    return list(map(transform, processed))
```

### DRY (Don't Repeat Yourself)

**Existing utilities to reuse:**

- `utils.sanitize_filename()` - Use for ALL filename/path sanitization (don't inline `"".join(c for c in ...)`)
- `config.app_config` - Single source for configuration (don't reload YAML files)
- `localization.get_text()` - All user-facing strings

**Patterns to follow:**

```python
# Bad: Repeated sanitization pattern
safe_name = "".join(c for c in name if c.isalnum() or c in " -_").strip()

# Good: Use the utility function
from classifai.utils import sanitize_filename
safe_name = sanitize_filename(name)

# Bad: Multiple context update styles
context.__class__(**{**context.__dict__, "field": value})  # Don't use
context.copy(update={"field": value})  # Deprecated

# Good: Use model_copy (Pydantic v2)
updated = context.model_copy(update={"field": value})
```

**Avoid duplicating:**

- Date parsing logic - use centralized date utilities
- File extension checks - reference `app_config.supported_extensions`
- Error message formatting - use `localization` module

### FP (Functional Programming)

**Core patterns used:**

- Immutable data with frozen Pydantic models
- Custom exceptions for error handling (from `classifai.exceptions`)
- Thread-safe state with `contextvars`
- Tenacity for declarative retry logic

**Rules:**

1. **Pure functions in `core/`** - No I/O, no logging, no side effects

```python
# Bad: Side effect in core module
def determine_path(context: FileContext) -> Path:
    logger.debug(f"Processing {context}")  # Side effect!
    return calculate_path(context)

# Good: Pure function, log at boundaries
def determine_path(context: FileContext) -> Path:
    return calculate_path(context)
```

2. **Use custom exceptions** - From `classifai.exceptions`

```python
from classifai.exceptions import ParsingError, LLMError

def parse_file(path: Path) -> str:
    try:
        return extract_text(path)
    except OSError as e:
        raise ParsingError(f"Failed to parse {path}: {e}") from e
```

3. **Use tenacity for retries** - Declarative retry logic

```python
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(stop=stop_after_attempt(3), wait=wait_exponential(min=2, max=10))
def call_ollama(prompt: str) -> dict:
    return make_request(prompt)
```

4. **No global mutable state** - Use contextvars or dependency injection

```python
from contextvars import ContextVar

# Thread-safe state
_language: ContextVar[Language] = ContextVar('lang', default=Language.EN)

def set_language(lang: Language) -> None:
    _language.set(lang)
```

5. **Immutable updates** - Never mutate `FileContext`

```python
# FileContext is frozen - always create new instances
new_context = context.model_copy(update={"category": "Invoices"})
```

### Quick Reference

| Principle | Check Before Committing                                              |
| --------- | -------------------------------------------------------------------- |
| KISS      | Is there a simpler way? Does similar code already exist?             |
| DRY       | Am I duplicating logic? Should this be a utility function?           |
| FP        | Is this function pure? Am I mutating state? Did I use exceptions?    |

## Commit Standards

**Format**: `type(scope): description`

**Types**: `feat`, `fix`, `refactor`, `docs`, `test`, `chore`, `perf`, `security`

**Examples**:
- `feat(parser): add MSG email file support`
- `fix(llm): handle timeout in Ollama API calls`
- `refactor(config): migrate to pydantic-settings`

**Footer** (required):
```
🤖 Generated with [Claude Code](https://claude.ai/code)

Co-Authored-By: Claude <noreply@anthropic.com>
```

## Quality Standards

- **First-attempt compilation** - Code must run without syntax errors
- **Zero type errors** - Use proper type hints throughout
- **Comprehensive docstrings** - Google style for all public functions
- **Test coverage** - New code requires tests

## Pre-Commit Checklist

1. `pre-commit run --all-files` passes (runs ruff, mypy, yamlfmt, file checks)
2. `pytest` passes
3. No `returns` library imports
4. Custom exceptions used for errors
5. Proper commit message format

**Never disable a failing quality gate (mypy, ruff, hook, test) to unblock a commit.** Fix the underlying issue.

<!-- code-review-graph MCP tools -->
## MCP Tools: code-review-graph

**IMPORTANT: This project has a knowledge graph. ALWAYS use the
code-review-graph MCP tools BEFORE using Grep/Glob/Read to explore
the codebase.** The graph is faster, cheaper (fewer tokens), and gives
you structural context (callers, dependents, test coverage) that file
scanning cannot.

### When to use graph tools FIRST

- **Exploring code**: `semantic_search_nodes` or `query_graph` instead of Grep
- **Understanding impact**: `get_impact_radius` instead of manually tracing imports
- **Code review**: `detect_changes` + `get_review_context` instead of reading entire files
- **Finding relationships**: `query_graph` with callers_of/callees_of/imports_of/tests_for
- **Architecture questions**: `get_architecture_overview` + `list_communities`

Fall back to Grep/Glob/Read **only** when the graph doesn't cover what you need.

### Key Tools

| Tool | Use when |
|------|----------|
| `detect_changes` | Reviewing code changes — gives risk-scored analysis |
| `get_review_context` | Need source snippets for review — token-efficient |
| `get_impact_radius` | Understanding blast radius of a change |
| `get_affected_flows` | Finding which execution paths are impacted |
| `query_graph` | Tracing callers, callees, imports, tests, dependencies |
| `semantic_search_nodes` | Finding functions/classes by name or keyword |
| `get_architecture_overview` | Understanding high-level codebase structure |
| `refactor_tool` | Planning renames, finding dead code |

### Workflow

1. The graph auto-updates on file changes (via hooks).
2. Use `detect_changes` for code review.
3. Use `get_affected_flows` to understand impact.
4. Use `query_graph` pattern="tests_for" to check coverage.
