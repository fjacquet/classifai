"""
Infrastructure for file system operations.

This module contains impure functions that interact with the file system,
such as reading, parsing, and moving files. It uses the `returns` library
to handle potential failures in a functional way.
"""

import shutil
from collections.abc import Callable
from pathlib import Path

from returns.result import Failure, Result, Success, safe

from classifai.core.parsing import get_parser
from classifai.core.types import FileContext
from classifai.infrastructure.history import log_operation


def read_and_parse_file(context: FileContext) -> Result[FileContext, str]:
    """
    Parses the file content and metadata. This is an impure step
    as it performs file I/O. It returns a Result container.
    """
    if context.rule_match_category:
        return Success(context)  # Skip parsing if a rule already matched

    file_extension = context.source_path.suffix.lower()
    file_type = "document"
    if file_extension in [".png", ".jpg", ".jpeg", ".tiff", ".bmp"]:
        file_type = "image"

    parser: Callable | None = get_parser(file_extension)
    if not parser:
        return Failure(f"No parser found for file type: {file_extension}")

    try:
        content, metadata = parser(str(context.source_path.absolute()))
        # Using a copy-and-update pattern for immutability
        updated_context = context.__class__(
            **{
                **context.__dict__,
                "content": content,
                "metadata": metadata,
                "file_type": file_type,
            }
        )
        return Success(updated_context)
    except Exception as e:
        return Failure(f"Failed to parse {context.source_path.name}: {e}")


@safe
def _resolve_name_conflict(destination: Path) -> Path:
    """
    Handles name conflicts by appending a counter to the filename.
    This is a pure-like helper, but marked safe due to file system access.
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


@safe
def _perform_operation(source: Path, destination: Path, operation: str) -> tuple[Path, Path]:
    """
    Performs the actual move or copy operation.
    """
    if operation == "move":
        shutil.move(source, destination)
    elif operation == "copy":
        shutil.copy2(source, destination)
    else:
        raise ValueError(f"Invalid operation: {operation}")
    return source, destination


def transfer_file(context: FileContext, operation: str) -> Result[FileContext, str]:
    """
    Moves or copies a file, handling path creation and name conflicts.
    This is the main entrypoint for file transfer operations.
    """
    if not context.final_destination_path:
        return Failure("Destination path not set in context.")

    destination = Path(context.final_destination_path)

    # Ensure the destination directory exists (impure but unlikely to fail)
    destination.parent.mkdir(parents=True, exist_ok=True)

    # Pipeline: resolve conflicts → perform operation → log → return updated context
    # First, resolve any name conflicts
    resolved_path_result = _resolve_name_conflict(destination)

    # The rest of the pipeline needs to work with the resolved path
    return (
        resolved_path_result
        # After resolving, perform the requested operation. Keep propagating `final_dest`.
        .bind(
            lambda final_dest: _perform_operation(context.source_path, final_dest, operation).map(
                lambda _: final_dest
            )
        )
        # Log the operation and keep propagating `final_dest`.
        .bind(
            lambda final_dest: safe(log_operation)(operation, str(context.source_path), str(final_dest)).map(
                lambda _: final_dest
            )
        )
        # Return a NEW context instance that reflects the actual destination
        .map(
            lambda final_dest: context.__class__(
                **{**context.__dict__, "final_destination_path": str(final_dest)}
            )
        )
        .alt(lambda err: Failure(f"File operation failed: {err}"))
    )
