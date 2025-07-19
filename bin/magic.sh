#!/bin/bash
set -e



uv run main.py run  -d 'Documents' -m dry-run -r -ls -R -v -s "$@"