"""Entry-point helper utilities shared by the CLI and Streamlit UI.

This module centralises the logic that was previously duplicated between
`classifai_cli.py` and `classifai_app.py` so that the two front-ends only
handle user-interaction concerns (collecting input, displaying a preview
and progress bars).

Functions provided
------------------
build_scan_config(...):
    Normalise / validate raw parameters coming from any UI and returns a
    simple `dict` (or `ScanConfig` dataclass) that can be directly fed to
    `core_logic.run_scan()`.

generate_file_operations(results_df):
    Transform the DataFrame returned by `run_scan()` into an iterable of
    `(source_path, destination_path)` tuples.

perform_operations(ops, operation, progress_cb=None):
    Execute a *move* or *copy* operation for each tuple in *ops* using the
    existing helpers in `infrastructure.file_system`.  A *progress_cb* can be
    supplied to provide UI-specific feedback (e.g. Streamlit progress bar
    update or Rich console progress).
"""

from __future__ import annotations

from collections.abc import Callable, Iterable
from dataclasses import dataclass
from pathlib import Path

import pandas as pd
from returns.result import Success

from classifai.core.types import FileContext
from classifai.infrastructure.file_system import transfer_file

__all__ = [
    "ScanConfig",
    "build_scan_config",
    "generate_file_operations",
    "perform_operations",
]


@dataclass(slots=True)
class ScanConfig:
    """Container for arguments passed to :pyfunc:`core_logic.run_scan`."""

    source_dir: Path
    destination_dir: Path
    rename_files: bool = False
    use_vision: bool = False
    language_subfolders: bool = False
    recursive: bool = False
    categories: list[str] | None = None

    def to_tuple(self) -> tuple:
        """Return the arguments in the order expected by *run_scan*."""

        return (
            str(self.source_dir),
            str(self.destination_dir),
            self.rename_files,
            self.use_vision,
            self.language_subfolders,
            self.recursive,
            self.categories or [],
        )


# ---------------------------------------------------------------------------
# Builders
# ---------------------------------------------------------------------------


def build_scan_config(
    *,
    source_dir: str | Path,
    destination_dir: str | Path,
    rename_files: bool = False,
    use_vision: bool = False,
    language_subfolders: bool = False,
    recursive: bool = False,
    categories: list[str] | None = None,
) -> ScanConfig:
    """Validate & wrap UI parameters into a :class:`ScanConfig`."""

    src = Path(source_dir).expanduser().resolve()
    dest = Path(destination_dir).expanduser().resolve()

    if not src.exists() or not src.is_dir():
        raise ValueError(f"source_dir does not exist or is not a directory: {src}")

    # Destination dir may not exist yet – no strict validation.

    return ScanConfig(
        source_dir=src,
        destination_dir=dest,
        rename_files=rename_files,
        use_vision=use_vision,
        language_subfolders=language_subfolders,
        recursive=recursive,
        categories=categories,
    )


# ---------------------------------------------------------------------------
# DataFrame helpers
# ---------------------------------------------------------------------------


def generate_file_operations(results_df: pd.DataFrame) -> list[dict]:
    """Return a list of dictionaries with source, destination, and context."""

    # Import logger from logging_module
    from classifai.logging_module import logger

    # If the DataFrame is empty, return an empty list of operations
    if results_df.empty:
        logger.info("No files were processed successfully. Returning empty operations list.")
        return []

    required_cols = {"Source Path", "Destination Path"}
    missing = required_cols - set(results_df.columns)
    if missing:
        raise KeyError(f"Missing columns in results_df: {', '.join(missing)}")

    ops = []
    for _, row in results_df.iterrows():
        context = FileContext(
            source_path=Path(row["Source Path"]),
            destination_dir=Path(row["Destination Path"]).parent.parent,
            rename_files=row["New Filename"] != row["File Name"],
            use_vision=False,  # This is not available in the context of perform_operations
            language_subfolders=False,  # This is not available in the context of perform_operations
            categories=[],  # This is not available in the context of perform_operations
            final_destination_path=Path(row["Destination Path"]),
        )
        ops.append(
            {
                "source": row["Source Path"],
                "destination": row["Destination Path"],
                "context": context,
            },
        )
    return ops


# ---------------------------------------------------------------------------
# Operations
# ---------------------------------------------------------------------------


def perform_operations(
    ops: Iterable[dict],
    operation: str,
    *,
    progress_cb: Callable[[int, int, str], None] | None = None,
) -> int:
    """Execute *move* or *copy* on each (src, dest) pair.

    Parameters
    ----------
    ops
        Iterable of dictionaries with source, destination, and context.
    operation
        Either "move" or "copy".
    progress_cb
        Optional callback ``(index, total, file_name) -> None`` that gets
        invoked after each successful operation.

    Returns
    -------
    int
        Number of files successfully processed.
    """

    if operation not in {"move", "copy"}:
        raise ValueError("operation must be 'move' or 'copy'")

    total = len(list(ops)) if not isinstance(ops, list) else len(ops)
    success_count = 0

    for i, op in enumerate(ops):
        result = transfer_file(op["context"], operation)
        if isinstance(result, Success):
            success_count += 1
        if progress_cb is not None:
            progress_cb(i + 1, total, Path(op["source"]).name)

    return success_count
