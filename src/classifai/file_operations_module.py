"""
File operations module for ClassifAI.

This module handles moving and copying files, as well as resolving name conflicts.
"""

import shutil
from datetime import datetime
from pathlib import Path

from loguru import logger


def _get_photo_destination(destination_dir: Path, metadata: dict, original_filename: str) -> Path:
    """Constructs a destination path for photos based on EXIF data."""
    try:
        if "date" in metadata and metadata["date"]:
            date = datetime.strptime(metadata["date"], "%Y:%m:%d %H:%M:%S")
            year = date.strftime("%Y")
            month = date.strftime("%m_%B")
            dest = destination_dir / "Photos" / year / month
            if "location" in metadata and metadata["location"]:
                dest = dest / metadata["location"]
            return dest / original_filename
    except (ValueError, KeyError) as e:
        logger.warning(f"Could not parse photo metadata: {e}")
    # Fallback to a generic 'Photos' directory
    return destination_dir / "Photos" / original_filename


def move_file(source_path: str, destination_dir: str, metadata: dict = None) -> str:
    """
    Moves a file to a destination directory, handling name conflicts.
    """
    return _transfer_file(source_path, destination_dir, "move", metadata)


def copy_file(source_path: str, destination_dir: str, metadata: dict = None) -> str:
    """
    Copies a file to a destination directory, handling name conflicts.
    """
    return _transfer_file(source_path, destination_dir, "copy", metadata)


def _transfer_file(source_path: str, destination_dir: str, operation: str, metadata: dict = None) -> str:
    """
    Internal function to handle both move and copy operations.
    """
    try:
        source = Path(source_path)
        destination = Path(destination_dir)

        if metadata and source.suffix.lower() in [".jpg", ".jpeg", ".png", ".tiff"]:
            new_file_path = _get_photo_destination(destination, metadata, source.name)
            destination = new_file_path.parent
        else:
            new_file_path = destination / source.name

        destination.mkdir(parents=True, exist_ok=True)

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
        logger.error(f"Error {operation}ing file {source_path} to {destination_dir}: {e}")
        return ""
