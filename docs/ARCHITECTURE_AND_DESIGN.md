# ClassifAI: Architecture and Design Principles (Harmonized)

**Date:** July 19, 2025
**Version:** 3.1
**Project:** ClassifAI
**Objective:** This document provides a comprehensive overview of ClassifAI's architecture, design principles, and implementation patterns, harmonized with current specifications.

---

## 1. System Architecture

ClassifAI adopts a modular, layered architecture based on functional programming principles to facilitate development, testing, and maintenance. The system is organized into distinct layers with clear responsibilities, separating pure logic from side effects.

### 1.1. Architecture Overview

```bash
+--------------------------+     +-------------------------+     +--------------------------+
| Interfaces               |     | Orchestration           |     |.   Pure Business Logic   |
| (app/cli.py, app/web.py) |---->| (core/workflow.py)      |---->| (core/classification.py. |
+--------------------------+     +-------------------------+     | core/types.py)           |
|                                                                +--------------------------+
|
v
+--------------------------+     +-------------------------+
| Infrastructure           |     | External Services       |
| (infrastructure/llm.py,  |<--->| (LLM APIs, Databases,   |
| file_system.py, etc.)    |     | File System I/O)        |
+--------------------------+     +-------------------------+
```

### 1.2. Key Components

1. **Interfaces Layer (`app/`)**:

   - **CLI Interface (`app/cli.py`)**: Command-line interface built with Typer or Argparse.
   - **Web Interface (`app/web_ui.py`)**: Streamlit-based web UI for interactive use.
   - **API (`app/api.py`)**: A RESTful API to allow for programmatic integration with other systems.

2. **Pure Core (`core/`)**:

   - **Workflow (`core/workflow.py`)**: Central orchestration of the classification pipeline, composing pure functions.
   - **Classification Logic (`core/classification.py`)**: Pure functions responsible for the business logic of classification.
   - **Data Types (`core/types.py`)**: Definition of all primary data structures, such as immutable dataclasses (`frozen=True`).

3. **Infrastructure Layer (`infrastructure/`)**:

   - **LLM Client (`infrastructure/llm.py`)**: Handles all communication with the Large Language Model.
   - **File System (`infrastructure/file_system.py`)**: Manages all file I/O operations (move, copy, delete, read, write) with robust, functional error handling.
   - **Parsing (`infrastructure/parsing.py`)**: Extracts text and metadata from various file formats.
   - **Configuration (`infrastructure/config.py`)**: Loads, validates, and provides access to application settings from `.env` and YAML files.

4. **Support Modules**:
   - **Knowledge Base (`infrastructure/knowledge_base.py`)**: Manages reference data like the `sector_issuer_mapping.yaml`.
   - **History (`infrastructure/history.py`)**: Tracks file operations for auditing and potential undo functionality.
   - **Logging**: Centralized logging configured with Loguru.

## 2. Functional Programming Approach

ClassifAI strictly adheres to functional programming principles to enhance code quality and testability.

### 2.1. Core Principles

- **Pure Functions**: Most functions, especially in the `core/` directory, must be pure.
- **Immutability**: Data structures defined in `core/types.py` are immutable (e.g., `@dataclass(frozen=True)`).
- **Function Composition**: Complex workflows are built by composing simpler functions.
- **Separation of Core Logic and Side Effects**: The `core/` directory contains pure business logic, while the `infrastructure/` directory manages all side effects (I/O, network calls, etc.).

### 2.2. Functional Containers (`returns` library)

ClassifAI uses the `returns` library for robust error and side-effect management.

1. **`Result[Success, Failure]`**: For all fallible operations, such as file I/O or API calls.
2. **`Maybe[Some, Nothing]`**: For optional values, such as looking up an item that may not exist.
3. **`@safe` Decorator**: To wrap functions with potential exceptions in a `Result` container.

## 3. Key Technology Choices

ClassifAI leverages modern, robust libraries for its implementation:

1. **Functional Programming**: `returns` library.
2. **Logging**: `loguru`.
3. **CLI Framework**: `typer`.
4. **Web UI**: `streamlit`.
5. **LLM Integration**: `litellm` for interfacing with Ollama.
6. **Parsing Libraries**: `PyMuPDF`, `python-docx`, `openpyxl`, `extract-msg`.
7. **Testing**: `pytest`, `pytest-mock`, `hypothesis`.
