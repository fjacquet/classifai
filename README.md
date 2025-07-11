# ClassifAI

ClassifAI is a tool to automatically organize files in a directory using a hybrid of rule-based logic and local AI models with Ollama.

## Features

* **Hybrid Classification**: Uses a user-defined knowledge base (`debitors.yaml`) for fast, rule-based classification, falling back to powerful Ollama language models for semantic analysis.
* **Multiple AI Modes**: Choose between a fast `embedding` mode for quick similarity searches or a `completion` mode for in-depth content analysis.
* **Robust Parsing**: Supports a wide range of file types, including PDFs, Office documents, images (with OCR), and generic text files, with a fallback to `pandoc` for maximum compatibility.
* **Web Interface**: An intuitive Streamlit UI for easy configuration, previewing, and execution.
* **Command-Line Interface**: A powerful CLI for scripting and advanced users.

## Installation

1. **Clone the repository:**

    ```bash
    git clone https://github.com/your-username/classifai.git
    cd classifai
    ```

2. **Install System Dependencies:**
    * **Pandoc:** For advanced document parsing.

        ```bash
        # On macOS with Homebrew
        brew install pandoc
        ```

    * **Tesseract:** For Optical Character Recognition (OCR) in images.

        ```bash
        # On macOS with Homebrew
        brew install tesseract
        ```

3. **Install Python dependencies:**

    ```bash
    uv pip install -e .
    ```

4. **Install Ollama & Models:**
    * Follow the instructions on the [Ollama website](https://ollama.ai/) to install and run Ollama.
    * Pull the required models:

        ```bash
        # For completion mode
        ollama pull gemma3n
        # For embedding mode
        ollama pull mxbai-embed-large
        ```

## Usage

### Web Interface (Recommended)

Launch the Streamlit application for a user-friendly experience:

```bash
streamlit run src/classifai/classifai_app.py
```

### Command-Line Interface (CLI)

**Example (using fast embedding mode):**

```bash
uv run main.py --source-dir /path/to/your/files --classification-mode embedding
```

**Example (using detailed completion mode):**

```bash
uv run main.py --source-dir /path/to/your/files --classification-mode completion
```
