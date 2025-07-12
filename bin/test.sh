#!/bin/bash
set -e
uv run pytest --cov --cov-branch --cov-report=xml
