"""
History module for ClassifAI.

This module handles logging and retrieving file operations to support undo functionality.
"""

import json
from pathlib import Path

from loguru import logger

HISTORY_FILE = Path("logs/history.json")


def log_operation(operation: str, source_path: str, dest_path: str):
    """
    Logs a file operation to the history file.

    Args:
        operation (str): The type of operation (e.g., "move", "copy").
        source_path (str): The source file path.
        dest_path (str): The destination file path.
    """
    HISTORY_FILE.parent.mkdir(parents=True, exist_ok=True)
    history_entry = {
        "operation": operation,
        "source": source_path,
        "destination": dest_path,
    }

    try:
        history = []
        if HISTORY_FILE.exists() and HISTORY_FILE.stat().st_size > 0:
            with open(HISTORY_FILE) as f:
                history = json.load(f)

        history.append(history_entry)

        with open(HISTORY_FILE, "w") as f:
            json.dump(history, f, indent=4)

    except (OSError, json.JSONDecodeError) as e:
        logger.error(f"Error writing to history file {HISTORY_FILE}: {e}")


def get_last_operation() -> dict | None:
    """
    Retrieves the last operation from the history file.

    Returns:
        A dictionary representing the last operation, or None if history is empty.
    """
    if not HISTORY_FILE.exists() or HISTORY_FILE.stat().st_size == 0:
        return None

    try:
        with open(HISTORY_FILE) as f:
            history = json.load(f)
        return history[-1] if history else None
    except (OSError, json.JSONDecodeError) as e:
        logger.error(f"Error reading from history file {HISTORY_FILE}: {e}")
        return None


def remove_last_operation():
    """
    Removes the last operation from the history file.
    """
    if not HISTORY_FILE.exists() or HISTORY_FILE.stat().st_size == 0:
        return

    try:
        with open(HISTORY_FILE) as f:
            history = json.load(f)

        if history:
            history.pop()

        with open(HISTORY_FILE, "w") as f:
            json.dump(history, f, indent=4)

    except (OSError, json.JSONDecodeError) as e:
        logger.error(f"Error updating history file {HISTORY_FILE}: {e}")
