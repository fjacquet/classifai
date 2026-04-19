# ClassifAI — Product Requirements Document

- **Version:** 1.0 (supersedes `FUNCTIONAL_SPECIFICATION.md`)
- **Date:** 2026-04-19
- **Owner:** Frederic Jacquet
- **Status:** Living document — update via PR

---

## 1. Problem

Everyday users accumulate hundreds of unsorted files in `Downloads/`,
email attachments, and scanner inboxes: invoices, bank statements, medical
bills, receipts, contracts, photos. Manual sorting is tedious, error-prone,
and never keeps up. Existing tools either require cloud upload (privacy
concern), are rigid rule-based (brittle), or are one-shot automations
without a taxonomy.

ClassifAI **organizes files into a predictable folder hierarchy by issuer,
sector, category, language, and date**, using a hybrid of fast rules and
local AI, without sending data to third parties.

## 2. Personas

| Persona                 | Needs                                                   | Primary interface |
| ----------------------- | ------------------------------------------------------- | ----------------- |
| **Power user**          | Script against a full archive, cron-driven workflows    | CLI               |
| **Non-technical user**  | Drop a folder, preview, confirm                         | Streamlit UI      |
| **Automation builder**  | Integrate with home-server / scanner / other programs   | FastAPI           |
| **Continuous inbox**    | Point at a folder and forget; process as files arrive   | Watcher daemon    |

## 3. Goals

1. **Correct classification** for the long tail of personal documents
   (banking, insurance, health, utilities, commerce).
2. **Privacy by default** — no document content leaves the machine.
3. **No cloud required** — works offline with a local model via Ollama.
4. **Reversible** — default mode is `dry-run`; `move` / `copy` require
   confirmation; an `undo` command exists.
5. **Extensible taxonomy** — categories, sectors, aliases, and rules are
   YAML-editable without a release.
6. **Multi-interface parity** — the same core logic drives CLI, Web UI,
   API, and watcher.

## 4. Non-goals

1. Cloud-hosted multi-tenant service.
2. Full-text search / vector retrieval over the corpus (removed;
   see CHANGELOG).
3. ZIP / archive extraction — expected to be done before ClassifAI runs
   (see "File Type Handling Constraints" below).
4. Audio / video transcription (deferred).
5. Editing document content — ClassifAI only sorts and renames.

## 5. Functional requirements

### 5.1 Output layout

Every organized file lands at:

```
<destination>/<Language>/<Sector>/<Issuer>/<Category>/<Date>_<Title>.<ext>
```

Example:

```
/Sorted/fr/Santé/M-Thérapies/Factures/2025-07-18_Consultation_orthopedie.pdf
/Sorted/en/Finance/UBS/Relevés/2025-01-15_Monthly_statement.pdf
```

- `Language` is ISO 639-1 (`fr`, `en`, …). Default `en` if undetectable.
- `Date` is ISO 8601 `YYYY-MM-DD`, extracted from content with metadata
  fallback.
- `Title` is produced by the LLM (concise, descriptive, filename-safe).
- Filename is sanitized via `utils.sanitize_filename`.

### 5.2 Classification pipeline

Implementation of [ADR-0002](adr/0002-hybrid-rule-plus-llm-classification.md).
Fixed priority:

1. **Early rules** match on filename / path / MIME.
2. **Full rules** match on metadata + MIME after parsing.
3. **Knowledge-base lookup** maps extracted issuer → sector
   (`config/sector_issuer_mapping.yaml`, with alias normalization).
4. **LLM enrichment** fills any unset fields (language, category, title,
   date, unknown issuer) via Ollama.
5. **Fuzzy correction** fixes LLM category typos (≥85% match) via
   `difflib.get_close_matches`.

### 5.3 Categories & sectors

- **Valid categories:** flat list in `config/categories.yaml`. LLM is
  constrained to this list.
- **Valid sectors:** flat list in `config/sectors.yaml`. KB-fallback LLM
  is constrained to this list.
- **`_UNKNOWN_` category:** when the LLM cannot confidently pick, the
  file goes to a `_UNKNOWN_` subfolder with a suggested category appended
  to the filename for human review:
  `…/_UNKNOWN_/2025-07-19_Titre_suggested-Ressources-Humaines.pdf`

### 5.4 Unknown issuer workflow

- New issuers discovered by the LLM are appended to
  `config/unknown_issuers.yaml` with a timestamp and an AI-suggested
  sector.
- CLI command `classifai kb-list-unknown` surfaces them for review.
- Admin moves reviewed issuers into `sector_issuer_mapping.yaml` (as
  canonical entries or aliases) — a manual promotion step by design.

### 5.5 File type support

