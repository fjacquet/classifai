"""
Core workflow orchestration for ClassifAI.

This module contains the pure functions responsible for orchestrating the
classification workflow. It coordinates the different steps of the process
while maintaining functional programming principles.
"""

from pathlib import Path

from loguru import logger
from returns.result import Failure, Result, Success

from classifai.config import app_config
from classifai.core.classification import classify_document
from classifai.core.logic import determine_final_path
from classifai.core.types import FileContext
from classifai.infrastructure.file_system import (
    get_supported_files,
    move_file_to_destination,
    read_file_content,
)
from classifai.infrastructure.llm import enrich_with_ai


def process_single_file(
    file_path: Path,
    dest_dir: Path,
    rename_files: bool = False,
    use_vision: bool = False,
    language_subfolders: bool = True,
) -> Result[FileContext, str]:
    """
    Process a single file through the classification pipeline.
    This is a pure orchestration function that coordinates the workflow.

    Args:
        file_path: Path to the file to process
        dest_dir: Destination directory for classified files
        rename_files: Whether to rename files based on AI-extracted information
        use_vision: Whether to use vision model for image classification
        language_subfolders: Whether to create language subfolders

    Returns:
        Result containing either the final FileContext or an error message
    """
    logger.info(f"Processing file: {file_path}")

    # File type validation - reject .zip files per functional specification
    if file_path.suffix.lower() == ".zip":
        error_msg = (
            f"ZIP files are not supported for direct processing: {file_path.name}. "
            "Please decompress the archive before submitting files for classification."
        )
        logger.error(error_msg)
        return Failure(error_msg)

    # Initialize context
    context = FileContext(
        source_path=file_path,
        destination_dir=dest_dir,
        rename_files=rename_files,
        use_vision=use_vision,
        language_subfolders=language_subfolders,
        categories=app_config.categories,
    )

    # Execute the pipeline
    return (
        # Read file content
        read_file_content(context)
        # Classify document
        .bind(classify_document)
        # Enrich with AI
        .bind(enrich_with_ai)
        # Determine final path
        .map(determine_final_path)
        # Move file to destination
        .bind(move_file_to_destination)
    )


def process_directory(
    source_dir: Path,
    dest_dir: Path,
    rename_files: bool = False,
    use_vision: bool = False,
    language_subfolders: bool = True,
    recursive: bool = False,
    watch: bool = False,
) -> Result[list[FileContext], str]:
    """
    Process all supported files in a directory.
    This is a pure orchestration function that coordinates the workflow.

    Args:
        source_dir: Directory containing files to process
        dest_dir: Destination directory for classified files
        rename_files: Whether to rename files based on AI-extracted information
        use_vision: Whether to use vision model for image classification
        language_subfolders: Whether to create language subfolders
        recursive: Whether to scan directories recursively
        watch: Whether to watch directory for new files

    Returns:
        Result containing either a list of processed FileContexts or an error message
    """
    logger.info(f"Processing directory: {source_dir}")

    # Get list of supported files
    files_result = get_supported_files(source_dir, recursive)

    if isinstance(files_result, Failure):
        return files_result

    files = files_result.unwrap()
    logger.info(f"Found {len(files)} supported files")

    # Process each file
    results = []
    for file_path in files:
        result = process_single_file(
            file_path=file_path,
            dest_dir=dest_dir,
            rename_files=rename_files,
            use_vision=use_vision,
            language_subfolders=language_subfolders,
        )

        if isinstance(result, Success):
            results.append(result.unwrap())
        else:
            logger.error(f"Failed to process {file_path}: {result.failure()}")

    # If watch mode is enabled, set up a watcher in a separate thread
    if watch:
        from classifai.background_watcher import start_watcher

        start_watcher(
            source_dir=source_dir,
            dest_dir=dest_dir,
            rename_files=rename_files,
            use_vision=use_vision,
            language_subfolders=language_subfolders,
            recursive=recursive,
        )

    return Success(results)
