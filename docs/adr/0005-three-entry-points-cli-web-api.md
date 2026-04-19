# ADR-0005: Three entry points — CLI, Streamlit, FastAPI

- **Status:** Accepted
- **Date:** 2024 (codified retroactively 2026-04-19)
- **Deciders:** Frederic Jacquet

## Context

ClassifAI serves three distinct interaction modes:

1. **Batch / scripting** — one-shot organization of a directory, typically
   from a terminal or cron job.
2. **Interactive** — a non-technical user wants to preview, tweak options,
   and confirm operations before they run.
3. **Programmatic** — an external system (future: mobile app, home-server
   automation, another script) calls ClassifAI over HTTP.

Collapsing these into a single interface forces one audience into the wrong
mode.

## Decision

Ship **three entry points**, all backed by the same core pipeline
(`src/classifai/pipeline.py`) and the same configuration (`AppConfig`):

| Entry point      | Module                          | Audience            | Technology |
| ---------------- | ------------------------------- | ------------------- | ---------- |
| CLI              | `classifai_cli.py`              | Scripting, power    | Typer      |
| Web UI           | `classifai_app.py`              | Non-technical users | Streamlit  |
| REST API         | `app/` (FastAPI routes)         | Programmatic        | FastAPI    |
| Watcher daemon   | `background_watcher.py`         | Continuous inbox    | Watchdog   |

Shared helpers live in `entrypoint_utils.py` (`generate_file_operations`,
`perform_operations`) so each entry point is a thin shell around identical
logic. Defaults are centralized in `defaults.py` to keep CLI and Streamlit
behavior aligned.

## Rationale

- **Right tool per user.** A CLI is ideal for power users and cron; a
  Streamlit UI is a zero-code way to preview + confirm; a FastAPI surface
  lets other programs integrate.
- **Shared core = zero drift.** All three entry points call the same
  `run_scan` / pipeline functions. Adding a feature in the pipeline appears
  everywhere simultaneously.
- **Centralized defaults.** `defaults.py` was added specifically to stop
  CLI and Streamlit drifting apart (`recursive` defaulted differently; see
  CHANGELOG Unreleased "CLI/Streamlit Defaults Aligned").
- **Watchdog as a 4th facade.** The background watcher reuses the same
  pipeline on file-system events. Same logic, different trigger.

## Alternatives considered

1. **CLI-only.** Rejected: excludes the non-technical audience the UI is
   designed for (spouse/family organizing their own inbox).
2. **Web-only (Streamlit).** Rejected: awkward for scripting, cron, CI,
   headless servers.
3. **API-only (with separate clients).** Rejected: overkill for a local
   desktop tool; adds HTTP deployment complexity for every user.
4. **CLI + Web, drop API.** Reasonable, but blocks future automation
   scenarios; the FastAPI surface is small and cheap to maintain.

## Consequences

- **Positive:** Each audience gets the right ergonomics. Shared core
  prevents behavior drift. Adding a feature touches one place.
- **Negative:**
  - Four surfaces to keep docs and help-text in sync with.
  - Streamlit and Typer have different defaulting idioms — hence the
    need for `defaults.py`.
  - Testing effort multiplies: happy path must be verified on at least
    CLI and Streamlit.
- **Contract:** When a new flag is added, it MUST be added to
  `defaults.py` (if defaultable) and exposed on CLI + Streamlit before
  the PR lands.

## References

- `src/classifai/classifai_cli.py`
- `src/classifai/classifai_app.py`
- `src/classifai/app/` (FastAPI routes)
- `src/classifai/background_watcher.py`
- `src/classifai/entrypoint_utils.py`, `defaults.py`
