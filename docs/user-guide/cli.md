# CLI Reference

ClassifAI's CLI is built with [Typer](https://typer.tiangolo.com). Run
`uv run classifai --help` at any time for the authoritative list.

## Commands

| Command                     | Purpose                                    |
| --------------------------- | ------------------------------------------ |
| [`run`](#run)               | One-shot organize a directory              |
| [`watch`](#watch)           | Continuously organize new files in a dir   |
| [`undo`](#undo)             | Reverse the last move/copy operation      |
| [`kb-list-unknown`](#kb-list-unknown) | List unknown issuers captured during scans |

---

## `run`

Process a directory once.

```bash
uv run classifai run --source-dir <path> [options]
```

### Options

| Option                | Short | Default                     | Purpose                                       |
| --------------------- | ----- | --------------------------- | --------------------------------------------- |
| `--source-dir`        | `-s`  | **required**                | Folder to organize                            |
| `--destination-dir`   | `-d`  | same as source              | Output folder                                 |
| `--mode`              | `-m`  | `dry-run`                   | `dry-run` / `move` / `copy`                   |
| `--ollama-model`      | `-ai` | from env / config           | LLM model name (e.g. `gemma3n`)               |
| `--ollama-url`        | `-url`| from env / config           | Ollama API URL                                |
| `--rename-files`      | `-r`  | `False`                     | AI-powered filename rewriting                 |
| `--use-vision`        | `-uv` | from config                 | Use vision model for images                   |
| `--language-subfolders` | `-ls`| `False`                    | Create `en/`, `fr/` top-level subfolders      |
| `--recursive`         | `-R`  | `False`                     | Scan subdirectories                           |
| `--verbose`           | `-v`  | `False`                     | DEBUG logging                                 |
| `--quiet-llm`         | `-ql` | `False`                     | Suppress DEBUG logs from the LLM module       |
| `--log-file`          |       | `logs/main.log`             | Log file path                                 |

### Examples

Dry-run over a folder, recursively:

```bash
uv run classifai run -s ~/Inbox -R
```

Move to a different destination with verbose logs but hush the LLM chatter:

```bash
uv run classifai run -s ~/Inbox -d ~/Sorted -m move -v -ql
```

Use a specific model for this run:

```bash
uv run classifai run -s ~/Inbox -ai llama3:70b
```

---

## `watch`

Monitor a directory and organize new files as they arrive.

```bash
uv run classifai watch --source-dir <path> --destination-dir <path> [--mode move|copy]
```

Runs until interrupted. Useful for scanner / download inboxes. Accepts
the same tuning options as `run`.

Makefile shortcut:

```bash
make watch SRC=~/Inbox DEST=~/Sorted
```

---

## `undo`

Reverse the most recent move/copy.

```bash
uv run classifai undo
```

- For `move`: the file is moved back to its original path.
- For `copy`: the copied file is deleted.
- Only one step deep. Running `undo` twice does not undo the previous
  previous op.

---

## `kb-list-unknown`

List issuers that the LLM discovered but that aren't yet in
`config/sector_issuer_mapping.yaml`.

```bash
uv run classifai kb-list-unknown [--file config/unknown_issuers.yaml]
```

Review these periodically and promote valid ones into the mapping file.
See [Configuration → Issuer aliases](configuration.md#issuer-aliases-and-unknown-issuers).

---

## Exit codes & errors

- `0` — success.
- Non-zero — an error was raised. See `logs/main.log` for detail.
- Classification failures on individual files don't abort the run; they
  are logged and the file is skipped.

## Makefile shortcuts

| Command            | Does                                         |
| ------------------ | -------------------------------------------- |
| `make run`         | `classifai --help`                           |
| `make web`         | launch Streamlit UI                          |
| `make watch SRC=.. DEST=..` | start watcher                       |
| `make check`       | lint + tests                                 |
| `make format`      | ruff format                                  |
| `make dev`         | install dev dependencies                     |

See `make help` for the full list.
