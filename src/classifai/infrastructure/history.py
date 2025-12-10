"""
Infrastructure for history operations.

This module contains impure functions for interacting with the history file.
"""

import json
from pathlib import Path

from loguru import logger

HISTORY_FILE = Path("logs/history.json")


def log_operation(operation: str, source_path: str, dest_path: str) -> None:
    """
    Logs a file operation to the history file.

    Args:
        operation: The operation type (e.g., "move", "copy")
        source_path: The source file path
        dest_path: The destination file path
    """
    try:
        HISTORY_FILE.parent.mkdir(parents=True, exist_ok=True)
        history_entry = {
            "operation": operation,
            "source": source_path,
            "destination": dest_path,
        }

        history = []
        if HISTORY_FILE.exists() and HISTORY_FILE.stat().st_size > 0:
            with open(HISTORY_FILE) as f:
                history = json.load(f)

        history.append(history_entry)

        with open(HISTORY_FILE, "w") as f:
            json.dump(history, f, indent=4)
    except Exception as e:
        logger.error(f"Failed to log operation: {e}")
        raise


def get_last_operation() -> dict | None:
    """
    Retrieves the last operation from the history file.

    Returns:
        The last operation entry as a dict, or None if no history exists
    """
    try:
        if not HISTORY_FILE.exists() or HISTORY_FILE.stat().st_size == 0:
            return None

        with open(HISTORY_FILE) as f:
            history = json.load(f)

        if not history:
            return None
        return history[-1]
    except Exception as e:
        logger.error(f"Failed to get last operation: {e}")
        return None


def remove_last_operation() -> None:
    """
    Removes the last operation from the history file.
    """
    try:
        if not HISTORY_FILE.exists() or HISTORY_FILE.stat().st_size == 0:
            return

        with open(HISTORY_FILE) as f:
            history = json.load(f)

        if history:
            history.pop()

        with open(HISTORY_FILE, "w") as f:
            json.dump(history, f, indent=4)
    except Exception as e:
        logger.error(f"Failed to remove last operation: {e}")
        raise
