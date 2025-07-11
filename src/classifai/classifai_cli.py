"""
CLI for ClassifAI.
"""

import shutil
from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console
from rich.table import Table

from classifai.background_watcher import start_watcher
from classifai.config import USE_VISION_MODEL
from classifai.core_logic import run_scan
from classifai.embedding_module import (
    EmbeddingModelNotFoundError,
    get_embedding,
)
from classifai.file_operations_module import copy_file, move_file
from classifai.history_module import get_last_operation, remove_last_operation
from classifai.logging_module import setup_logger

app = typer.Typer()
console = Console()


@app.command()
def run(
    source_dir: Annotated[
        Path,
        typer.Option(
            ...,
            "--source-dir",
            "-s",
            help="Path to the directory to organize.",
        ),
    ],
    destination_dir: Annotated[
        Path,
        typer.Option(
            "--destination-dir",
            "-d",
            help="Path to the destination directory.",
        ),
    ] = None,
    mode: Annotated[
        str,
        typer.Option(
            "--mode",
            "-m",
            help="Mode of operation: dry-run, move, or copy.",
        ),
    ] = "dry-run",
    classification_mode: Annotated[
        str,
        typer.Option(
            "--classification-mode",
            "-cm",
            help="Classification mode: completion or embedding.",
        ),
    ] = "completion",
    embedding_model: Annotated[
        str,
        typer.Option(
            "--embedding-model",
            "-em",
            help="Name of the Ollama embedding model to use.",
        ),
    ] = None,
    ollama_model: Annotated[
        str,
        typer.Option(
            "--ollama-model",
            "-ai",
            help="Name of the Ollama model to use.",
        ),
    ] = "gemma3n",
    ollama_url: Annotated[
        str,
        typer.Option(
            "--ollama-url",
            "-url",
            help="URL of the Ollama API.",
        ),
    ] = "http://localhost:11434",
    rename_files: Annotated[
        bool,
        typer.Option(
            "--rename-files",
            "-r",
            help="Enable AI-powered file renaming.",
        ),
    ] = False,
    use_vision: Annotated[
        bool,
        typer.Option(
            "--use-vision",
            "-uv",
            help="Use vision model for image classification.",
        ),
    ] = USE_VISION_MODEL,
    language_subfolders: Annotated[
        bool,
        typer.Option(
            "--language-subfolders",
            "-ls",
            help="Create language-based subfolders (e.g., /en, /fr).",
        ),
    ] = False,
    recursive: Annotated[
        bool,
        typer.Option(
            "--recursive",
            "-R",
            help="Scan subdirectories recursively.",
        ),
    ] = False,
    verbose: Annotated[bool, typer.Option("--verbose", "-v", help="Enable verbose output.")] = False,
    log_file: Annotated[Path, typer.Option("--log-file", help="Path to save the log file.")] = Path(
        "logs/main.log"
    ),
):
    """
    Organize files in a directory using an Ollama language model.
    """
    # Create log directory if it doesn't exist
    if log_file:
        log_file.parent.mkdir(parents=True, exist_ok=True)

    log_level = "DEBUG" if verbose else "INFO"
    logger = setup_logger(log_level, log_file)

    if destination_dir is None:
        destination_dir = source_dir

    logger.info(f"Starting ClassifAI in {mode} mode.")
    logger.info(f"Source directory: {source_dir}")
    logger.info(f"Destination directory: {destination_dir}")
    logger.info(f"Ollama model: {ollama_model}")
    logger.info(f"Classification mode: {classification_mode}")

    # Default categories for now, will be configurable later
    categories = [
        "Documents",
        "Images",
        "Videos",
        "Audio",
        "Archives",
        "Scripts",
        "Misc",
    ]

    try:
        category_embeddings = {}
        if classification_mode == "embedding":
            for category in categories:
                category_embeddings[category] = get_embedding(category, model=embedding_model)
    except EmbeddingModelNotFoundError as e:
        console.print(f"[bold red]Error:[/bold red] {e}")
        raise typer.Exit(code=1)

    table = Table(title="Classification Preview", expand=True)
    table.add_column("File Name", style="cyan", width=30)
    table.add_column("Language", style="yellow", width=10)
    table.add_column("Category", style="magenta", width=20)
    table.add_column("Issuer", style="blue", width=20)
    table.add_column("New Filename", style="blue", width=30)
    table.add_column("Destination Path", style="green")

    results_df = run_scan(
        source_dir,
        destination_dir,
        classification_mode,
        embedding_model,
        rename_files,
        use_vision,
        language_subfolders,
        recursive,
    )

    files_to_process = []
    for _, row in results_df.iterrows():
        table.add_row(
            row["File Name"],
            row["Language"],
            row["Category"],
            row["Issuer"],
            row["New Filename"],
            row["Destination Path"],
        )
        files_to_process.append(
            (
                Path(row["Source Path"]),
                row["Category"],
                Path(row["Destination Path"]),
                row["Language"],
                row["Metadata"],
                row["Issuer"],
            )
        )

    console.print(table)

    if mode != "dry-run":
        if typer.confirm("Do you want to proceed with the file operations?"):
            for file, category, dest_path, lang, meta, issuer in files_to_process:
                if mode == "move":
                    move_file(str(file.absolute()), str(dest_path))
                elif mode == "copy":
                    copy_file(str(file.absolute()), str(dest_path))
            logger.info("File operations completed.")
        else:
            logger.info("File operations cancelled.")


@app.command()
def undo():
    """
    Undoes the last file operation.
    """
    last_op = get_last_operation()
    if not last_op:
        console.print("[bold yellow]No history found. Nothing to undo.[/bold yellow]")
        raise typer.Exit()

    op_type = last_op["operation"]
    source = last_op["source"]
    dest = last_op["destination"]

    console.print(f"Last operation: {op_type} '{source}' to '{dest}'")
    if not typer.confirm("Do you want to undo this operation?"):
        raise typer.Exit()

    try:
        if op_type == "move":
            # Move the file back to its original location
            original_path = Path(source)
            shutil.move(dest, original_path)
            console.print(f"[green]Moved '{dest}' back to '{original_path}'[/green]")
        elif op_type == "copy":
            # Delete the copied file
            Path(dest).unlink()
            console.print(f"[green]Deleted copied file '{dest}'[/green]")

        remove_last_operation()
        console.print("[bold green]Undo successful.[/bold green]")

    except FileNotFoundError:
        console.print(f"[bold red]Error: File not found at '{dest}'. Cannot undo.[/bold red]")
        if typer.confirm("Remove this entry from history?"):
            remove_last_operation()
    except Exception as e:
        console.print(f"[bold red]An error occurred during undo: {e}[/bold red]")


@app.command()
def watch(
    source_dir: Annotated[
        Path,
        typer.Option(
            ...,
            "--source-dir",
            "-s",
            help="Path to the directory to watch.",
        ),
    ],
    destination_dir: Annotated[
        Path,
        typer.Option(
            "--destination-dir",
            "-d",
            help="Path to the destination directory.",
        ),
    ],
    mode: Annotated[
        str,
        typer.Option(
            "--mode",
            "-m",
            help="Mode of operation: move or copy.",
        ),
    ] = "move",
    classification_mode: Annotated[
        str,
        typer.Option(
            "--classification-mode",
            "-cm",
            help="Classification mode: completion or embedding.",
        ),
    ] = "completion",
    **kwargs,
):
    """
    Watches a directory for new files and organizes them automatically.
    """
    start_watcher(source_dir, destination_dir, mode, classification_mode, **kwargs)


if __name__ == "__main__":
    app()
