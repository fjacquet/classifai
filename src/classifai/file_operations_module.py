"""
File operations module for ClassifAI.

This module handles moving and copying files, as well as resolving name conflicts.
"""

import shutil
from datetime import datetime
from pathlib import Path

from loguru import logger

from classifai.history_module import log_operation


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


def move_file(
    source_path: str,
    destination_dir: str,
    metadata: dict = None,
    language: str = None,
    new_filename: str = None,
    issuer: str = None,
) -> str:
    """
    Moves a file to a destination directory, handling name conflicts.
    """
    return _transfer_file(
        source_path,
        destination_dir,
        "move",
        metadata,
        language,
        new_filename,
        issuer,
    )


def copy_file(
    source_path: str,
    destination_dir: str,
    metadata: dict = None,
    language: str = None,
    new_filename: str = None,
    issuer: str = None,
) -> str:
    """
    Copies a file to a destination directory, handling name conflicts.
    """
    return _transfer_file(
        source_path,
        destination_dir,
        "copy",
        metadata,
        language,
        new_filename,
        issuer,
    )


def _transfer_file(
    source_path: str,
    destination_dir: str,
    operation: str,
    metadata: dict = None,
    language: str = None,
    new_filename: str = None,
    issuer: str = None,
) -> str:
    """
    Internal function to handle both move and copy operations.
    """
    try:
        source = Path(source_path)
        destination = Path(destination_dir)
        filename = new_filename or source.name

        if metadata and source.suffix.lower() in [".jpg", ".jpeg", ".png", ".tiff"]:
            # Photo-specific logic remains the same
            new_file_path = _get_photo_destination(destination, metadata, filename)
            destination_folder = new_file_path.parent
        else:
            # General path construction
            destination_folder = destination
            if issuer:
                destination_folder = destination_folder / issuer
            else:
                destination_folder = destination_folder / "Unknown_Issuer"

            if language and language != "N/A":
                destination_folder = destination_folder / language

            new_file_path = destination_folder / filename

        destination_folder.mkdir(parents=True, exist_ok=True)

        # Handle name conflicts
        counter = 1
        stem = new_file_path.stem
        suffix = new_file_path.suffix

        # Check if a file with the same name already exists in the destination
        if new_file_path.exists():
            # If it exists, start the counter to find a new name
            while new_file_path.exists():
                new_file_path = destination_folder / f"{stem} ({counter}){suffix}"
                counter += 1

        if operation == "move":
            shutil.move(source, new_file_path)
            logger.info(f"Moved: {source} -> {new_file_path}")
        elif operation == "copy":
            shutil.copy2(source, new_file_path)
            logger.info(f"Copied: {source} -> {new_file_path}")

        log_operation(operation, str(source), str(new_file_path))

        return str(new_file_path)

    except Exception as e:
        logger.error(f"Error {operation}ing file {source_path} to {destination_dir}: {e}")
        return ""
