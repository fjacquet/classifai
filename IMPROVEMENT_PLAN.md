# ClassifAI Improvement Plan

Open items only. The critical, high- and most medium-priority items of the
original plan (missing `AppConfig` fields, category config mismatch,
deprecated `KnowledgeBase` class, context managers, subprocess timeouts,
thread-safe localization, retries with backoff, single-pass scanning,
filename sanitization, context-update pattern, duplicate CLI/pipeline
implementations, geocoding tests) are done and have been removed.

## Security

- `infrastructure/parsing.py`: resolve `pandoc` / `pdftotext` with
  `shutil.which()` before running them.
- File operations: guard against symlink tricks and over-long paths when
  moving/copying.

## Testing

- Edge cases: very long filenames (>255 chars), Unicode/emoji in filenames,
  files without extensions, empty files.

## Code quality

- Type hints for the `parsing_handler` decorator (`infrastructure/parsing.py`).
- One docstring style (Google) across modules — `entrypoint_utils.py` still
  uses NumPy style.

## Configuration

- Validate the YAML files against a schema (e.g. Pydantic) at startup, beyond
  the current rule checks in `validation.py`.
- Make hard-coded values configurable in `config/settings.yaml`: LLM
  `MAX_RETRIES` / `TIMEOUT` (`infrastructure/llm.py`) and the default `fr`
  language folder (`core/logic.py`).
