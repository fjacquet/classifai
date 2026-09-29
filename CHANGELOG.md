# Changelog

All notable changes to ClassifAI will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- `classifai watch` accepts `--ollama-model/-ai`, `--ollama-url/-url`, `--rename-files/-r`,
  `--use-vision/-uv` and `--language-subfolders/-ls`
- Watch mode waits until a file's size is stable, handles renames (download to a temporary
  name, then rename), ignores hidden, Office lock, temporary (`.part`, `.crdownload`, …) and
  unsupported files, and processes files on a worker thread
- Scanned PDFs are OCRed (first 3 pages) when neither PyMuPDF nor `pdftotext` finds a text
  layer; OCR uses `fra+eng+deu` when the language packs are installed
- Ollama structured outputs: JSON schemas constrain the category to `categories.yaml` and the
  AI sector fallback to `sectors.yaml`
- Identical content already at the destination (SHA-256) is skipped instead of duplicated
- `online_geocoding` setting in `config/settings.yaml` (default `false`)
- Startup validation of unknown rule condition types and metadata match operators

### Changed
- Issuers are matched after accent folding and punctuation normalization, on whole words, and
  filed under the canonical name from `sector_issuer_mapping.yaml` (one `UBS` folder for
  `UBS AG` and `UBS Switzerland AG`)
- LLM calls use `temperature: 0`, `num_ctx: 8192`, `keep_alive: 10m`, a 120 s timeout, and
  retry 5xx responses as well as network errors; document text is fenced and truncated
  head + tail to 4000 characters; the model is skipped when no text was extracted
- Reverse geocoding of photo GPS coordinates (Nominatim) is opt-in, cached and limited to
  1 request/second
- Renamed files use the first valid date among the model's answer and the file metadata
- Recursive scans skip a destination nested inside the source; scans skip hidden, Office lock
  and unsupported files
- `pdftotext` and `pandoc` run with a 60 s timeout; EML parsing honours declared charsets and
  falls back to the HTML body; archives are listed instead of extracted
- `unknown_issuers.yaml` and `logs/history.json` are written atomically; destination names are
  reserved with an exclusive create
- Rule validation raises `ConfigurationError` (the CLI exits with code 1) instead of calling
  `sys.exit`
- `core/` no longer logs; `core/parsing.py` moved to `infrastructure/parser_registry.py`
- Documentation aligned with the code (README, user guide, PRD, ADRs, CLAUDE.md)

### Fixed
- `classifai watch` failed on every file (incomplete scan configuration)
- `--ollama-model` / `--ollama-url` and the Web UI model/URL inputs were ignored
- Vision images are sent base64-encoded (Ollama rejected the previous encoding)
- The `aliases:` section of `sector_issuer_mapping.yaml` was ignored
- `kb-list-unknown` could not read the format written by the unknown-issuer recorder
- Unknown issuers were counted twice per document
- Rule matches no longer create nested `N/A/` folders; the photo layout triggers on the `Images`
  category
- The AI sector fallback can no longer create sectors outside `sectors.yaml`

### Removed
- Unwired FastAPI app (`src/classifai/app/api.py`), duplicate Streamlit UI (`app/web_ui.py`),
  `src/classifai/main.py` dispatcher and `core/classification.py`
- Dependencies: `fastapi`, `uvicorn`, `python-multipart`, `litellm`, `ollama`, `langdetect`,
  `pydantic-settings`
- `OLLAMA_EMBEDDING_MODEL_NAME` from `.env.example` (unused)

## [0.2.2] - 2026-09-13

### Fixed
- Dependencies: `gitpython` bumped to 3.1.62 and full `uv.lock` refresh
- CI and Security workflows trigger on `main`; `actions/first-interaction@v3` inputs

### Changed
- Python blocks in Markdown reformatted to satisfy `ruff format`

## [0.2.1] - 2026-08-01

### Changed
- Documentation restructured into a User Guide, PRD and ADRs
- CI standardized on `fjacquet/ci@v1`; docs deployed to GitHub Pages from `main`
- Standard status badges in the README
- Full `uv.lock` upgrade to clear Dependabot alerts

