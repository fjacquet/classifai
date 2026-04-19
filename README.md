# ClassifAI

Automatically organize files using a hybrid of YAML rules and a local LLM
via [Ollama](https://ollama.ai). Privacy-first, offline-capable,
extensible by editing YAML.

[![CI](https://github.com/fjacquet/classifai/actions/workflows/ci.yml/badge.svg)](https://github.com/fjacquet/classifai/actions/workflows/ci.yml)
[![codecov](https://codecov.io/gh/fjacquet/classifai/graph/badge.svg?token=TS8PKVYX1V)](https://codecov.io/gh/fjacquet/classifai)
[![Python](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![uv](https://img.shields.io/badge/packaged%20with-uv-blueviolet)](https://github.com/astral-sh/uv)
[![pre-commit](https://img.shields.io/badge/pre--commit-enabled-brightgreen)](https://pre-commit.com/)

---

## What it does

ClassifAI reads a folder of mixed files (PDFs, Office docs, images,
emails, …), extracts text and metadata, and organizes them into a
predictable hierarchy:

```
Language/Sector/Issuer/Category/Date_Title.ext
```

The classification pipeline runs fast YAML rules first, falls back to a
knowledge-base lookup, and only invokes the LLM for the unknown tail.
No document content leaves your machine.

## Documentation

| Doc | For |
| --- | --- |
| 📖 **[User Guide](docs/user-guide/index.md)** | Install, quickstart, CLI, Web UI, configuration, troubleshooting |
| 📋 **[Product Requirements (PRD)](docs/PRD.md)** | What ClassifAI does and why |
| 🏛️ **[Architecture Decisions (ADRs)](docs/adr/README.md)** | The significant technical choices, with rationale |
| 🗂️ **[Document Types](docs/DOCUMENTS_TYPES.md)** | Categories of files ClassifAI handles |
| 📝 **[Changelog](CHANGELOG.md)** | What's changed release-to-release |
| 🤖 **[CLAUDE.md](CLAUDE.md)** | Conventions for AI-assisted contributions |

## Quick install

```bash
# System deps (macOS)
brew install pandoc tesseract libmagic exiftool

# Python project
git clone https://github.com/fjacquet/classifai.git
cd classifai
uv pip install -e .

# Local LLM
ollama pull gemma3n
```

Full instructions: [User Guide → Installation](docs/user-guide/installation.md).

## Quick run

```bash
# Preview first — nothing moves
uv run classifai run --source-dir ~/Downloads/Inbox --mode dry-run

# Then move
uv run classifai run -s ~/Downloads/Inbox -d ~/Sorted -m move

# Or use the Web UI
make web
```

Full workflow: [User Guide → Quickstart](docs/user-guide/quickstart.md).

## Design highlights

- **Hybrid classification** — rules + knowledge base + LLM, in that
  order. The LLM is the fallback, not the default.
  ([ADR-0002](docs/adr/0002-hybrid-rule-plus-llm-classification.md))
- **Privacy by default** — Ollama runs locally; document content never
  leaves the machine. ([ADR-0003](docs/adr/0003-ollama-as-llm-runtime.md))
- **Multiple entry points** — CLI, Streamlit UI, FastAPI, file watcher.
  Shared core, aligned defaults.
  ([ADR-0005](docs/adr/0005-three-entry-points-cli-web-api.md))
- **YAML-editable taxonomy** — categories, sectors, issuers, aliases,
  rules. No rebuilds to change organization.
  ([ADR-0006](docs/adr/0006-yaml-driven-configuration.md))

## Contributing

Read [`CLAUDE.md`](CLAUDE.md) before you start. Run `make check` before
you commit. **Never disable a quality gate** (mypy, ruff, pre-commit,
tests) to unblock a merge — fix the underlying issue.

## License

[MIT](LICENSE)
