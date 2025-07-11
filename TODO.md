# ClassifAI - TODO

This document tracks the remaining tasks and the history of completed work for the ClassifAI project.

---

## Remaining Tasks

### 1. Finalizing AI and Rule-Based Logic

- [x] **AI-Powered Sector Classification**:
  - [x] Add a new function `get_sector_with_ai` to `ollama_classification_module.py`.
  - [x] Update `core_logic.py` to call this function as a fallback when the issuer is not in the knowledge base.
- [x] **Rule for `.ppk` Files**:
  - [x] Add a rule to `config/rules.yaml` to classify `.ppk` files as "Clés et Certificats".

### 2. Fonctionnalités Futures

- [ ] **Support Audio/Vidéo**:
  - [ ] Ré-intégrer la transcription audio/vidéo avec des imports conditionnels (tâche différée).

---

## Completed Tasks

### 1. Finalizing Implementation and Documentation

- [x] **Refine File Naming**:
  - [x] Improve the AI prompt in `ollama_classification_module.py` to enforce the `YYYY-MM-DD_Titre_Court_Document.ext` format.
  - [x] Add a fallback mechanism in `core_logic.py` to handle cases where the AI-generated filename is invalid.
- [x] **Consolidate Documentation**:
  - [x] Merge `ADDENDUM.md`, `SPECIFICATIONS.md`, and `SPECIFICATION_REVISED.md` into a single, authoritative `ARCHITECTURE.md`.
  - [x] Delete the old specification documents.
- [x] **Code Cleanup**:
  - [x] Remove the duplicate `classifai_app.py` from the project root.

### 2. Environment & Core Setup

- [x] Install Ollama and pull a base model.
- [x] Initialize project structure (source, tests, docs).
- [x] Set up `uv` for dependency management.
- [x] Configure `pytest`, `pytest-mock`, `faker`, and `coverage.py`.
- [x] Configure `ruff` for linting and formatting.
- [x] Configure `yamlfix` for YAML files.
- [x] Create `.env.example` and add `.env` to `.gitignore`.
- [x] Implement core logic modules (`parsing`, `ollama_classification`, `file_operations`, `utils`, `logging`).

### 3. CLI and UI Implementation

- [x] Implement the command-line interface (CLI) with all options.
- [x] Implement the Streamlit web application (UI).
- [x] Implement "dry-run" mode and user confirmation.
- [x] Implement progress bars and real-time logging in the UI.

### 4. Advanced Parsing & Classification

- [x] **Structured Renaming & Organization**:
  - [x] Implement the full folder structure: `Langue/Secteur/Émetteur/Catégorie/`.
  - [x] Ensure the filename format `Date_Titre_Court_Document.ext` is correctly applied.
- [x] **Knowledge-Based Classification**:
  - [x] Create `knowledge_base_module.py` to handle `debitors.yaml`.
- [x] **Advanced Parsing with Pandoc**:
  - [x] Refactor `parsing_module.py` to use a hierarchical approach with Pandoc as a fallback.
  - [x] Added parsers for `.html`, `.rtf`, `.eml`, and `.msg`.
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

### 5. Advanced Features

- [x] **History and Undo**:
  - [x] Create `history_module.py` to log all file operations.
  - [x] Implement an `undo` command.
- [x] **Vision Model Integration**:
  - [x] Integrate `ollama/llava` for advanced image classification.
- [x] **Background Watching**:
  - [x] Implement a background process to watch a folder for new files.

### 6. Testing and Configuration

- [x] Write comprehensive unit and integration tests for all completed features.
- [x] Add configuration for generic text file extensions.
- [x] Add configuration to enable/disable vision model usage.
- [x] Add `categories.yaml` for dynamic category management.
