"""
Command-line interface for ClassifAI.

This module provides the CLI interface for ClassifAI using Typer.
It handles command-line arguments, options, and executes the appropriate
core functionality.
"""

from pathlib import Path

import typer
from loguru import logger
from returns.result import Success

from classifai.core.workflow import process_directory, process_single_file
from classifai.logging_module import setup_logging

# Create Typer app
app = typer.Typer(
    name="classifai",
    help="Classify and organize your files with local AI models.",
    add_completion=False,
)


@app.command()
def scan(
    source_dir: Path = typer.Argument(  # noqa: B008 - Typer CLI argument pattern
        ...,
        help="Directory containing files to classify",
        exists=True,
        dir_okay=True,
        file_okay=False,
    ),
    dest_dir: Path = typer.Argument(  # noqa: B008 - Typer CLI argument pattern
        ...,
        help="Destination directory for classified files",
        exists=True,
        dir_okay=True,
        file_okay=False,
    ),
    rename: bool = typer.Option(
        False,
        "--rename",
        "-r",
        help="Rename files based on AI-extracted information",
    ),
    use_vision: bool = typer.Option(
        False,
        "--vision",
        "-v",
        help="Use vision model for image classification",
    ),
    language_subfolders: bool = typer.Option(
        True,
        "--lang-folders/--no-lang-folders",
        help="Create language subfolders",
    ),
    recursive: bool = typer.Option(False, "--recursive", "-R", help="Scan directories recursively"),
    watch: bool = typer.Option(False, "--watch", "-w", help="Watch directory for new files"),
):
    """
    Scan a directory and classify files according to their content.
    """
    setup_logging()
    logger.info(f"Starting ClassifAI scan of {source_dir}")

    # Process the directory
    result = process_directory(
        source_dir=source_dir,
        dest_dir=dest_dir,
        rename_files=rename,
        use_vision=use_vision,
        language_subfolders=language_subfolders,
        recursive=recursive,
        watch=watch,
    )

    if isinstance(result, Success):
        logger.info("Scan completed successfully")
        return 0
    error = result.failure()
    logger.error(f"Scan failed: {error}")
    return 1


@app.command()
def classify(
    file_path: Path = typer.Argument(  # noqa: B008 - Typer CLI argument pattern
        ...,
        help="File to classify",
        exists=True,
        dir_okay=False,
        file_okay=True,
    ),
    dest_dir: Path = typer.Argument(  # noqa: B008 - Typer CLI argument pattern
        ...,
        help="Destination directory for classified file",
        exists=True,
        dir_okay=True,
        file_okay=False,
    ),
    rename: bool = typer.Option(
        False,
        "--rename",
        "-r",
        help="Rename file based on AI-extracted information",
    ),
    use_vision: bool = typer.Option(
        False,
        "--vision",
        "-v",
        help="Use vision model for image classification",
    ),
    language_subfolders: bool = typer.Option(
        True,
        "--lang-folders/--no-lang-folders",
        help="Create language subfolders",
    ),
):
    """
    Classify a single file according to its content.
    """
    setup_logging()
    logger.info(f"Classifying file: {file_path}")

    # Process the file
    result = process_single_file(
        file_path=file_path,
        dest_dir=dest_dir,
        rename_files=rename,
        use_vision=use_vision,
        language_subfolders=language_subfolders,
    )

    if isinstance(result, Success):
        logger.info("Classification completed successfully")
        return 0
    error = result.failure()
    logger.error(f"Classification failed: {error}")
    return 1


@app.command()
def version():
    """
    Show the version of ClassifAI.
    """
    from classifai import __version__

    typer.echo(f"ClassifAI version: {__version__}")
    return 0


if __name__ == "__main__":
    app()
