# Troubleshooting

## Ollama

### `Connection refused` / `Failed to establish a new connection`

Ollama isn't running, or `OLLAMA_API_URL` points somewhere else.

```bash
ollama serve                          # make sure the daemon is up
curl http://localhost:11434/api/tags  # should return JSON
```

If you set a custom URL in `.env`, verify it matches where Ollama is
actually listening.

### `model "gemma3n" not found`

You haven't pulled the model:

```bash
ollama pull gemma3n
```

Or switch model for a run:

```bash
uv run classifai run -s ~/Inbox -ai llama3:8b
```

### Slow runs / LLM timeouts

ClassifAI wraps LLM calls in `tenacity` with exponential backoff, so
transient failures retry automatically. If every call is slow:

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
contrast, rotated text, handwriting). The pipeline keeps going — the
file is classified from metadata alone.

Known limitation: **scanned PDFs don't trigger OCR.** ClassifAI uses
PyMuPDF's text layer; if the PDF has no text layer, extraction returns
empty. See the PRD "Open questions" section.

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

ExifTool is optional. Without it, the pipeline uses PyMuPDF's built-in
metadata for PDFs and Pillow's EXIF for images — usually enough. Install
it for better results on quirky formats:

```bash
brew install exiftool       # macOS
sudo apt-get install exiftool  # Debian/Ubuntu
```

## Classification quality

### Wrong sector / issuer for a known entity

The entity isn't in `sector_issuer_mapping.yaml`, or the alias hasn't
been registered. Add it:

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
   filename, MIME, metadata field).

### `_UNKNOWN_` folders proliferating

The LLM couldn't confidently pick. Contents have a suggested category
appended to the filename. Review them, then either:

- Add the suggested category to `categories.yaml`, or
- Fold the document into an existing category manually.

## File operations

### "File operation cancelled"

You answered `n` to the confirmation prompt. No files were moved.
Re-run and confirm.

### `FileExistsError` or name clash

The pipeline resolves name conflicts by appending `" (1)"`, `" (2)"`,
etc. If you see this error raw, please report it — it shouldn't escape.

### `undo` fails with "file not found"

The destination file was moved/renamed/deleted outside of ClassifAI
between the original operation and the `undo`. Accept the loss and
clear the entry from the history when prompted.

## Configuration validation

### `ConfigurationError: Category 'X' referenced in rules.yaml is not in categories.yaml`

Exactly what it says. Either:

- Add `X` to `config/categories.yaml`, or
- Remove the rule referencing `X` from `config/rules.yaml`.

Don't suppress the check — drift is the bug it's designed to catch.

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
