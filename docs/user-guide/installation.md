# Installation

ClassifAI runs on Python 3.10+ and needs a handful of system tools plus a
local Ollama instance.

## 1. System dependencies

### macOS (Homebrew)

```bash
brew install pandoc tesseract libmagic exiftool
```

### Ubuntu / Debian

```bash
sudo apt-get install pandoc tesseract-ocr libmagic1 exiftool
```

### Windows

- [Pandoc](https://pandoc.org/installing.html)
- [Tesseract](https://github.com/UB-Mannheim/tesseract/wiki)
- [libmagic](https://github.com/nscaife/file-windows)
- [ExifTool](https://exiftool.org/)

`libmagic` and `exiftool` are **recommended but optional** — ClassifAI
degrades gracefully when they're absent (MIME detection falls back to
extension-based guessing; rich metadata is skipped).

## 2. Python + project

Clone and install with [`uv`](https://docs.astral.sh/uv/):

```bash
git clone https://github.com/fjacquet/classifai.git
cd classifai
uv pip install -e .          # or: make install
```

For development (tests, linters, docs):

```bash
uv pip install -e ".[dev]"   # or: make dev
```

## 3. Ollama + a model

Install Ollama from [ollama.ai](https://ollama.ai), then pull a model:

```bash
ollama pull gemma3n       # text model (default)
ollama pull llava         # vision model (optional, for image OCR+understanding)
```

Smaller models work on CPU-only laptops; larger models benefit from a GPU
but are not required.

## 4. Configure environment

Copy `.env.example` to `.env` and adjust:

```dotenv
OLLAMA_MODEL_NAME=gemma3n
OLLAMA_VISION_MODEL_NAME=llava
OLLAMA_API_URL=http://localhost:11434
```

These values are also used as defaults by the CLI and the Web UI.

## 5. Verify the install

```bash
uv run classifai --help
uv run classifai run --source-dir ./tests/fixtures --mode dry-run
```

If both commands produce output without stack traces, you're ready to
continue to the [Quickstart](quickstart.md).

## Troubleshooting install

See [Troubleshooting](troubleshooting.md) for common install issues
(Tesseract not on PATH, Ollama unreachable, libmagic errors on macOS, etc.).
