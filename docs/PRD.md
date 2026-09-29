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
   and watcher.

## 4. Non-goals

1. Cloud-hosted multi-tenant service.
2. Full-text search / vector retrieval over the corpus (removed;
   see CHANGELOG).
3. ZIP / archive extraction — expected to be done before ClassifAI runs
   (see [Constraints](#9-constraints) below).
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
/Sorted/en/Banque/UBS/Relevés Bancaires/2025-01-15_Monthly_statement.pdf
```

- `Language` is ISO 639-1 (`fr`, `en`, …) when `--language-subfolders` is
  on; otherwise, or if undetectable, `fr`.
- `<Date>_<Title>` is only applied with `--rename-files`; otherwise the
  original filename is kept.
- `Date` is ISO 8601 `YYYY-MM-DD`: the first valid date among the LLM's
  document date and the file's metadata creation / EXIF date.
- `Title` is produced by the LLM (concise, descriptive, filename-safe).
- Filename is sanitized via `utils.sanitize_filename`.
- `Issuer` is the canonical name from the knowledge base when the issuer
  is known, so name variants share one folder.
- Rule-matched files go to
  `<destination>/[fr/]Secteur_Inconnu/<unknown issuer>/<Category>/<original name>`.
- Images classified `Images` with an EXIF date go to
  `<destination>/[<Language>/]Photos/YYYY/MM_Month/[<City, Country>/]` (location only
  with opt-in online geocoding).

### 5.2 Classification pipeline

Implementation of [ADR-0002](adr/0002-hybrid-rule-plus-llm-classification.md).
Fixed order:

1. **Early rules** match on filename / path (fnmatch globs) before
   parsing. A match skips parsing and the LLM.
2. **Parsing** extracts text, MIME type and metadata.
3. **Full rules** match on MIME type + metadata after parsing. A match
   skips the LLM.
4. **LLM enrichment** extracts issuer, category, date, title and
   language via Ollama, with the category constrained to
   `categories.yaml` by a JSON schema. Skipped when no text was extracted.
5. **Fuzzy correction** fixes LLM category typos (≥85% match) via
   `difflib.get_close_matches`; otherwise the category is `_UNKNOWN_`.
6. **Knowledge-base lookup** maps the extracted issuer → sector and
   canonical name (`config/sector_issuer_mapping.yaml`, with accent-folding
   normalization, aliases and whole-word matching).
7. **AI sector fallback** asks the LLM for a sector from
   `config/sectors.yaml` when the issuer is unknown.
8. **Path determination** builds the destination (section 5.1).

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

- New issuers discovered by the LLM are recorded in
  `config/unknown_issuers.yaml`, keyed by normalized name, with the
  original name, first/last-seen timestamps and a count (written
  atomically).
- CLI command `classifai kb-list-unknown` surfaces them for review
  (issuer, count, last seen).
- Admin moves reviewed issuers into `sector_issuer_mapping.yaml` (as
  canonical entries or aliases) — a manual promotion step by design.

### 5.5 File type support

Scanned extensions are `DEFAULT_SUPPORTED_EXTENSIONS`
(`src/classifai/config.py`, overridable with `supported_extensions` in
`config/settings.yaml`) plus `generic_text_extensions` from
`config/settings.yaml`. Hidden files and Office lock files (`~$…`) are
skipped.

| Category        | Extensions                                              | Parser      |
| --------------- | ------------------------------------------------------- | ----------- |
| Documents       | `.pdf .docx .txt .rtf .odt`                             | Native (`.odt`: Pandoc); PDF: PyMuPDF → pdftotext → OCR of first 3 pages |
| Spreadsheets    | `.xlsx`                                                 | Native      |
| Presentations   | `.pptx .ppt .odp`                                       | Pandoc      |
| Images (OCR)    | `.png .jpg .jpeg .tiff .bmp`                            | Tesseract (`fra+eng+deu` when installed); optional vision model |
| Email           | `.msg .eml`                                             | Native      |
| Web             | `.html`                                                 | Native      |
| E-books         | `.epub`                                                 | Pandoc      |
| Technical docs  | `.md .rst .tex .latex .org`                             | Pandoc (`.md`: plain text when listed in `generic_text_extensions`) |
| Generic text    | `generic_text_extensions` (`.log .sh .csv .json .xml .ini .conf .cfg .vcf .ics …`) | Plain text |

External tools (`pdftotext`, `pandoc`) are stopped after 60 s.

### 5.6 Operation modes

- `dry-run` (default): preview the full plan; nothing is moved.
- `move`: relocate files; pre-confirm prompt in both CLI and UI.
- `copy`: duplicate files; original retained.
- **Undo**: `classifai undo` reverses the last operation using the
  `logs/history.json` log (written atomically); repeat to go further
  back.
- **Duplicates**: a file whose identical content (SHA-256) is already at
  the destination is skipped and the source kept; a different file with
  the same name gets `" (n)"` appended.

### 5.7 Language / localization

- LLM prompts are written in English; category and sector names (and
  the `_UNKNOWN_` category suggestion) are in **French** (internal
  simplification, not a user-facing setting).
- User-facing UI strings are resolved via
  `src/classifai/localization.py` (thread-safe via `contextvars`),
  currently FR and EN.

## 6. Non-functional requirements

1. **Privacy.** No document content is sent off-machine. Ollama default
   URL is `localhost:11434`. See [ADR-0003](adr/0003-ollama-as-llm-runtime.md).
   The only online feature — reverse-geocoding photo GPS coordinates via
   Nominatim — is off unless `online_geocoding: true` is set.
2. **Robustness.**
   - Tenacity-based retry on LLM calls (network errors and 5xx,
     exponential backoff); 120 s timeout.
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

- **Entry points:** CLI (Typer), Streamlit, Watchdog daemon — all
  share the core pipeline. ([ADR-0005](adr/0005-three-entry-points-cli-web-api.md))
- **Core / infrastructure split:** pure business logic in `core/`; I/O in
  `infrastructure/`.
- **LLM runtime:** Ollama's HTTP API (`/api/generate`) called directly with
  `httpx`, using JSON-schema structured outputs. ([ADR-0003](adr/0003-ollama-as-llm-runtime.md))
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
  ClassifAI does not unpack them (`.zip` files are rejected).

## 10. Open questions / future work

- Should there be a Streamlit-based taxonomy editor? (see
  [ADR-0006](adr/0006-yaml-driven-configuration.md))
- Audio / video transcription (deferred; was noted in the archived
  IMPACT_ANALYSIS).

## 11. Reference

- ADRs: [`docs/adr/`](adr/README.md)
- Changelog: [`CHANGELOG.md`](https://github.com/fjacquet/classifai/blob/main/CHANGELOG.md)
- User Guide: [`docs/user-guide/`](user-guide/index.md)
- Archived historical specs: `docs/archive/` in the repository (not part
  of this site)
