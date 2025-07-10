# ClassifAI

ClassifAI is a tool to automatically organize files in a directory using local AI models with Ollama.

## Installation

1. **Clone the repository:**

    ```bash
    git clone https://github.com/your-username/classifai.git
    cd classifai
    ```

2. **Install dependencies:**

    ```bash
    uv pip install -e .
    ```

3. **Install Ollama:**
    Follow the instructions on the [Ollama website](https://ollama.ai/) to install and run Ollama on your system.

4. **Pull the required models:**
    ClassifAI uses two types of models: a **completion model** for detailed analysis and an **embedding model** for fast similarity searches.

    * **Completion Model (for `-cm completion` mode):**

        ```bash
        ollama pull gemma3n
        ```

    * **Embedding Model (for `-cm embedding` mode):**

        ```bash
        ollama pull mxbai-embed-large
        ```

## Usage

### Command-Line Interface (CLI)

To run the CLI, use the `uv run main.py` command with your desired options.

**Example (using fast embedding mode):**

```bash
uv run main.py --source-dir /path/to/your/files --classification-mode embedding
```

**Example (using detailed completion mode):**

```bash
uv run main.py --source-dir /path/to/your/files --classification-mode completion
```

### Web Interface (Streamlit)

To launch the web interface, run:

```bash
streamlit run src/classifai/classifai_app.py
```

The web UI allows you to configure all options graphically.
