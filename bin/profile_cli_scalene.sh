#!/usr/bin/env bash
# Profile the ClassifAI CLI with Scalene.
#
# Usage:
#   bin/profile_cli_scalene.sh --source-dir <DIR> [other classifai_cli options]
#
# It writes an interactive HTML report (scalene_report.html by default) that you
# can open in a browser.
#
# Environment variables:
#   SCALENE_OUT  Override the output file name (default: scalene_report.html)
#
set -euo pipefail

OUT_FILE="${SCALENE_OUT:-scalene_report.html}"

# Ensure Scalene is available in the venv (run via `uv run`).
uv run scalene -o "$OUT_FILE" -m classifai.classifai_cli -- run "$@"

echo "Scalene profile written to $OUT_FILE"