| Category        | Extensions                                              | Parser      |
| --------------- | ------------------------------------------------------- | ----------- |
| Documents       | `.pdf .docx .doc .txt .rtf .odt`                        | Native      |
| Spreadsheets    | `.xlsx .xls .ods`                                       | Native      |
| Presentations   | `.pptx .ppt .odp`                                       | Pandoc      |
| Images (OCR)    | `.png .jpg .jpeg .tiff .bmp`                            | Tesseract   |
| Email           | `.msg .eml`                                             | Native      |
| Web             | `.html`                                                 | Native      |
| E-books         | `.epub`                                                 | Pandoc      |
| Technical docs  | `.md .rst .tex .org`                                    | Pandoc      |

### 5.6 Operation modes

- `dry-run` (default): preview the full plan; nothing is moved.
- `move`: relocate files; pre-confirm prompt in both CLI and UI.
- `copy`: duplicate files; original retained.
- **Undo**: `classifai undo` reverses the last operation using the
  `history.json` log.

### 5.7 Language / localization

- LLM prompts and expected responses are in **French** (internal
  simplification, not a user-facing setting).
- User-facing UI strings are resolved via
  `src/classifai/localization.py` (thread-safe via `contextvars`),
  currently FR and EN.

## 6. Non-functional requirements

1. **Privacy.** No document content is sent off-machine. Ollama default
   URL is `localhost:11434`. See [ADR-0003](adr/0003-ollama-as-llm-runtime.md).
2. **Robustness.**
   - Tenacity-based retry on LLM calls (exponential backoff).
   - Graceful degradation when `libmagic` or `exiftool` are absent.
   - Custom exception hierarchy (`exceptions.py`); no silent failures.
3. **Reversibility.** `dry-run` is default; `move`/`copy` confirm; undo
   exists.
4. **Testability.**
   - Pure functions in `core/`, side effects in `infrastructure/`.
   - Property-based tests via Hypothesis (`tests/property/`).
   - Coverage tracked via Codecov.
5. **Performance.** Early rules short-circuit the pipeline before any
   parsing; LLM calls are the slow path and only invoked when needed.
6. **Configurability.**
   - Model + URL via environment variables.
   - Taxonomy (categories / sectors / rules / aliases) via YAML.
   - Behaviour flags (recursive, rename, vision, language subfolders,
     verbosity) via CLI + UI with aligned defaults (`defaults.py`).

## 7. Architecture (summary)

See ADRs for full detail.

- **Entry points:** CLI (Typer), Streamlit, FastAPI, Watchdog daemon — all
  share the core pipeline. ([ADR-0005](adr/0005-three-entry-points-cli-web-api.md))
- **Core / infrastructure split:** pure business logic in `core/`; I/O in
  `infrastructure/`.
- **LLM runtime:** Ollama via `litellm`. ([ADR-0003](adr/0003-ollama-as-llm-runtime.md))
- **OCR engine:** Tesseract (Chandra OCR 2 evaluated and deferred —
  [ADR-0001](adr/0001-ocr-engine-stay-on-tesseract.md)).
- **Error handling:** native Python exceptions; no `returns` library.
  ([ADR-0004](adr/0004-remove-returns-library.md))
- **Configuration:** YAML + env vars, loaded once into frozen `AppConfig`.
  ([ADR-0006](adr/0006-yaml-driven-configuration.md))

## 8. Success metrics

- **Classification accuracy** on a held-out labelled set of the user's own
  documents: ≥90% correct `Sector/Issuer/Category` assignment.
- **Unknown-issuer reduction** over time as the KB grows: the fraction of
  runs hitting the LLM sector-fallback path should trend down.
- **No data egress** to non-configured endpoints — verified by network
  inspection (Ollama URL respected, no implicit cloud fallbacks).
- **Time-to-first-successful-run** for a new user: under 15 minutes
  including Ollama install.

## 9. Constraints

- Python 3.10+.
- System dependencies: Tesseract, Pandoc, libmagic (recommended),
  ExifTool (recommended).
- Ollama must be installed and reachable at the configured URL.
- Archives (`.zip`, `.tar`) must be decompressed before invocation —
  ClassifAI does not unpack them.

## 10. Open questions / future work

- Should there be a Streamlit-based taxonomy editor? (see
  [ADR-0006](adr/0006-yaml-driven-configuration.md))
- OCR fallback for scanned PDFs (currently PyMuPDF text-layer only —
  no OCR if the layer is empty). Tracked outside this PRD.
- Audio / video transcription (deferred; was noted in the archived
  IMPACT_ANALYSIS).

## 11. Reference

- ADRs: [`docs/adr/`](adr/)
- Changelog: [`CHANGELOG.md`](../CHANGELOG.md)
- User Guide: [`docs/user-guide/`](user-guide/)
- Archived historical specs: [`docs/archive/`](archive/)
