# Quickstart

Organize a folder of unsorted documents in five minutes.

## Prerequisites

- [Installation](installation.md) complete.
- Ollama is running (`ollama serve`) and a model is pulled.

## 1. Preview first (always)

Default mode is `dry-run` — nothing moves, you see the planned layout:

```bash
uv run classifai run --source-dir ~/Downloads/Inbox --mode dry-run
```

You'll see a table: source filename, detected language, category, issuer,
new filename, destination path.

Review it. If it looks right, continue.

## 2. Move for real

```bash
uv run classifai run \
  --source-dir ~/Downloads/Inbox \
  --destination-dir ~/Sorted \
  --mode move
```

You'll be asked to confirm before files are relocated.

Use `--mode copy` instead of `move` if you want to keep the originals.

## 3. Watch a folder continuously

Drop new scans/downloads into one folder and have ClassifAI organize them
as they arrive:

```bash
uv run classifai watch \
  --source-dir ~/Downloads/Inbox \
  --destination-dir ~/Sorted \
  --mode move
```

Runs until you interrupt it (Ctrl-C).

## 4. Undo

Made a mistake? Revert the last operation:

```bash
uv run classifai undo
```

`undo` is one step deep — it reverses the most recent move/copy logged
in `history.json`.

## 5. Using the Web UI instead

Prefer clicking to typing?

```bash
streamlit run src/classifai/classifai_app.py     # or: make web
```

Opens at `http://localhost:8501`. Same behavior, different skin. See
[Web UI](web-ui.md).

## Typical result

After a successful `move`, your target directory looks like:

```
~/Sorted/
├── fr/
│   └── Santé/
│       └── M-Thérapies/
│           └── Factures/
│               └── 2025-07-18_Consultation_orthopedie.pdf
└── en/
    └── Finance/
        └── UBS/
            └── Relevés/
                └── 2025-01-15_Monthly_statement.pdf
```

## Next steps

- Review [CLI reference](cli.md) for all options.
- Tune [Configuration](configuration.md) to add your own categories,
  sectors, rules, and issuer aliases.
- Read [Troubleshooting](troubleshooting.md) when something surprises you.
