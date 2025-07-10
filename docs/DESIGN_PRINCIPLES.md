## Design Principles and Decisions - ClassifAI

This document records the key design principles, architectural decisions, and development conventions adopted throughout the ClassifAI project. It serves as a guide for all contributors, ensuring consistency, quality, and maintainability.

-----

### 1\. Core Philosophy

Our development philosophy for ClassifAI is rooted in several established principles:

* **Modularity and Reusability**: We organize code into distinct, self-contained **modules** (`parsing`, `ollama_classification`, `file_operations`, `logging`, `history`, `config`, `utils`). Each module has clear, single responsibilities, minimizing coupling between them. This approach naturally adheres to the **DRY (Don't Repeat Yourself)** principle by promoting shared, reusable components, and the **KISS (Keep It Simple, Stupid)** principle by breaking down complexity into manageable units.
* **Configuration Management**: We prioritize security and flexibility.
  * **Sensitive information** and environment-specific settings (like Ollama API URLs, default model names, or any future API keys) are managed exclusively via **`.env` files**. These files are loaded at application startup using `python-dotenv` and are explicitly excluded from version control (`.gitignore`).
  * **Non-sensitive, default configurations** (e.g., predefined classification categories, logging levels, specific parsing options) are stored in a structured **YAML file** (e.g., `config/settings.yaml`).
* **Test-Driven Mindset (TDD)**: We adopt a **Test-Driven Development** approach. All new features and bug fixes must be accompanied by comprehensive tests written *before* the implementation. This ensures code correctness, provides clear specifications, and facilitates refactoring. We commit to achieving a **high code coverage** (aiming for \>80%) as measured by `coverage.py`.
* **User-Centric Design**: While leveraging advanced AI, the end-user experience remains paramount. Both the CLI and Streamlit interfaces should be intuitive, provide clear feedback (including "dry run" previews), and offer validation steps to prevent unintended actions.

-----

### 2\. Key Technology and Library Choices

We've selected modern, robust, and performant Python libraries for ClassifAI:

* **Logging**: We use **`loguru`** for all application logging. It provides a simple, powerful, and feature-rich interface for logging, including built-in support for file rotation, colorized console output, and easy configuration. This significantly simplifies error tracking and operational monitoring.
* **CLI Framework**: We use **`typer`** to build our command-line interface. Built on top of Click, its modern, annotation-based syntax makes it exceptionally easy to create clean, user-friendly, and robust CLIs with automatic help generation and validation.
* **Web UI Framework**: **`streamlit`** is our choice for the graphical web interface. It allows for rapid development of interactive data applications directly in Python, making it ideal for visualizing the classification process and enabling user interaction without complex front-end development.
* **Dependency Management**: Project dependencies are managed with **`uv`**. Its unparalleled speed and reliability ensure consistent and efficient installation, resolution, and management of Python packages across all development and deployment environments.
* **LLM Integration**: We leverage **`litellm`** as a universal interface for interacting with various Large Language Models. For ClassifAI, this specifically allows seamless communication with **Ollama**'s local LLM servers. This choice provides flexibility to switch between different Ollama models (e.g., `llama3`, `mistral`, `llava`) and potentially other LLM providers in the future.
* **Parsing Libraries**: A set of specialized libraries will handle content extraction from diverse document formats:
  * **`PyMuPDF`** (Fitz): For robust and fast PDF text and image extraction.
  * **`python-docx`**: For reading `.docx` (Microsoft Word) files.
  * **`openpyxl`**: For reading `.xlsx` (Microsoft Excel) files.
  * **`python-pptx`**: For reading `.pptx` (Microsoft PowerPoint) files.
  * **`Pillow`**: For general image processing.
  * **`pytesseract`**: For Optical Character Recognition (OCR) on images, acting as a Python wrapper for the Tesseract OCR engine.
  * **`textract`**: A convenient wrapper for various document types, potentially simplifying initial parsing attempts before resorting to format-specific libraries.
  * **`pydub`** and **`moviepy`**: For handling audio and video files, including extracting audio tracks for transcription.
  * **`SpeechRecognition`**: For converting speech to text, interfacing with various transcription services (including local ones like OpenAI's Whisper if integrated).

-----

### 3\. Testing and Quality Assurance Conventions

A rigorous approach to testing and code quality is paramount for ClassifAI's reliability:

* **Testing Framework**: **`pytest`** is our primary testing framework. All tests will be written as `pytest` functions or methods.
* **Test Fixtures**: For setting up and tearing down test resources (like temporary files, directories, or mocked environments), we use a combination of `pytest` fixtures for common setups and **`contextlib`** managers (`@contextlib.contextmanager`) for more specific, self-contained resource management. This provides clarity and ensures proper cleanup.
* **Mocking and Fakes**:
  * **`pytest-mock`**: We use this plugin to easily mock external services and complex dependencies (e.g., `litellm` calls to Ollama, file system operations) during unit tests, ensuring tests are fast, isolated, and deterministic.
  * **`faker`**: For generating realistic yet synthetic data (e.g., fake file names, content, user details) to populate test scenarios, especially for parsing and classification modules.
* **Code Coverage**: We use **`pytest-cov`** (a `pytest` plugin for `coverage.py`) to measure test coverage. A minimum target coverage of **\>80%** will be enforced for core logic.
* **Static Code Analysis and Formatting**:
  * **`ruff`**: This ultra-fast linter and formatter will be used for enforcing coding style (PEP 8 compliance) and identifying potential issues early.
  * **`yamlfix`**: Ensures all YAML configuration files (e.g., `config/settings.yaml`) adhere to a consistent formatting standard.

### 4\. Code Quality and Formatting Workflow

To maintain a consistent and high-quality codebase, the following commands **must be run before committing changes**:

1. **Run Tests with Coverage**: Ensure all tests pass and check code coverage.

    ```bash
    uv run pytest --cov=classifai --cov-report=term-missing --no-cov-on-fail
    ```

2. **Fix Linting Errors and Format Code**: Automatically fix common linting issues and format all Python code.

    ```bash
    uv ruff check . --fix
    uv ruff format .
    ```

3. **Format YAML**: Format all YAML configuration files.

    ```bash
    uv run yamlfix .
    ```

    *Note: These commands can be integrated into pre-commit hooks for automated execution.*

-----

### 5\. Environment Integrity

* **The `.venv` directory is sacred.** Under no circumstances should the contents of the virtual environment (`.venv/`) be modified manually. It contains third-party packages managed by `uv` and is not part of our application's source code. All issues related to dependencies must be resolved by correcting our own application code or by managing dependencies properly through `uv` commands (e.g., `uv pip install`, `uv pip uninstall`, `uv pip sync`).
* **Operating System Compatibility**: ClassifAI is designed to function primarily on **macOS**. While cross-platform compatibility will be considered in design, macOS is the primary target for initial development and testing. Dependencies on system-level tools (like Tesseract, FFmpeg, Poppler utilities) must be clearly documented for macOS users.
