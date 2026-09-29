"""
Infrastructure for file system operations.

This module contains impure functions that interact with the file system,
such as reading, parsing, and moving files.
"""

import hashlib
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


def _sha256(path: Path) -> str:
    """Content hash of a file, read in chunks."""
    digest = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _is_same_content(source: Path, destination: Path) -> bool:
    """True if *destination* exists and holds exactly the bytes of *source*."""
    return (
        destination.is_file()
        and destination.stat().st_size == source.stat().st_size
        and _sha256(destination) == _sha256(source)
    )


def _claim_destination(destination: Path) -> Path:
    """
    Reserve a free destination name by creating it exclusively.

    Appends " (n)" to the stem until a name can be created, so two concurrent
    transfers can never pick the same file name.

    Args:
        destination: The intended destination path

    Returns:
        The reserved path (an empty placeholder file now exists there)
    """
    candidate, counter = destination, 0
    while True:
        try:
            with open(candidate, "x"):
                return candidate
        except FileExistsError:
            counter += 1
            candidate = destination.parent / f"{destination.stem} ({counter}){destination.suffix}"


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

    # Same content already filed: nothing to do (never delete the source here)
    if _is_same_content(context.source_path, destination):
        logger.info(f"Identical file already at '{destination}'; skipping {operation}.")
        return context.model_copy(update={"final_destination_path": str(destination)})

    # Reserve a non-conflicting name, then move/copy over the placeholder
    final_dest = _claim_destination(destination)
    try:
        _perform_operation(context.source_path, final_dest, operation)
    except FileOperationError:
        final_dest.unlink(missing_ok=True)
        raise

    # Log the operation
    try:
        log_operation(operation, str(context.source_path), str(final_dest))
    except Exception as e:
        logger.warning(f"Failed to log operation: {e}")

    # Return updated context with actual destination
    return context.model_copy(update={"final_destination_path": str(final_dest)})
