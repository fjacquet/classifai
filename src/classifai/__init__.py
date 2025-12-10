"""ClassifAI package initialization.

This module exposes the main entry points for the different interfaces:
- CLI: run_cli()
- Web UI: run_web_ui()
- API: run_api()
"""

from __future__ import annotations

__version__ = "0.2.0"

# Export main entry points
from classifai.main import run_api, run_cli, run_web_ui

__all__ = ["run_api", "run_cli", "run_web_ui", "__version__"]
