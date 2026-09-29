# Configuration

Everything you can tune lives in two places:

1. **Environment variables** (`.env` file or shell) — runtime wiring.
2. **YAML files under `config/`** — taxonomy, rules and settings.

The `config/` directory is resolved relative to the current working
directory, so run ClassifAI from the repository root. Files are read once
at startup.

See [ADR-0006](../adr/0006-yaml-driven-configuration.md) for the rationale.

## Environment variables

| Variable                     | Default                    | Purpose                                     |
| ---------------------------- | -------------------------- | ------------------------------------------- |
| `OLLAMA_MODEL_NAME`          | `gemma:2b`                 | Text LLM model (override with `--ollama-model`) |
| `OLLAMA_VISION_MODEL_NAME`   | `llava`                    | Vision model (used with `--use-vision`)     |
| `OLLAMA_API_URL`             | `http://localhost:11434`   | Ollama endpoint (override with `--ollama-url`) |

Loaded via `python-dotenv` — drop a `.env` in the repo root.

## YAML files

### `config/categories.yaml`

A flat list of every category a document can be assigned to.

```yaml
- Analyses
- Contrats
- Factures
- Rapports
- Relevés Bancaires
# ...
```

- The LLM is **constrained** to this list (JSON-schema enum) — it cannot
  invent new values. When it has no fitting answer the file goes to
  `_UNKNOWN_` (see [LLM behaviour](#llm-behaviour)).
- Add new categories as you need them; remove old ones freely.
- `classifai run`, `classifai watch` and the Web UI validate at startup that every category referenced in
  `rules.yaml` exists here. Missing? The run stops with a clear error.
- `Images` is special: images classified `Images` that carry an EXIF date
  are filed as photos (see [Photos](#photos)).
- The Web UI lets you edit this list for a session in its sidebar; the
  file itself is not changed.

### `config/sectors.yaml`

Flat list of every valid business sector.

```yaml
- Banque
- Santé
- Commerce
- Assurance
# ...
```

Used by the AI sector fallback: when an issuer is not in the knowledge
base, the model picks its sector from this list (JSON-schema enum) or
answers `null`, and the file goes to `Secteur_Inconnu`. Sectors from
`sector_issuer_mapping.yaml` are used as written, whether or not they
appear here.

### `config/sector_issuer_mapping.yaml`

The knowledge base. Maps **sectors → issuers**, with an optional
**aliases** section.

```yaml
Banque:
  - UBS
  - PostFinance
  - BCV

Santé:
  - Médecins
  - Hôpitaux
  - Helsana

Commerce:
  - Migros
  - Amazon

aliases:
  "UBS AG": "UBS"
  "UBS Switzerland AG": "UBS"
  "PostFinance AG": "PostFinance"
  "AXA Winterthur": "AXA"
  "Swiss Life AG": "Swiss Life"
```

How the issuer extracted by the LLM is matched:

1. **Normalize** — lowercase, accents folded (`Mobilière` = `Mobiliere`),
   punctuation turned into spaces, whitespace collapsed.
2. **Resolve aliases** — if the normalized issuer equals a normalized
   alias key, it is replaced by that alias's canonical name.
3. **Match** — sectors are scanned in file order; the first mapped issuer
   that appears as **whole words** inside the normalized issuer wins. So
   `UBS AG` matches `UBS`, but `Swiss` does not match `Swiss Life`.

On a match the file is filed under the **canonical issuer name as written
in the mapping** (e.g. `UBS AG` and `UBS Switzerland AG` both land in one
`UBS` folder), in that entry's sector. With no match the issuer is
recorded in [`unknown_issuers.yaml`](#configunknown_issuersyaml) and the
AI sector fallback is used (with the issuer name as extracted).

### `config/rules.yaml`

Ordered rules that assign a **category** without calling the LLM. See
`config/rules.yaml.example` for a commented starting point.

```yaml
rules:
  - name: "UBS statements by filename"
    conditions:
      - type: filename
        pattern: "UBS*statement*.pdf"   # fnmatch glob, case-sensitive
    action:
      type: categorize
      category: Relevés Bancaires

  - name: "Scanned invoices"
    conditions:
      - type: mime_type
        pattern: "image/*"              # exact type, or "prefix/*"
      - type: metadata
        field: title
        pattern: invoice
        match: contains                 # default: contains
    action:
      type: categorize
      category: Factures
```

Each rule has a `name`, a list of `conditions` (**all** must match) and an
`action` of `type: categorize` with a `category` from `categories.yaml`.
Rules can only set the category — not the sector or issuer.

| Condition `type` | Keys                          | Matches                                                        |
| ---------------- | ----------------------------- | -------------------------------------------------------------- |
| `filename`       | `pattern`                     | File name, as an `fnmatch` glob (`*`, `?`, `[...]`), case-sensitive |
| `path`           | `pattern`                     | Absolute resolved path, as an `fnmatch` glob, case-sensitive   |
| `mime_type`      | `pattern`                     | Detected MIME type: exact (`application/pdf`) or prefix (`image/*`) |
| `metadata`       | `field`, `pattern`, `match`   | A metadata field (e.g. `author`, `title`, `subject`, `creation_date`), case-insensitive |

Metadata `match` operators: `exact`, `contains`, `startswith`,
`endswith`, `glob`. Default is `contains` when unspecified. A metadata
condition fails when the field is absent.

The phase is inferred — there is no `phase` key:

- **Early rules** — every condition is `filename` or `path`. Evaluated
  **before parsing**; a match skips text extraction and the LLM.
- **Full rules** — at least one `mime_type` or `metadata` condition.
  Evaluated **after parsing**, only if no early rule matched.

Within each phase rules are evaluated **top to bottom**; the first match
wins.

Rule-matched files skip the LLM and the knowledge base, keep their name,
and land in:

```
<destination>/[fr/]Secteur_Inconnu/<unknown issuer>/<category>/<original name>
```

The `fr/` level only appears with `--language-subfolders` (no language is
detected for rule matches). Placeholder folders (`Secteur_Inconnu`,
`Émetteur_Inconnu`, `Non Classé`) are the same whatever the entry point.

At startup `classifai run` rejects rules whose category is not in
`categories.yaml` and conditions with an unknown `type` or `match` (see
[Validation at startup](#validation-at-startup)).

### `config/unknown_issuers.yaml`

**Generated, not hand-edited.** When the LLM identifies an issuer that
isn't in `sector_issuer_mapping.yaml`, it is recorded here, keyed by its
normalized name. The file is rewritten atomically after each update.

```yaml
groupe mutuel:
  original_name: Groupe Mutuel
  first_seen: '2026-09-20T08:14:03.512345+00:00'
  last_seen: '2026-09-28T17:40:11.004321+00:00'
  count: 3
```

No sector is stored — the AI sector fallback is recomputed per document.

Review periodically with:

```bash
uv run classifai kb-list-unknown
```

When you spot a legitimate new issuer, move it into
`sector_issuer_mapping.yaml` (as a canonical entry or as an alias of an
existing one) and optionally clear the row from `unknown_issuers.yaml`.

### `config/settings.yaml`

General settings. Every key is optional
(`config/settings.yaml.example` shows them).

| Key                       | Default                       | Purpose |
| ------------------------- | ----------------------------- | ------- |
| `generic_text_extensions` | `[]` (the shipped file lists `.log .sh .pem .ppk .pass .csv .xml .json .ini .conf .cfg .md .txt .rtf .opml .vcf .ics`) | Extensions read as plain text (UTF-8, then Windows-1252, then Latin-1) when no specific parser exists; also added to the scanned extensions |
| `supported_extensions`    | built-in list (see below)     | Replaces the built-in list of scanned extensions |
| `use_vision_model`        | `false`                       | Default for `--use-vision` / the Web UI checkbox |
| `online_geocoding`        | `false`                       | Reverse-geocode photo GPS coordinates to a `City, Country` folder |

`online_geocoding` is **opt-in** because it sends the photo's GPS
coordinates to OpenStreetMap Nominatim over the internet. Lookups are
cached (coordinates rounded to ~100 m) and limited to one request per
second, per the Nominatim usage policy.

### Supported file types

A scan picks up files whose extension is in `supported_extensions` or
`generic_text_extensions`. The built-in `supported_extensions`
(`DEFAULT_SUPPORTED_EXTENSIONS` in `src/classifai/config.py`):

| Kind            | Extensions                                   | Extraction |
| --------------- | -------------------------------------------- | ---------- |
| PDF             | `.pdf`                                       | PyMuPDF text layer → `pdftotext` → OCR of the first 3 pages (scanned PDFs) |
| Word            | `.docx`                                      | python-docx |
| Spreadsheets    | `.xlsx`                                      | openpyxl (cell values) |
| Text            | `.txt .md .rtf`                              | Plain text (`.md`, `.txt` via `generic_text_extensions`); striprtf for `.rtf` |
| OpenDocument, presentations, e-books, markup | `.odt .odp .pptx .ppt .epub .rst .tex .latex .org` | Pandoc (plain-text output); formats your Pandoc version cannot read yield no text |
| Images          | `.png .jpg .jpeg .tiff .bmp`                 | Tesseract OCR, EXIF date/GPS; optional vision model |
| Email           | `.eml .msg`                                  | Headers + body (`.eml`: declared charset honoured, plain-text part preferred, HTML part otherwise) |
| Web             | `.html`                                      | BeautifulSoup text (declared charset honoured) |

Notes:

- OCR uses the Tesseract languages `fra+eng+deu` that are installed.
- `pdftotext` and `pandoc` are stopped after 60 seconds.
- Archives (`.tar .gz .bz2 .xz`) have a parser that lists the files they
  contain (nothing is extracted), but they are only scanned if you add
  them to `supported_extensions`. `.zip` files are always rejected —
  decompress them first.
- When no text can be extracted, the LLM is not called and the file goes
  to `_UNKNOWN_` (unless a rule matched, or the vision model is used).

## LLM behaviour

ClassifAI calls Ollama's `/api/generate` endpoint directly over HTTP
(`src/classifai/infrastructure/llm.py`):

- **Structured outputs** — each call sends a JSON schema: `category` is
  restricted to `categories.yaml` (or `null`), and the AI sector fallback
  to `sectors.yaml` (or `null`). A category that still misses the list is
  corrected by fuzzy matching (≥ 85 % similarity) or rejected.
- **Deterministic settings** — `temperature: 0`, `num_ctx: 8192`,
  `keep_alive: 10m` (the model stays loaded between files).
- **Retries** — network errors and HTTP 5xx responses (e.g. 503 while a
  model loads) are retried up to 3 attempts with exponential backoff; 4xx
  errors fail immediately. Timeout: 120 s per request.
- **Prompt hygiene** — document text is fenced in `<document>` tags and
  treated as data; long documents keep their head and tail
  (4 000 characters in total) so letterheads and totals both survive.
  Useful metadata (author, title, subject, keywords, creation date,
  location) is passed as hints.
- **No text, no call** — if nothing could be extracted from a document,
  the model is skipped and the file goes to `_UNKNOWN_`.
- **`_UNKNOWN_`** — when no valid category comes back, the category is
  `_UNKNOWN_` and the model is asked to suggest a new French category
  name, appended to the filename when renaming
  (`…_suggested-Frais-Médicaux.pdf`).

## Destination layout

```
<destination>/<language>/<sector>/<issuer>/<category>/<filename>
```

- `<language>` is the detected ISO 639-1 code with
  `--language-subfolders`, `fr` otherwise (and `fr` when no language was
  detected).
- `<sector>` falls back to `Secteur_Inconnu`, `<category>` to
  `Non Classé`.
- `<issuer>` falls back to `Émetteur_Inconnu`.
- Rule-matched files use the layout described under
  [`config/rules.yaml`](#configrulesyaml).

### Photos

Files classified `Images` that have an EXIF date (`DateTimeOriginal`)
are filed by date instead:

```
<destination>/[<language>/]Photos/YYYY/MM_Month/[<City, Country>/]<filename>
```

The location level only appears when `online_geocoding` is enabled and
the photo has GPS coordinates.

## Shared defaults (`src/classifai/defaults.py`)

Controls values used by **both** CLI and Streamlit. Change here if you
want a different out-of-the-box default without flags.

```python
DEFAULT_RECURSIVE = False
DEFAULT_RENAME_FILES = False
DEFAULT_LANGUAGE_SUBFOLDERS = False
DEFAULT_VERBOSE = False
DEFAULT_QUIET_LLM = False
DEFAULT_LOG_FILE = Path("logs/main.log")
```

## Issuer aliases and unknown issuers

The alias system handles the fact that the same entity appears under
multiple legal/linguistic names:

- `UBS AG`, `UBS Switzerland AG` → canonical `UBS`
- `Helsana Assurance` → canonical `Helsana`
- `La Poste - PostFinance` → canonical `PostFinance`

Add aliases as you encounter them during review. Choose the most
recognizable variant as the canonical name, and list it under a sector —
the alias value is matched against the sector entries like any extracted
issuer, and that entry's name becomes the folder.

An alias key must equal the whole extracted name (after normalization).
Variants that already contain a mapped name as whole words (`UBS AG`
contains `UBS`) match even without an alias; aliases matter for names
that don't, such as `Union Bank of Switzerland` → `UBS`.

The **unknown-issuer workflow** turns LLM discoveries into durable
knowledge:

1. LLM encounters an unseen issuer → recorded in `unknown_issuers.yaml`
   (with a count and first/last-seen timestamps).
2. You review with `classifai kb-list-unknown`.
3. You promote it into `sector_issuer_mapping.yaml` (canonical or alias).
4. Future documents from that issuer get their sector and canonical
   folder name from the knowledge base, without the AI sector fallback
   call.

Over time the AI sector fallback is needed less and less.

## Validation at startup

Before processing files, `classifai run`, `classifai watch` and the Web UI
call `validate_app_config` in `src/classifai/validation.py`,
which raises a `ConfigurationError` listing every problem found:

- a rule whose category is not in `categories.yaml`
  (`Found rules with invalid categories: …`);
- a condition whose `type` is not `filename`, `path`, `mime_type` or
  `metadata`, or a metadata `match` that is not one of the five operators
  (`Found invalid rule conditions: …`).

The CLI prints the message and exits with code 1; the Web UI shows it and
stops. Fix the YAML — don't suppress the check.

## Formatting YAML

The project formats YAML with [`yamlfmt`](https://github.com/google/yamlfmt)
via pre-commit (settings in `.yamlfmt.yaml`):

```bash
uv run pre-commit run yamlfmt --all-files
```

Pre-commit runs it automatically on staged YAML files, together with
`check-yaml`.
