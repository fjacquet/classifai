# ADR-0006: YAML-driven configuration for categories, sectors, rules

- **Status:** Accepted
- **Date:** 2024 (codified retroactively 2026-04-19)
- **Deciders:** Frederic Jacquet

## Context

ClassifAI needs a way to define and evolve:

- The fixed list of valid categories (`Factures`, `Contrats`, …)
- The fixed list of valid business sectors (`Banque`, `Santé`, …)
- The issuer → sector mapping and its aliases
- Classification rules (filename patterns, MIME conditions, metadata matchers)

These lists change over time as users organize new domains (moving abroad,
changing jobs, new vendors). They must be **edited without a code release**.

## Decision

Store all four surfaces as YAML files under `config/`:

- `config/categories.yaml` — flat list of valid categories
- `config/sectors.yaml` — flat list of valid sectors
- `config/sector_issuer_mapping.yaml` — nested map, with `aliases` section
- `config/rules.yaml` — ordered list of rule objects (early + full)

Loaded once at startup into the frozen `AppConfig` dataclass
(`src/classifai/config.py`). Validation at startup checks that every category
referenced in `rules.yaml` exists in `categories.yaml` — the app fails fast
if it doesn't.

Model identities live in `.env` / environment variables
(`OLLAMA_MODEL_NAME`, `OLLAMA_API_URL`, `OLLAMA_VISION_MODEL_NAME`), not
in YAML — they're deployment concerns, not taxonomy.

## Rationale

- **Human-editable without rebuilds.** Users change their own taxonomy by
  editing a file; no code deployment, no migration.
- **Version-controlled & reviewable.** YAML diffs are clean in Git; adding
  a sector or alias is a readable one-line commit.
- **No DB dependency.** A document classifier that organizes files on disk
  should not require a database server.
- **Frozen at startup.** Loaded once into an immutable `AppConfig`. No
  mid-run reloads, no cache-coherence bugs.
- **Fails fast.** `validation.py` cross-checks rules vs. categories at
  startup — a rule referencing a dropped category surfaces immediately,
  not on the first matching document.
- **`yamlfix` keeps it tidy.** Pre-commit and CI run `yamlfix` so the
  files stay canonical regardless of who edited them.

## Alternatives considered

1. **Embed taxonomy in Python code.** Rejected: requires a release for
   every taxonomy change; alienates non-developer users.
2. **SQLite / Postgres backend.** Rejected: deployment overhead far
   outweighs benefit for data that fits on one screen and changes weekly
   at most.
3. **TOML.** Viable, but YAML handles nested lists/maps more ergonomically
   for the issuer → sector → aliases shape, and the project already uses
   YAML for pre-commit and mkdocs.
4. **JSON.** Rejected: no comments, worse for human hand-editing.
5. **pydantic-settings driving everything.** `pydantic-settings` is already
   a dependency and used for env vars. Extending it to wrap the YAML files
   is a reasonable incremental improvement (future ADR if taken).

## Consequences

- **Positive:** Evolve taxonomy without deploys; taxonomy is readable in
  PR review; zero DB footprint; startup validation catches drift.
- **Negative:**
  - No runtime UI to edit the taxonomy — users must touch YAML.
  - Typos in YAML keys fail at startup, not at write time. Mitigated by
    `check-yaml` pre-commit hook + explicit validation.
  - Two sources of truth exist (YAML for taxonomy, `.env` for runtime) —
    new contributors must learn which is which.
- **Follow-up:** Consider a Streamlit-based taxonomy editor if users
  request it — doesn't change the ADR, just wraps YAML with a UI.

## References

- `src/classifai/config.py` — loader + `AppConfig`
- `src/classifai/validation.py` — rules-vs-categories cross-check
- `config/` directory — the YAML files themselves
- [yamlfix](https://lyz-code.github.io/yamlfix/)
