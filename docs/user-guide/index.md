# User Guide

Welcome. This guide walks you through running ClassifAI on your own files —
from first install to daily workflows and the occasional troubleshooting
session.

## Contents

1. [Installation](installation.md) — system dependencies, Python setup,
   Ollama.
2. [Quickstart](quickstart.md) — organize your first folder in 5 minutes.
3. [CLI reference](cli.md) — all commands and options.
4. [Web UI](web-ui.md) — using the Streamlit interface.
5. [Configuration](configuration.md) — categories, sectors, rules, aliases,
   env vars.
6. [Troubleshooting](troubleshooting.md) — common issues and fixes.

## Which interface should I use?

| If you…                                       | Use           |
| --------------------------------------------- | ------------- |
| Want to script a one-shot run or cron it      | [CLI](cli.md) |
| Want to preview + confirm visually            | [Web UI](web-ui.md) |
| Want a folder to be watched continuously      | `classifai watch` (see [CLI](cli.md#watch)) |
| Want to integrate with another program        | FastAPI (see the code in `src/classifai/app/`) |

All four share the same core logic and configuration; switching between
them doesn't change classification behavior.

## What ClassifAI does, in one sentence

ClassifAI reads each file in a source directory, extracts metadata and
text, decides a `Language / Sector / Issuer / Category / Date_Title.ext`
placement via a hybrid of YAML rules and a local LLM (Ollama), and —
depending on mode — previews, moves, or copies the files into that
hierarchy.

For the formal requirements, see the [PRD](../PRD.md). For the reasoning
behind architecture choices, see the [ADRs](../adr/).