## [0.2.0] - 2026-04-18

### Added
- **CLI/Streamlit Consistency**
  - New `defaults.py` module with shared default values between CLI and Streamlit
  - `--quiet-llm` / `-ql` flag to suppress DEBUG logs from LLM module
  - Confirmation dialog in Streamlit before move/copy operations
  - File logging support in Streamlit (logs to `logs/main.log`)
- **MIME Type Detection & Rich Metadata Extraction**
  - `python-magic>=0.4.27` for accurate content-based MIME type detection
  - `pyexiftool>=0.5.6` for rich metadata extraction (PDF author, title, EXIF data, etc.)
  - Graceful degradation when system dependencies (libmagic, exiftool) are unavailable
  - `MetadataExtractionError` exception for metadata extraction failures
- **Two-Phase Rule Matching System**
  - Early rules: Match on filename/path patterns before file parsing (fast)
  - Full rules: Match on MIME type and metadata conditions after parsing
  - New rule condition types: `mime_type` (exact or prefix match like `image/*`)
  - New rule condition types: `metadata` (field/pattern matching with exact/contains/startswith/endswith/glob)
- **Enhanced LLM Classification**
  - Metadata hints added to LLM prompts (author, title, keywords, creation date)
  - Improves classification accuracy by providing document context
  - **Improved Category Selection Accuracy**
    - Categories now presented as a numbered list in prompts for better LLM comprehension
    - Explicit instructions to copy categories exactly without modification
    - Fuzzy matching fallback using `difflib.get_close_matches` with 85% threshold
    - Catches common LLM typos like 'Fichieurs Texte' → 'Fichiers Texte'
    - Logs corrections transparently for monitoring
- **Expanded Pandoc Support**
  - PowerPoint presentations (`.pptx`, `.ppt`)
  - OpenDocument presentations (`.odp`)
  - reStructuredText (`.rst`) for Python documentation
  - LaTeX documents (`.tex`, `.latex`)
  - Emacs Org-mode (`.org`)
  - E-books (`.epub`) and Markdown (`.md`) now in default extensions
- **New Packages**
  - `tenacity>=8.2.0` for declarative retry with exponential backoff
  - `pydantic-settings>=2.0` for type-safe configuration management
  - `pre-commit>=3.6.0` for automated code quality gates
- **Custom Exception Hierarchy** (`exceptions.py`)
  - `ClassifAIError` - Base exception
  - `ParsingError` - File parsing errors
  - `ClassificationError` - Classification errors
  - `FileOperationError` - File operations errors
  - `LLMError` - AI/Ollama API errors
  - `KnowledgeBaseError` - Knowledge base errors
  - `ConfigurationError` - Configuration errors
  - `ValidationError` - Data validation errors
- **Enhanced Utilities** (`utils.py`)
  - `sanitize_filename()` - Single source of truth for filename sanitization
  - `sanitize_path_component()` - Directory name sanitization
  - `parse_date_flexible()` - Multi-format date parsing
  - `format_date_for_filename()` - Date formatting for filenames
- **Pre-commit Configuration** (`.pre-commit-config.yaml`)
  - Ruff linting and formatting hooks
  - YAML formatting
  - Mypy type checking
  - Common issue detection
- **Thread-safe Localization** - Using `contextvars` instead of global mutable state
- **Pipeline Enhancement** - Added `process_single_file()` convenience function

### Changed
- **CLI/Streamlit Defaults Aligned**
  - `recursive` now defaults to `False` in both (was `True` in Streamlit)
  - `quiet_llm` now defaults to `False` in both (was `True` in Streamlit)
  - Destination directory now falls back to source directory in both interfaces
- **BREAKING**: Removed `returns` library - replaced with native Python exceptions
  - `Result[T, E]` replaced with direct returns or exception raising
  - `Success(value)` replaced with `return value`
  - `Failure(error)` replaced with `raise CustomException(error)`
  - `Maybe[T]` replaced with `T | None`
  - `@safe` decorator replaced with try/except blocks
  - `flow()` and `bind()` replaced with sequential function calls
