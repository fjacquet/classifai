# ADR-0002: Hybrid rule-based + LLM classification

- **Status:** Accepted
- **Date:** 2024 (codified retroactively 2026-04-19)
- **Deciders:** Frederic Jacquet

## Context

ClassifAI must assign every incoming file to a `Sector/Issuer/Category/Language`
tuple. Two obvious pure strategies exist:

1. **Pure LLM classification** — send every file's extracted text to the model
   and let it return all fields.
2. **Pure rules** — hand-written YAML regex/glob rules cover every case.

Both fail alone. Pure-LLM is slow, non-deterministic, and expensive for trivial
cases (a PDF named `UBS_statement_2025-01.pdf` does not need a 7B-parameter
model). Pure-rules cannot cope with unseen issuers, cross-language documents,
or handwritten/scanned material.

## Decision

Classification follows a **fixed-priority cascade**:

1. **Early rules** (filename/path patterns, MIME type) — runs before parsing.
   Matches short-circuit the pipeline.
2. **Full rules** (metadata-driven) — runs after parsing but before LLM.
3. **Knowledge-base lookup** — issuer → sector via
   `config/sector_issuer_mapping.yaml` (with alias normalization).
4. **LLM enrichment** — Ollama model fills whatever's still missing
   (language, category, title, date, unknown issuer).
5. **Fuzzy post-fix** — `difflib.get_close_matches` at 85% threshold catches
   LLM typos like `Fichieurs Texte` → `Fichiers Texte`.

Each step only runs if the previous step left fields unset. The LLM is the
**fallback**, not the default.

## Rationale

- **Latency & cost:** Rules match in milliseconds; LLM calls take seconds.
  The vast majority of the user's own documents (recurring issuers, known
  file-naming patterns) resolve at step 1 or 2, keeping the pipeline cheap.
- **Determinism & auditability:** Rules are versioned YAML — decisions are
  reproducible and reviewable. LLM output is only invoked when rules can't
  reach a conclusion, confining non-determinism to the unknown tail.
- **Progressive enrichment:** The LLM discovers new issuers, which get
  recorded to `config/unknown_issuers.yaml` for human review and promotion
  into the knowledge base. The rule surface grows over time; LLM dependence
  shrinks.
- **Graceful degradation:** If Ollama is unreachable, early-rule and
  knowledge-base paths still classify a significant share of files — the
  system doesn't hard-fail.

## Alternatives considered

1. **Pure-LLM.** Rejected: unnecessary cost/latency for trivially-classifiable
   files; fragile to model regressions; harder to audit.
2. **Pure-rules + manual tail.** Rejected: does not scale to novel issuers or
   multilingual content; high maintenance burden.
3. **Embedding-based retrieval.** Tried and removed in 0.2.0 era (see
   `CHANGELOG.md`). Added dependency weight (vector DB + embedding model) for
   marginal gains over explicit rules + LLM fallback.

## Consequences

- **Positive:** Fast hot path; deterministic where it matters; LLM workload
  minimized; knowledge base improves over time via the unknown-issuer loop.
- **Negative:** Two configuration surfaces (rules.yaml *and* mapping yaml);
  onboarding requires understanding both; rule ordering matters and is not
  obvious from code.
- **Follow-up:** Document the rule schema and the unknown-issuer review
  workflow in the User Guide.

## References

- `src/classifai/core/rules.py` — rule matching
- `src/classifai/infrastructure/knowledge_base.py` — KB lookup + alias handling
- `src/classifai/pipeline.py` — cascade orchestration
- `config/rules.yaml`, `config/sector_issuer_mapping.yaml`
