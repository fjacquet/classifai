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
| `--ollama-model`      | `-ai` | `OLLAMA_MODEL_NAME` (`gemma4:e4b`) | Text LLM model name                      |
| `--ollama-url`        | `-url`| `OLLAMA_API_URL`            | Ollama API URL                                |
| `--rename-files`      | `-r`  | `False`                     | Rename to `YYYY-MM-DD_Short_Title.ext`        |
| `--use-vision`        | `-uv` | `use_vision_model` in `settings.yaml` (`False`) | Use `OLLAMA_VISION_MODEL_NAME` for images |
| `--language-subfolders` | `-ls`| `False`                    | Use the detected language (`en/`, `fr/`, …) as top-level folder; otherwise `fr/` |
| `--recursive`         | `-R`  | `False`                     | Scan subdirectories                           |
| `--verbose`           | `-v`  | `False`                     | DEBUG logging                                 |
| `--quiet-llm`         | `-ql` | `False`                     | Suppress DEBUG logs from the LLM module       |
| `--log-file`          |       | `logs/main.log`             | Log file path                                 |

Before scanning, `run` (and `watch`, before it starts watching) validates `config/rules.yaml`: a rule whose
category is not in `categories.yaml`, or a condition with an unknown
`type` / `match`, stops the run with an error listing the offending rules
(exit code 1). See [Configuration → rules](configuration.md#configrulesyaml).

### What gets scanned

- Only files whose extension is supported (see
  [Configuration → Supported file types](configuration.md#supported-file-types)).
  Hidden files (`.name`) and Office lock files (`~$name`) are skipped.
- With `--recursive`, a destination folder nested inside the source is
  skipped, so already-filed documents are not re-classified.
- `.zip` archives are rejected with an error: decompress them first.

### Moving and copying

- If a file with **identical content** (SHA-256) already sits at the
  destination path, the file is skipped and the source is left in place.
- If a *different* file already has that name, the new one gets
  `" (1)"`, `" (2)"`, … appended to its name.
- Every move/copy is recorded in `logs/history.json` for [`undo`](#undo).

### Renaming

With `--rename-files`, files are named `YYYY-MM-DD_Short_Title.ext`:

- the date is the first valid one among the model's document date and
  the file's metadata creation date / EXIF date;
- the title is the model's short title;
- `_UNKNOWN_` documents get `_suggested-<Category>` appended (a new
  category suggested by the model);
- if none of these is available, the original name is kept.

Files matched by a rule are never renamed.

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
uv run classifai watch --source-dir <path> --destination-dir <path> [options]
```

Runs until interrupted (Ctrl-C). Useful for scanner / download inboxes.

### Options

| Option                  | Short  | Default                          | Purpose                                  |
| ----------------------- | ------ | -------------------------------- | ---------------------------------------- |
| `--source-dir`          | `-s`   | **required**                     | Folder to watch                          |
| `--destination-dir`     | `-d`   | **required**                     | Output folder                            |
| `--mode`                | `-m`   | `move`                           | `move` / `copy` (no confirmation prompt) |
| `--ollama-model`        | `-ai`  | `OLLAMA_MODEL_NAME` (`gemma4:e4b`) | Text LLM model name                      |
| `--ollama-url`          | `-url` | `OLLAMA_API_URL`                 | Ollama API URL                           |
| `--rename-files`        | `-r`   | `False`                          | Rename to `YYYY-MM-DD_Short_Title.ext`   |
| `--use-vision`          | `-uv`  | `use_vision_model` (`False`)     | Use the vision model for images          |
| `--language-subfolders` | `-ls`  | `False`                          | Detected language as top-level folder    |

### Behaviour

- The watch is always **recursive** (new files in subfolders are picked
  up too).
- A file is processed once its size has stopped changing, so half-written
  scans and downloads are not classified early. Files that keep changing
  for 5 minutes, or vanish, are skipped.
- Renames are handled: a browser that downloads to a temporary name and
  then renames the file is caught on the final name.
- Ignored: hidden files, Office lock files (`~$…`), temporary files
  (`.part`, `.crdownload`, `.tmp`, `.download`, `.partial`), unsupported
  extensions, and files inside the destination when it is nested in the
  watched folder.
- Classification runs on a worker thread, one file at a time; a failing
  file is logged and the watcher keeps going.

Makefile shortcut:

```bash
make watch SRC=~/Inbox DEST=~/Sorted
```

`SRC` and `DEST` are both required.

---

## `undo`

Reverse the most recent move/copy.

```bash
uv run classifai undo
```

- For `move`: the file is moved back to its original path.
- For `copy`: the copied file is deleted.
- Asks for confirmation, then removes the entry from `logs/history.json`.
  Running `undo` again reverses the operation before that one.

---

## `kb-list-unknown`

List issuers that the LLM discovered but that aren't yet in
`config/sector_issuer_mapping.yaml`, with how often each was seen and
when it was last seen (columns: Issuer, Count, Last Seen).

```bash
uv run classifai kb-list-unknown [--file/-f config/unknown_issuers.yaml]
```

Without `--file`, reads `unknown_issuers.yaml` in the config directory
(`config/`).

Review these periodically and promote valid ones into the mapping file.
See [Configuration → Issuer aliases](configuration.md#issuer-aliases-and-unknown-issuers).

---

## Exit codes & errors

- `0` — success.
- Non-zero — an error was raised (e.g. `1` when `rules.yaml` fails
  validation). See `logs/main.log` for detail.
- Classification failures on individual files don't abort the run; they
  are logged and the file is skipped.

## Makefile shortcuts

| Command            | Does                                         |
| ------------------ | -------------------------------------------- |
| `make run`         | `classifai --help`                           |
| `make web`         | launch Streamlit UI                          |
| `make watch SRC=.. DEST=..` | start watcher                       |
| `make ci`          | lint + tests + build                         |
| `make format`      | ruff format                                  |
| `make dev`         | install dev dependencies                     |

See `make help` for the full list.
