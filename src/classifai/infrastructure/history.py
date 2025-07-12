"""
Infrastructure for history operations.

This module contains impure functions for interacting with the history file.
"""

import json
from pathlib import Path

from returns.maybe import Maybe, Nothing, Some
from returns.result import safe

HISTORY_FILE = Path("logs/history.json")


@safe
def log_operation(operation: str, source_path: str, dest_path: str) -> None:
    """
    Logs a file operation to the history file.
    """
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


@safe
def get_last_operation() -> Maybe[dict]:
    """
    Retrieves the last operation from the history file as a Maybe.
    """
    if not HISTORY_FILE.exists() or HISTORY_FILE.stat().st_size == 0:
        # Always return an *instance* of `Nothing` so that `isinstance(..., Nothing)`
        # works regardless of whether ``Nothing`` is a class (after our monkey patch)
        # or a singleton instance (stock behaviour).
        try:
            return Nothing() if callable(Nothing) else Nothing  # type: ignore[misc]
        except TypeError:
            # If `Nothing` is a singleton instance, fall back to returning it directly.
            return Nothing

    with open(HISTORY_FILE) as f:
        history = json.load(f)

    if not history:
        try:
            return Nothing() if callable(Nothing) else Nothing  # type: ignore[misc]
        except TypeError:
            return Nothing
    return Some(history[-1])


@safe
def remove_last_operation() -> None:
    """
    Removes the last operation from the history file.
    """
    if not HISTORY_FILE.exists() or HISTORY_FILE.stat().st_size == 0:
        return

    with open(HISTORY_FILE) as f:
        history = json.load(f)

    if history:
        history.pop()

    with open(HISTORY_FILE, "w") as f:
        json.dump(history, f, indent=4)
