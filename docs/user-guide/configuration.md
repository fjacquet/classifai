# Configuration

Everything you can tune lives in two places:

1. **Environment variables** (`.env` file or shell) — runtime wiring.
2. **YAML files under `config/`** — taxonomy and rules.

See [ADR-0006](../adr/0006-yaml-driven-configuration.md) for the rationale.

## Environment variables

| Variable                     | Default                    | Purpose                                     |
| ---------------------------- | -------------------------- | ------------------------------------------- |
| `OLLAMA_MODEL_NAME`          | `gemma:2b`                 | Text LLM model                              |
| `OLLAMA_VISION_MODEL_NAME`   | `llava`                    | Vision model (used with `--use-vision`)     |
| `OLLAMA_API_URL`             | `http://localhost:11434`   | Ollama endpoint                             |

Loaded via `python-dotenv` — drop a `.env` in the repo root.

## YAML files

### `config/categories.yaml`

A flat list of every category a document can be assigned to.

```yaml
- Analyses
- Contrats
- Factures
- Rapports
- Relevés
# ...
```

- The LLM is **constrained** to this list — it cannot invent new values.
- Add new categories as you need them; remove old ones freely.
- `ClassifAI` validates at startup that every category referenced in
  `rules.yaml` exists here. Missing? Startup fails with a clear error.

### `config/sectors.yaml`

Flat list of every valid business sector.

```yaml
- Banque
- Santé
- Commerce
- Assurance
# ...
```

Same semantics as categories — the LLM-based sector fallback is
constrained to this list.

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

At runtime ClassifAI flattens this into an **issuer → sector** dict for
O(1) lookup. Aliases are applied so all variations land in the same
canonical folder.

### `config/rules.yaml`

Ordered rules that short-circuit the LLM. Two kinds:

- **Early rules** — match before parsing, using filename / path / MIME.
- **Full rules** — match after parsing, using metadata + MIME.

```yaml
rules:
  - name: "UBS statements by filename"
    phase: early
    conditions:
      - field: filename
        pattern: "^UBS.*statement.*\\.pdf$"
    classification:
      sector: Banque
      issuer: UBS
      category: Relevés

  - name: "Scanned invoices by MIME"
    phase: full
    conditions:
      - field: mime_type
        pattern: "image/*"          # prefix match
      - field: metadata
        key: exif.DocumentType
        match: contains
        value: invoice
    classification:
      category: Factures
```

Condition `match` operators: `exact`, `contains`, `startswith`,
`endswith`, `glob`. Default is `exact` when unspecified.

Rules are evaluated **top to bottom**; the first match wins within its
phase.

### `config/unknown_issuers.yaml`

**Generated, not hand-edited.** When the LLM identifies an issuer that
isn't in `sector_issuer_mapping.yaml`, it gets appended here with a
timestamp and an AI-suggested sector.

Review periodically with:

```bash
uv run classifai kb-list-unknown
```

When you spot a legitimate new issuer, move it into
`sector_issuer_mapping.yaml` (as a canonical entry or as an alias of an
existing one) and optionally clear the row from `unknown_issuers.yaml`.

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
recognizable variant as the canonical name.

The **unknown-issuer workflow** turns LLM discoveries into durable
knowledge:

1. LLM encounters an unseen issuer → appends to `unknown_issuers.yaml`.
2. You review with `classifai kb-list-unknown`.
3. You promote it into `sector_issuer_mapping.yaml` (canonical or alias).
4. Future runs match it via the fast rule path, skipping the LLM.

Over time the LLM's share of classification shrinks.

## Validation at startup

`src/classifai/validation.py` verifies that every category referenced in
`rules.yaml` exists in `categories.yaml`. A drift will fail the startup
with an explicit error — fix the YAML, don't suppress the check.

## Formatting YAML

The project uses `yamlfix` (via pre-commit and Makefile):

```bash
uv run yamlfix config/        # format everything under config/
```

Pre-commit runs this automatically on staged `config/*.yaml` files.
