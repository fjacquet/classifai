# ClassifAI - TODO

This document tracks the remaining tasks and the history of completed work for the ClassifAI project.

---

## Remaining Tasks

### 1. Finalizing Core Functionality

- [x] **Structured Renaming & Organization**:
  - [x] Implement the full folder structure: `Langue/Émetteur/Catégorie/`.
  - [x] Ensure the filename format `Date_Titre_Court_Document.ext` is correctly applied.
  - [ ] Ensure the filename format `Date_Titre_Court_Document.ext` is correctly applied.
- [ ] **Expanded Format Support**:
  - [ ] Add a dedicated parser for `.msg` files using the `extract-msg` library.
  - [ ] Re-attempt robust integration of audio/video transcription (deferred).

---

## Completed Tasks

### 1. Environment & Core Setup

- [x] Install Ollama and pull a base model.
- [x] Initialize project structure (source, tests, docs).
- [x] Set up `uv` for dependency management.
- [x] Configure `pytest`, `pytest-mock`, `faker`, and `coverage.py`.
- [x] Configure `ruff` for linting and formatting.
- [x] Configure `yamlfix` for YAML files.
- [x] Create `.env.example` and add `.env` to `.gitignore`.
- [x] Implement core logic modules (`parsing`, `ollama_classification`, `file_operations`, `utils`, `logging`).

### 2. CLI and UI Implementation

- [x] Implement the command-line interface (CLI) with all options.
- [x] Implement the Streamlit web application (UI).
- [x] Implement "dry-run" mode and user confirmation.
- [x] Implement progress bars and real-time logging in the UI.

### 3. Advanced Parsing & Classification

- [x] **Knowledge-Based Classification**:
  - [x] Create `knowledge_base_module.py` to handle `debitors.yaml`.
- [x] **Advanced Parsing with Pandoc**:
  - [x] Refactor `parsing_module.py` to use a hierarchical approach with Pandoc as a fallback.
  - [x] Added parsers for `.html`, `.rtf`, `.eml`.
- [x] **EXIF-Based Photo Organization**:
  - [x] Enhance image parser to extract all relevant EXIF data.
  - [x] Create `geocoding_module.py` to handle reverse geocoding.
  - [x] Update file operations to create date/location-based folders for photos.
- [x] **Custom Rules**:
  - [x] Implement a rules engine for pre-classification based on filename or path.
- [x] **Language-Based Organization**:
  - [x] Integrate a language detection library (`langdetect`).
  - [x] Update file operations to create language-based subfolders.
- [x] **Archive Support**:
  - [x] Add support for parsing archive contents (`.zip`, etc.).
- [x] **AI-Powered Renaming (Initial)**:
  - [x] Enhance Ollama prompts to extract issuer, date, and a short title.

### 4. Advanced Features

- [x] **History and Undo**:
  - [x] Create `history_module.py` to log all file operations.
  - [x] Implement an `undo` command.
- [x] **Vision Model Integration**:
  - [x] Integrate `ollama/llava` for advanced image classification.
- [x] **Background Watching**:
  - [x] Implement a background process to watch a folder for new files.

### 5. Testing and Configuration

- [x] Write comprehensive unit and integration tests for all completed features.
- [x] Add configuration for generic text file extensions.
- [x] Add configuration to enable/disable vision model usage.
