# Installation

ClassifAI runs on Python 3.10+ and needs a handful of system tools plus a
local Ollama instance.

## 1. System dependencies

### macOS (Homebrew)

```bash
brew install pandoc tesseract libmagic exiftool
brew install tesseract-lang poppler   # optional: fra/deu OCR, pdftotext
```

### Ubuntu / Debian

```bash
sudo apt-get install pandoc tesseract-ocr libmagic1 exiftool
sudo apt-get install tesseract-ocr-fra tesseract-ocr-deu poppler-utils   # optional
```

### Windows

- [Pandoc](https://pandoc.org/installing.html)
- [Tesseract](https://github.com/UB-Mannheim/tesseract/wiki)
- [libmagic](https://github.com/nscaife/file-windows)
- [ExifTool](https://exiftool.org/)

`libmagic` and `exiftool` are **recommended but optional** — ClassifAI
degrades gracefully when they're absent (MIME detection falls back to
extension-based guessing; rich metadata is skipped).

- **OCR languages:** OCR uses `fra+eng+deu`, restricted to the Tesseract
  language packs actually installed. Without the French/German packs,
  French/German scans are read with the English model only.
- **`pdftotext`** (Poppler) is an optional second attempt at a PDF's text
  layer, between PyMuPDF and OCR. It is skipped with a warning when
  missing.
- **Pandoc** is needed for `.odt`, `.epub`, `.pptx`, `.rst`, `.tex`,
  `.org` and similar formats (see
  [Configuration → Supported file types](configuration.md#supported-file-types)).

## 2. Python + project

Clone and install with [`uv`](https://docs.astral.sh/uv/):

```bash
git clone https://github.com/fjacquet/classifai.git
cd classifai
uv sync --all-extras --all-groups   # or: make install
```

For development (tests, linters, docs):

```bash
uv pip install -e ".[dev]"   # or: make dev
```

## 3. Ollama + a model

Install Ollama from [ollama.ai](https://ollama.ai), then pull a model:

```bash
ollama pull gemma:2b      # text model (default when OLLAMA_MODEL_NAME is unset)
ollama pull llava         # vision model (optional, used with --use-vision)
```

Smaller models work on CPU-only laptops; larger models benefit from a GPU
but are not required.

## 4. Configure environment

Copy `.env.example` to `.env` and adjust (every variable is optional; the
values below are the built-in defaults):

```dotenv
OLLAMA_MODEL_NAME=gemma:2b
OLLAMA_VISION_MODEL_NAME=llava
OLLAMA_API_URL=http://localhost:11434
```

These values are also used as defaults by the CLI and the Web UI. The
text model and URL can be overridden per run (`--ollama-model`,
`--ollama-url`, or the Web UI sidebar).

## 5. Verify the install

```bash
uv run classifai --help
uv run classifai run --source-dir ~/Documents/some-folder --mode dry-run
```

Point `--source-dir` at any folder of your documents — `dry-run` only
prints the planned layout, nothing is moved.

Run ClassifAI from the repository root: configuration is read from the
`config/` directory relative to the current working directory.

If both commands produce output without stack traces, you're ready to
continue to the [Quickstart](quickstart.md).

## Troubleshooting install

See [Troubleshooting](troubleshooting.md) for common install issues
(Tesseract not on PATH, Ollama unreachable, libmagic errors on macOS, etc.).
