# Troubleshooting

## Ollama

### `Request to Ollama failed: …` (connection refused)

Ollama isn't running, or `OLLAMA_API_URL` (or `--ollama-url`) points
somewhere else.

```bash
ollama serve                          # make sure the daemon is up
curl http://localhost:11434/api/tags  # should return JSON
```

If you set a custom URL in `.env`, verify it matches where Ollama is
actually listening.

### `Ollama API error: 404` (model not found)

You haven't pulled the model (the default is `gemma:2b`, or whatever
`OLLAMA_MODEL_NAME` says):

```bash
ollama pull gemma:2b
```

Or switch model for a run:

```bash
uv run classifai run -s ~/Inbox -ai llama3:8b
```

### Slow runs / LLM timeouts

ClassifAI wraps LLM calls in `tenacity` with exponential backoff:
network errors and 5xx responses are retried (3 attempts), and each
request may take up to 120 s — the first call of a run can be slow while
Ollama loads the model, which then stays loaded for 10 minutes. If every
call is slow:

- Try a smaller model (`gemma:2b` on CPU, `llama3:8b` with modest GPU).
- Reduce batch size by running on smaller source folders.
- Check Ollama isn't swapped out / starved for RAM (activity monitor).

## Tesseract / OCR

### `Tesseract is not installed or not in your PATH`

```bash
# macOS
brew install tesseract

# Debian/Ubuntu
sudo apt-get install tesseract-ocr

# Verify
which tesseract
tesseract --version
```

On Windows, add the Tesseract install dir to `PATH`.

### OCR returns empty text

Expected for images with no text, or where Tesseract struggles (low
contrast, rotated text, handwriting). The pipeline keeps going, but with
no text the LLM is not called and the file goes to `_UNKNOWN_` (unless a
rule matched or `--use-vision` is on for images).

Scanned PDFs (no text layer, even via `pdftotext`) are OCRed — only the
first 3 pages, to bound the cost.

### Poor OCR on French or German documents

OCR uses `fra+eng+deu`, but only the language packs Tesseract has
installed. Check with `tesseract --list-langs` and install the missing
packs (`brew install tesseract-lang`, or
`sudo apt-get install tesseract-ocr-fra tesseract-ocr-deu`).

## libmagic / `python-magic`

### `failed to find libmagic`

On macOS after `brew install libmagic`, if you still see the error, tell
Python where to look:

```bash
export DYLD_LIBRARY_PATH="/opt/homebrew/lib:$DYLD_LIBRARY_PATH"
# Apple Silicon default; on Intel use /usr/local/lib
```

On Windows, download libmagic from
[nscaife/file-windows](https://github.com/nscaife/file-windows) and
place the DLLs on `PATH`.

ClassifAI degrades gracefully without libmagic — MIME detection falls
back to extension-based guessing. You'll just lose some accuracy on
files with the wrong extension.

## ExifTool

### Rich metadata absent

ExifTool is optional. Without it, only parser metadata is available:
Pillow's EXIF date/GPS for images and the headers of `.eml` / `.msg`
emails — PDF and Office author/title/creation date are not read, so
`metadata` rules and the LLM's metadata hints have less to work with.
Install it for better results:

```bash
brew install exiftool       # macOS
sudo apt-get install exiftool  # Debian/Ubuntu
```

## Classification quality

### Wrong sector / issuer for a known entity

The entity isn't in `sector_issuer_mapping.yaml`, or the extracted name
doesn't contain the mapped name as whole words and no alias is
registered. Check `classifai kb-list-unknown` for the exact extracted
name, then add it:

```yaml
Banque:
  - UBS          # canonical

aliases:
  "UBS AG": "UBS"
```

### Wrong category for many files

1. Check `config/categories.yaml` — is the right category even in the
   list?
2. Look at `logs/main.log` with `-v` — what did the LLM return?
3. If the LLM consistently picks a neighbor category, add a rule to
   `config/rules.yaml` that short-circuits on a reliable signal (path,
   filename, MIME type, metadata field).

### `_UNKNOWN_` folders proliferating

The LLM couldn't pick a category from the list, or no text could be
extracted (see [OCR returns empty text](#ocr-returns-empty-text)). With
`--rename-files`, a suggested category is appended to the filename
(`…_suggested-<Category>`). Review them, then either:

- Add the suggested category to `categories.yaml`, or
- Fold the document into an existing category manually.

## File operations

### "File operation cancelled"

You answered `n` to the confirmation prompt. No files were moved.
Re-run and confirm.

### `FileExistsError` or name clash

The pipeline resolves name conflicts by appending `" (1)"`, `" (2)"`,
etc. If you see this error raw, please report it — it shouldn't escape.

### A file was not moved and is still in the source folder

A file with identical content (SHA-256) already exists at the
destination path, so the transfer was skipped on purpose
(`Identical file already at …` in the log). Delete the source copy if
you don't need it.

### `undo` fails with "file not found"

The destination file was moved/renamed/deleted outside of ClassifAI
between the original operation and the `undo`. Accept the loss and
clear the entry from the history when prompted.

## Configuration validation

### `Found rules with invalid categories: - Rule 'N' uses invalid category: 'X'`

`classifai run` stops with this `ConfigurationError` (exit code 1).
Either:

- Add `X` to `config/categories.yaml`, or
- Fix or remove the rule referencing `X` in `config/rules.yaml`.

### `Found invalid rule conditions: - Rule 'N' uses unknown condition type: 'T'`

A condition `type` must be `filename`, `path`, `mime_type` or
`metadata`; a metadata `match` must be `exact`, `contains`,
`startswith`, `endswith` or `glob`. See
[Configuration → rules](configuration.md#configrulesyaml).

Don't suppress the checks — drift is the bug they're designed to catch.

## Pre-commit / CI

### `mypy` fails on a legacy file

Fix the types. `CLAUDE.md` has a hard rule: **never disable a quality
gate to unblock a commit.** If the fix is genuinely large, scope it
explicitly with the team before disabling.

### `ruff format --check` fails in CI

Run `make format` locally, commit, push.

## Still stuck?

1. Re-run with `--verbose` and check `logs/main.log` — stack traces are
   your friend.
2. Search issues: [github.com/fjacquet/classifai/issues](https://github.com/fjacquet/classifai/issues).
3. Open a new issue with the minimal reproducer and log excerpt.
