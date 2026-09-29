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
results, different ergonomics:

- **Sidebar configuration** — text inputs for the source and destination
  directories, the Ollama API URL and the completion model, a
  categories text area, option checkboxes and logging options.
- **Scan = preview** — scanning never moves anything; it fills an
  editable table with the planned organization. There is no separate
  dry-run mode.
- A confirmation step before any copy / move.
- A progress bar while files are copied or moved.
- File logging to `logs/main.log` (same as the CLI).

## Sidebar

| Section                  | Control                          | Default |
| ------------------------ | -------------------------------- | ------- |
| 📁 Directory Settings    | **Source Directory**             | `~/Downloads` |
|                          | **Destination Directory**        | same as the source |
| 🧠 AI & Model Settings   | **Ollama API URL**               | `OLLAMA_API_URL` |
|                          | **Completion Model**             | `OLLAMA_MODEL_NAME` |
|                          | **Categories (one per line)**    | `config/categories.yaml` |
| ⚙️ Other Options         | Recursive Scan                   | off |
|                          | Create Language Subfolders       | off |
|                          | Enable AI-Powered Renaming       | off |
|                          | Use Vision Model for Images      | `use_vision_model` in `settings.yaml` |
| 📋 Logging               | Verbose Logging / Quiet LLM Logs | off |

Checkbox defaults come from `src/classifai/defaults.py`, like the CLI.
Edits to the categories list apply to this session's scans only; the
YAML file is not changed.

## Typical workflow

1. Type the **source directory** (and, optionally, the **destination
   directory**) in the sidebar.
2. Adjust the model, categories and options if needed.
3. Click **Scan Directory**. The **Results** table shows, per file, the
   detected language, category, issuer, new filename and destination
   path.
4. Edit the table if needed — the **Destination Path** column is what
   will be used — or remove rows you don't want to process.
5. Click **Copy Files** or **Move Files**, then **✅ Confirm** (or
   **❌ Cancel**).
6. A summary shows how many files succeeded; the results table is
   cleared.

## Parity with the CLI

Both interfaces:

- Read the same `config/` YAML files.
- Use the same pipeline, with the Ollama URL and model you enter.
- Respect the same defaults (see [ADR-0005](../adr/0005-three-entry-points-cli-web-api.md)).
- Write the same history file, so `classifai undo` from the terminal
  works on an operation done in the UI.

Differences: the UI does not validate `rules.yaml` at startup (the CLI
does), and unknown issuers go to `Unknown_Issuer` rather than
`Émetteur_Inconnu`.

If you notice other behavior drift between the two, it's a bug — please
report it.

## When to use which

| Use the UI when…                                   | Use the CLI when…                              |
| -------------------------------------------------- | ---------------------------------------------- |
| You want to preview visually                       | You want to script / cron / CI                 |
| You're on your own machine and want low friction   | You're on a headless server                    |
| A non-technical family member is using ClassifAI   | You need fine-grained flags or piping          |

Both can coexist — Streamlit doesn't lock anything; you can switch to the
CLI for one run and back.