- **Simplified Architecture**
  - Deleted duplicate `core/workflow.py` (use `pipeline.py`)
  - Deleted duplicate `infrastructure/knowledge.py` (use `knowledge_base.py`)
  - Deleted duplicate `app/cli.py` (use `classifai_cli.py`)
  - Removed monkey-patching in `__init__.py`
- **Updated Main Entry Point** (`main.py`) - Now uses `classifai_cli` directly
- **Updated API and Web UI** - Use native Python pattern instead of `returns`
- **CLAUDE.md** - Updated with new patterns, commit standards, quality checklist

### Fixed
- Added missing `config_dir` and `supported_extensions` to `AppConfig`
- Fixed category configuration mismatch in `knowledge_base.py` (list vs dict)
- Removed deprecated `KnowledgeBase` class usage from `pipeline.py` and `background_watcher.py`
- Updated all tests to use native Python instead of `returns` library

### Removed
- `returns` library dependency - replaced with native Python patterns
- Duplicate implementation files:
  - `src/classifai/core/workflow.py`
  - `src/classifai/infrastructure/knowledge.py`
  - `src/classifai/app/cli.py`

### Earlier 0.2.0 development (2024)

#### Added
- **Security**: Path traversal attack prevention in file uploads and archive extraction
- **Security**: Strict validation for tar and zip archive extraction
- **Feature**: Gemini generated image asset for project branding
- **Feature**: MkDocs documentation site with material theme
- **CI**: Auto-fix in ruff linter
- **CI**: MkDocs publish workflow
- **Docs**: Codecov badge in README

#### Changed
- Major architectural overhaul with functional programming patterns using `returns` library
- Improved readability of final_path assignment with line breaks

#### Fixed
- Removed unnecessary -U flag from uv sync command in CI workflow

## [0.1.0] - 2024

### Added
- **Core Features**
  - Hybrid classification using rule-based engine and AI models via Ollama
  - Hierarchical folder structure: `Language/Sector/Issuer/Category/Date_Title.ext`
  - AI-powered sector classification with knowledge base fallback
  - Custom rules engine with YAML configuration
  - Language detection and language-based subfolders

- **File Processing**
  - PDF parsing with PyMuPDF and pandoc fallback
  - Office document support (DOCX, XLSX)
  - Image OCR with Tesseract and optional vision model
  - MSG email file parsing
  - Archive extraction (ZIP, TAR) with security validation
  - Robust parsing with multiple fallback strategies

- **User Interfaces**
  - Streamlit web UI for configuration and preview
  - CLI with typer for scripting and automation
  - Dry-run, move, and copy operation modes
  - Undo functionality with operation history

- **Classification**
  - AI-powered file renaming with date and title extraction
  - Unknown issuer tracking and logging
  - Embedding classification support
  - Contextual classification with document analysis

- **Infrastructure**
  - Background watcher for automatic file processing
  - Recursive directory scanning
  - Vision model support for image classification
  - Functional pipeline with `returns` library for error handling

- **Configuration**
  - YAML-based configuration for categories, rules, and sectors
  - Sector-issuer mapping with alias support
  - Environment variable support for Ollama settings

- **Development**
  - Pytest test suite with coverage reporting
  - Property-based testing with Hypothesis
  - Ruff linting and formatting
  - GitHub Actions CI/CD pipeline
  - Dependency review workflow

### Dependencies
- Python 3.10+
- Ollama for local LLM inference
- Pandoc for document conversion
- Tesseract for OCR

## [0.0.1] - 2024

### Added
- Initial project structure and core functionality
- Basic file classification concept

---

[Unreleased]: https://github.com/fjacquet/classifai/compare/v0.2.2...HEAD
[0.2.2]: https://github.com/fjacquet/classifai/compare/v0.2.1...v0.2.2
[0.2.1]: https://github.com/fjacquet/classifai/compare/v0.2.0...v0.2.1
[0.2.0]: https://github.com/fjacquet/classifai/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/fjacquet/classifai/compare/v0.0.1...v0.1.0
[0.0.1]: https://github.com/fjacquet/classifai/releases/tag/v0.0.1
