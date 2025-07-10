"""
File operations module for ClassifAI.

This module handles moving and copying files, as well as resolving name conflicts.
"""

import shutil
from pathlib import Path

from loguru import logger


def move_file(source_path: str, destination_dir: str) -> str:
    """
    Moves a file to a destination directory, handling name conflicts.

    Args:
        source_path (str): The absolute path of the file to move.
        destination_dir (str): The absolute path of the destination directory.

    Returns:
        str: The path of the moved file, or an empty string if the move fails.
    """
    return _transfer_file(source_path, destination_dir, "move")


def copy_file(source_path: str, destination_dir: str) -> str:
    """
    Copies a file to a destination directory, handling name conflicts.

    Args:
        source_path (str): The absolute path of the file to copy.
        destination_dir (str): The absolute path of the destination directory.

    Returns:
        str: The path of the copied file, or an empty string if the copy fails.
    """
    return _transfer_file(source_path, destination_dir, "copy")


def _transfer_file(source_path: str, destination_dir: str, operation: str) -> str:
    """
    Internal function to handle both move and copy operations.

    Args:
        source_path (str): The absolute path of the file to transfer.
        destination_dir (str): The absolute path of the destination directory.
        operation (str): "move" or "copy".

    Returns:
        str: The path of the transferred file, or an empty string if the
             operation fails.
    """
    try:
        source = Path(source_path)
        destination = Path(destination_dir)

        destination.mkdir(parents=True, exist_ok=True)

        new_file_path = destination / source.name

        # Handle name conflicts
        counter = 1
        while new_file_path.exists():
            new_file_path = destination / f"{source.stem} ({counter}){source.suffix}"
            counter += 1

        if operation == "move":
            shutil.move(source, new_file_path)
            logger.info(f"Moved: {source} -> {new_file_path}")
        elif operation == "copy":
            shutil.copy2(source, new_file_path)
            logger.info(f"Copied: {source} -> {new_file_path}")

        return str(new_file_path)

    except Exception as e:
        logger.error(
            f"Error {operation}ing file {source_path} to {destination_dir}: {e}"
        )
        return ""
