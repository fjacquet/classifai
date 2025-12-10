"""
Shared default values for CLI and Streamlit interfaces.

This module ensures consistent behavior across all ClassifAI entry points.
"""

from pathlib import Path

# Scanning defaults
DEFAULT_RECURSIVE = False
DEFAULT_RENAME_FILES = False
DEFAULT_LANGUAGE_SUBFOLDERS = False

# Logging defaults
DEFAULT_VERBOSE = False
DEFAULT_QUIET_LLM = False
DEFAULT_LOG_FILE = Path("logs/main.log")

# Directory defaults
DEFAULT_DESTINATION_FALLBACK_TO_SOURCE = True
