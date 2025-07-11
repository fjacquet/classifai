"""
File operations module for ClassifAI.

This module handles moving and copying files, as well as resolving name conflicts.
"""

import shutil
from pathlib import Path

from loguru import logger

from classifai.history_module import log_operation


def move_file(source_path: str, destination_path: str) -> str:
    """
    Moves a file to a destination path, handling name conflicts.
    """
    return _transfer_file(source_path, destination_path, "move")


def copy_file(source_path: str, destination_path: str) -> str:
    """
    Copies a file to a destination path, handling name conflicts.
    """
    return _transfer_file(source_path, destination_path, "copy")


def _transfer_file(source_path: str, destination_path: str, operation: str) -> str:
    """
    Internal function to handle both move and copy operations.
    It creates the destination directory and resolves name conflicts.
    """
    try:
        source = Path(source_path)
        destination = Path(destination_path)

        # Create the destination folder if it doesn't exist
        destination.parent.mkdir(parents=True, exist_ok=True)

        # Handle name conflicts by appending a counter
        counter = 1
        final_destination = destination
        while final_destination.exists():
            final_destination = destination.parent / f"{destination.stem} ({counter}){destination.suffix}"
            counter += 1

        if operation == "move":
            shutil.move(source, final_destination)
            logger.info(f"Moved: {source} -> {final_destination}")
        elif operation == "copy":
            shutil.copy2(source, final_destination)
            logger.info(f"Copied: {source} -> {final_destination}")

        log_operation(operation, str(source), str(final_destination))

        return str(final_destination)

    except Exception as e:
        logger.error(f"Error {operation}ing file {source_path} to {destination_path}: {e}")
        return ""
