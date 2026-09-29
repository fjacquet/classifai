"""
Infrastructure for file system operations.

This module contains impure functions that interact with the file system,
such as reading, parsing, and moving files.
"""

import shutil
from collections.abc import Callable
from pathlib import Path

from loguru import logger

from classifai.core.types import FileContext
from classifai.exceptions import FileOperationError, ParsingError
from classifai.infrastructure.history import log_operation
from classifai.infrastructure.parser_registry import get_parser


def read_and_parse_file(context: FileContext) -> FileContext:
    """
    Parses the file content and metadata. This is an impure step
    as it performs file I/O.

    Integrates MIME type detection and rich metadata extraction:
    - MIME type is always detected (cheap operation)
    - If early rule matched, skips full parsing (content extraction)
    - Rich metadata from ExifTool is merged with parser metadata

    Args:
        context: The file context to update with parsed content

    Returns:
        Updated FileContext with content, metadata, file_type, and mime_type

    Raises:
        ParsingError: If the file cannot be parsed
    """
    from classifai.infrastructure.metadata import (
        extract_rich_metadata,
        get_mime_type,
        merge_metadata,
    )

    # Always detect MIME type (cheap operation, useful for logging/debugging)
    mime_type = get_mime_type(context.source_path)

    # Skip full parsing if an early rule already matched
    if context.rule_match_category:
        return context.model_copy(update={"mime_type": mime_type})

    file_extension = context.source_path.suffix.lower()
    file_type = "document"
    if file_extension in [".png", ".jpg", ".jpeg", ".tiff", ".bmp"]:
        file_type = "image"

    parser: Callable | None = get_parser(file_extension)
    if not parser:
        raise ParsingError(f"No parser found for file type: {file_extension}")

    try:
        # Extract content and parser-specific metadata
        content, parser_metadata = parser(str(context.source_path.absolute()))

        # Extract rich metadata via ExifTool (gracefully degrades if unavailable)
        rich_metadata = extract_rich_metadata(context.source_path)

        # Intelligently merge metadata (non-empty wins, prefer more specific)
        merged_metadata = merge_metadata(parser_metadata, rich_metadata)

        return context.model_copy(
            update={
                "content": content,
                "metadata": merged_metadata,
                "file_type": file_type,
                "mime_type": mime_type,
            },
        )
    except Exception as e:
        raise ParsingError(f"Failed to parse {context.source_path.name}: {e}") from e


def _resolve_name_conflict(destination: Path) -> Path:
    """
    Handles name conflicts by appending a counter to the filename.

    Args:
        destination: The intended destination path

    Returns:
        A path that doesn't conflict with existing files
    """
    # Check if the destination exists
    if not destination.exists():
        return destination

    # If it exists, create a new filename with a counter
    counter = 1
    final_destination = destination.parent / f"{destination.stem} ({counter}){destination.suffix}"

    # Keep incrementing the counter until we find a non-existing filename
    while final_destination.exists():
        counter += 1
        final_destination = destination.parent / f"{destination.stem} ({counter}){destination.suffix}"

    return final_destination


def _perform_operation(source: Path, destination: Path, operation: str) -> None:
    """
    Performs the actual move or copy operation.

    Args:
        source: Source file path
        destination: Destination file path
        operation: Either "move" or "copy"

    Raises:
        FileOperationError: If the operation fails
        ValueError: If operation is invalid
    """
    try:
        if operation == "move":
            shutil.move(source, destination)
        elif operation == "copy":
            shutil.copy2(source, destination)
        else:
            raise ValueError(f"Invalid operation: {operation}")
    except (shutil.Error, OSError) as e:
        raise FileOperationError(f"Failed to {operation} file: {e}") from e


def transfer_file(context: FileContext, operation: str) -> FileContext:
    """
    Moves or copies a file, handling path creation and name conflicts.
    This is the main entrypoint for file transfer operations.

    Args:
        context: The file context with final_destination_path set
        operation: Either "move" or "copy"

    Returns:
        Updated FileContext with actual destination path

    Raises:
        FileOperationError: If the operation fails
    """
    if not context.final_destination_path:
        raise FileOperationError("Destination path not set in context.")

    destination = Path(context.final_destination_path)

    # Ensure the destination directory exists
    destination.parent.mkdir(parents=True, exist_ok=True)

    # Resolve any name conflicts
    final_dest = _resolve_name_conflict(destination)

    # Perform the file operation
    _perform_operation(context.source_path, final_dest, operation)

    # Log the operation
    try:
        log_operation(operation, str(context.source_path), str(final_dest))
    except Exception as e:
        logger.warning(f"Failed to log operation: {e}")

    # Return updated context with actual destination
    return context.model_copy(update={"final_destination_path": str(final_dest)})
