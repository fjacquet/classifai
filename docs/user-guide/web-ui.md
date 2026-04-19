# Web UI (Streamlit)

A browser-based interface for users who don't want to touch a terminal.

## Start it

```bash
streamlit run src/classifai/classifai_app.py
# or
make web
```

Opens at `http://localhost:8501`. Close with Ctrl-C in the terminal.

## What it does

The UI wraps the same core pipeline as the CLI — identical classification
results, different ergonomics. It adds:

- File-picker style directory selection.
- Live preview table of the planned organization.
- A confirmation dialog before any `move` / `copy` operation.
- Streaming log output while a run is in progress.
- File logging to `logs/main.log` (same as the CLI).

## Typical workflow

1. Pick a **source directory**.
2. (Optional) Pick a **destination directory** — defaults to the source.
3. Choose a **mode**: `dry-run`, `move`, or `copy`.
4. Toggle options (`recursive`, `rename`, `language_subfolders`,
   `use_vision`, …) — defaults match the CLI, coming from
   `src/classifai/defaults.py`.
5. Click **Preview** to see the plan.
6. Click **Execute** and confirm to apply it.

## Parity with the CLI

Both interfaces:

- Read the same `config/` YAML files.
- Use the same Ollama instance (from `OLLAMA_API_URL`).
- Respect the same defaults (see [ADR-0005](../adr/0005-three-entry-points-cli-web-api.md)).
- Write the same history file, so `classifai undo` from the terminal
  works on an operation done in the UI, and vice versa.

If you notice behavior drift between the two, it's a bug — please report
it.

## When to use which

| Use the UI when…                                   | Use the CLI when…                              |
| -------------------------------------------------- | ---------------------------------------------- |
| You want to preview visually                       | You want to script / cron / CI                 |
| You're on your own machine and want low friction   | You're on a headless server                    |
| A non-technical family member is using ClassifAI   | You need fine-grained flags or piping          |

Both can coexist — Streamlit doesn't lock anything; you can switch to the
CLI for one run and back.
