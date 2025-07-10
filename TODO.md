## 5. Architecture Refinement (Post-MVP)

- [x] **Embeddings Implementation**:
  - [x] Create `embedding_module.py` to generate embeddings for text content.
  - [x] Implement logic to compare document embeddings with category embeddings.
  - [x] Add a new classification mode (`--mode embeddings`) to the CLI.
- [ ] **Documentation**:
  - [x] Rename `docs/EMBEDDINGS.md` to `docs/ARCHITECTURE.md`.
  - [x] Update `docs/ARCHITECTURE.md` to reflect the current technology stack and the new hybrid classification strategy.

## 6. Parsing and Classification Refinement (Post-MVP)

- [x] **Robust Parsing**:
  - [x] Implement hierarchical parsing logic (specific parser -> generic text -> metadata fallback).
  - [x] Create a generic text parser for unrecognized but text-like file types.
  - [x] Improve image parser to handle OCR failures gracefully (no text found is not an error).
- [x] **Classification Fallback**:
  - [x] Update classification module to use filename and metadata when text content is empty.
- [x] **Configuration**:
  - [x] Add configuration for generic text file extensions.
  - [ ] Add configuration to enable/disable vision model usage for images.

## 7. Streamlit UI (Post-MVP)

- [ ] Create `classifai_app.py`.
- [ ] Build the main configuration screen.
- [ ] Implement the "Scan" functionality.
- [ ] Develop the "Preview & Validation" section.
  - [ ] Display proposed classifications, language, and new filenames.
  - [ ] Allow manual override of all suggested attributes.
- [ ] Add action buttons ("Move", "Copy").
- [ ] Implement progress bars and a real-time log display.
- [ ] Write functional tests for the Streamlit app.

## 8. Advanced Features (Future)

- [ ] **Language-Based Organization**:
  - [ ] Integrate a language detection library (e.g., `langdetect`).
  - [ ] Update file operations to create language-based subfolders (`/en`, `/fr`).
- [ ] **AI-Powered Renaming**:
  - [ ] Enhance Ollama prompts to extract issuer, date, and a short title.
  - [ ] Implement structured file renaming logic.
- [ ] **History and Undo**:
  - [ ] Create `history_module.py` to log all file operations.
  - [ ] Implement an `undo` command.
- [ ] **Custom Rules**:
  - [ ] Implement a rules engine for pre-classification based on filename or path.
- [ ] **Background Watching**:
  - [ ] Implement a background process to watch a folder for new files.
- [ ] **Vision Model Integration**:
  - [ ] Integrate `ollama/llava` for advanced image classification.
- [ ] **Expanded Format Support**:
  - [ ] Add support for audio and video transcription.
  - [ ] Add support for parsing archive contents (`.zip`, etc.).

---

## Completed Tasks

### 1. Environment Setup

- [x] Install Ollama and pull a base model (e.g., `gemma3n`).
- [x] Initialize project structure (source, tests, docs).
- [x] Set up `uv` for dependency management.
- [x] Configure `pytest`, `pytest-mock`, `faker`, and `coverage.py`.
- [x] Configure `ruff` for linting and formatting.
- [x] Configure `yamlfix` for YAML files.
- [x] Create `.env.example` and add `.env` to `.gitignore`.

### 2. Core Logic Modules (MVP)

- [x] **`parsing_module.py`**:
  - [x] Implement PDF parsing (`PyMuPDF`).
  - [x] Implement basic text file parsing (.txt, .md).
  - [x] Implement Word document parsing (`python-docx`).
  - [x] Implement image OCR parsing (`Pillow`, `pytesseract`).
  - [x] Handle parsing errors gracefully.
- [x] **`ollama_classification_module.py`**:
  - [x] Load Ollama configuration from `.env` (`python-dotenv`).
  - [x] Interface with Ollama via `litellm`.
  - [x] Implement prompt engineering for classification.
  - [x] Handle API errors (server down, model not found).
- [x] **`file_operations_module.py`**:
  - [x] Implement file `move` logic.
  - [x] Implement file `copy` logic.
  - [x] Implement name conflict resolution (e.g., `file (1).txt`).
  - [x] Ensure all operations use absolute paths.
- [x] **`utils.py`**:
  - [x] Add any shared utility functions.
- [x] **`logging_module.py`**:
  - [x] Set up basic logging for operations and errors using `loguru`.

### 3. CLI Implementation (MVP)

- [x] Create `classifai_cli.py` (or similar).
- [x] Implement argument parsing (using `argparse` or `typer`).
  - [x] `-s, --source-dir`
  - [x] `-d, --destination-dir`
  - [x] `-m, --mode` (dry-run, move, copy)
  - [x] `-ai, --ollama-model`
  - [x] `-url, --ollama-url`
  - [x] `-v, --verbose`
  - [x] `--log-file`
- [x] Implement `dry-run` mode to display proposed changes.
- [x] Implement `move` and `copy` modes with user confirmation.
- [x] Display a post-execution summary.

### 4. Testing (MVP)

- [x] Write unit tests for `parsing_module.py`.
- [x] Write unit tests for `file_operations_module.py`.
- [x] Write unit tests for `ollama_classification_module.py` (using `pytest-mock` for `litellm`).
- [x] Write integration tests for the CLI workflow.
- [x] Aim for high test coverage (`>80%`).
