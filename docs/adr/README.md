# Architecture Decision Records (ADRs)

This directory holds ADRs for ClassifAI — short, immutable documents capturing
significant architectural decisions, their context, and their consequences.

## What is an ADR?

An ADR records **one decision** at a point in time. ADRs are append-only:
when a decision is revisited, write a new ADR that supersedes the old one —
do not edit history.

Format inspired by Michael Nygard's
["Documenting Architecture Decisions"](https://cognitect.com/blog/2011/11/15/documenting-architecture-decisions).

## Index

| #    | Title                                                                           | Status    |
| ---- | ------------------------------------------------------------------------------- | --------- |
| 0001 | [Stay on Tesseract for OCR; defer Chandra OCR 2](0001-ocr-engine-stay-on-tesseract.md) | Accepted  |
| 0002 | [Hybrid rule-based + LLM classification](0002-hybrid-rule-plus-llm-classification.md)  | Accepted  |
| 0003 | [Ollama as the LLM runtime](0003-ollama-as-llm-runtime.md)                      | Accepted  |
| 0004 | [Remove the `returns` library; use native exceptions](0004-remove-returns-library.md) | Accepted  |
| 0005 | [Three entry points — CLI, Streamlit, FastAPI](0005-three-entry-points-cli-web-api.md) | Accepted  |
| 0006 | [YAML-driven configuration for categories, sectors, rules](0006-yaml-driven-configuration.md) | Accepted  |

## When to write an ADR

Write one when:

- Choosing between plausible alternatives with real trade-offs (framework,
  library, data store, protocol).
- Deliberately *not* doing something a reasonable future contributor might
  assume should be done (see ADR-0001: not adopting Chandra OCR 2).
- Reversing or replacing a previous decision (new ADR with
  `Supersedes: XXXX-...`).

Do **not** write one for routine code changes, refactors, or bug fixes.

## Template

Copy this block into `NNNN-short-kebab-title.md`:

```markdown
# ADR-NNNN: Short imperative title

- **Status:** Proposed | Accepted | Superseded by ADR-XXXX | Deprecated
- **Date:** YYYY-MM-DD
- **Deciders:** name(s)
- **Supersedes:** ADR-XXXX (if applicable)

## Context

What's the situation that forces a decision? What constraints apply?
State the problem, not the solution.

## Decision

What are we doing? One paragraph, imperative voice.

## Rationale

Why? Enumerate the forces: speed, cost, privacy, ergonomics, fit with
existing stack, etc. Be concrete.

## Alternatives considered

For each plausible alternative: what it is, why we rejected it (one
paragraph each is usually enough).

## Consequences

What becomes easier, harder, more or less likely because of this decision?
Include both positive and negative outcomes. Note any follow-up work this
decision creates.

## References

Links to code, external docs, prior ADRs, issues.
```

## Conventions

- Number monotonically: `0001`, `0002`, … zero-padded to four digits.
- File names: kebab-case, descriptive but brief.
- Never delete an ADR. Mark it `Superseded by ADR-XXXX` and link forward.
- Keep each ADR under ~300 lines. If it's longer, you're documenting too
  many decisions in one file.
