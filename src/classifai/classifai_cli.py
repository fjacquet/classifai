"""
CLI for ClassifAI.
"""

import shutil
from pathlib import Path
from typing import Annotated

import typer
import yaml
from rich.console import Console
from rich.table import Table

from classifai.background_watcher import start_watcher
from classifai.config import app_config, load_app_config
from classifai.defaults import (
    DEFAULT_LANGUAGE_SUBFOLDERS,
    DEFAULT_LOG_FILE,
    DEFAULT_QUIET_LLM,
    DEFAULT_RECURSIVE,
    DEFAULT_RENAME_FILES,
    DEFAULT_VERBOSE,
)
from classifai.entrypoint_utils import generate_file_operations, perform_operations
from classifai.infrastructure.history import get_last_operation, remove_last_operation
from classifai.localization import Language, get_text, set_language
from classifai.logging_module import setup_logger
from classifai.pipeline import run_scan
from classifai.validation import validate_rules_against_categories

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
    ollama_model: Annotated[
        str,
        typer.Option(
            "--ollama-model",
            "-ai",
            help="Name of the Ollama model to use.",
        ),
    ] = app_config.ollama_model_name,
    ollama_url: Annotated[
        str,
        typer.Option(
            "--ollama-url",
            "-url",
            help="URL of the Ollama API.",
        ),
    ] = app_config.ollama_api_url,
    rename_files: Annotated[
        bool,
        typer.Option(
            "--rename-files",
            "-r",
            help="Enable AI-powered file renaming.",
        ),
    ] = DEFAULT_RENAME_FILES,
    use_vision: Annotated[
        bool,
        typer.Option(
            "--use-vision",
            "-uv",
            help="Use vision model for image classification.",
        ),
    ] = app_config.use_vision_model,
    language_subfolders: Annotated[
        bool,
        typer.Option(
            "--language-subfolders",
            "-ls",
            help="Create language-based subfolders (e.g., /en, /fr).",
        ),
    ] = DEFAULT_LANGUAGE_SUBFOLDERS,
    recursive: Annotated[
        bool,
        typer.Option(
            "--recursive",
            "-R",
            help="Scan subdirectories recursively.",
        ),
    ] = DEFAULT_RECURSIVE,
    verbose: Annotated[
        bool, typer.Option("--verbose", "-v", help="Enable verbose output.")
    ] = DEFAULT_VERBOSE,
    quiet_llm: Annotated[
        bool,
        typer.Option(
            "--quiet-llm", "-ql", help="Suppress DEBUG logs from LLM module (useful with --verbose)."
        ),
    ] = DEFAULT_QUIET_LLM,
    log_file: Annotated[
        Path, typer.Option("--log-file", help="Path to save the log file.")
    ] = DEFAULT_LOG_FILE,
):
    """
    Organize files in a directory using an Ollama language model.
    """
    # Create log directory if it doesn't exist
    if log_file:
        log_file.parent.mkdir(parents=True, exist_ok=True)

    log_level = "DEBUG" if verbose else "INFO"
    quiet_modules = ["classifai.infrastructure.llm"] if quiet_llm else []
    logger = setup_logger(log_level, log_file, quiet_modules=quiet_modules)

    if destination_dir is None:
        destination_dir = source_dir

    # Set language to French
    set_language(Language.FR)

    logger.info(get_text("starting_classifai", mode=mode))
    logger.info(get_text("source_directory", source_dir=source_dir))
    logger.info(get_text("destination_directory", destination_dir=destination_dir))
    logger.info(get_text("ollama_model", model=ollama_model))

    table = Table(title=get_text("classification_preview"), show_header=True, header_style="bold magenta")
    table.add_column(get_text("file_name"), style="cyan")
    table.add_column(get_text("language"), style="yellow")
    table.add_column(get_text("category"), style="magenta")
    table.add_column(get_text("issuer"), style="blue")
    table.add_column(get_text("new_filename"), style="blue")
    table.add_column(get_text("destination_path"), style="green")

    # Load and validate configuration
    app_config = load_app_config()
    validate_rules_against_categories(app_config.rules, app_config.categories)

    results_df = run_scan(
        str(source_dir),
        str(destination_dir),
        rename_files,
        use_vision,
        language_subfolders,
        recursive,
        app_config.categories,
    )

    ops = generate_file_operations(results_df)
    for _, row in results_df.iterrows():
        table.add_row(
            row["File Name"],
            row["Language"],
            row["Category"],
            row["Issuer"],
            row["New Filename"],
            row["Destination Path"],
        )

    console.print(table)

    if mode != "dry-run":
        if typer.confirm("Do you want to proceed with the file operations?"):

            def _progress_cb(done: int, total: int, file_name: str):  # noqa: D401
                console.status(f"{mode.capitalize()}ing {file_name} ({done}/{total})")

            processed = perform_operations(ops, mode, progress_cb=_progress_cb)
            logger.info(f"File operations completed. {processed}/{len(ops)} succeeded.")
        else:
            logger.info("File operations cancelled.")


@app.command()
def undo():
    """
    Undoes the last file operation.
    """
    last_op = get_last_operation()

    if last_op is None:
        console.print(get_text("no_history_found"))
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
        console.print(get_text("undo_successful"))

    except FileNotFoundError:
        console.print(f"[bold red]Error: File not found at '{dest}'. Cannot undo.[/bold red]")
        if typer.confirm(get_text("remove_from_history")):
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
    **kwargs,
):
    """
    Watches a directory for new files and organizes them automatically.
    """
    start_watcher(source_dir, destination_dir, mode, **kwargs)


@app.command(name="kb-list-unknown")
def list_unknown_issuers(
    config_file: Annotated[
        Path,
        typer.Option(
            "--file",
            "-f",
            help="Path to the unknown issuers file.",
        ),
    ] = Path("config/unknown_issuers.yaml"),
):
    """
    Lists all the issuers that were not found in the knowledge base.
    """
    if not config_file.exists():
        console.print(f"[bold yellow]Unknown issuers file not found at '{config_file}'.[/bold yellow]")
        raise typer.Exit()

    with open(config_file) as f:
        try:
            unknown_issuers = yaml.safe_load(f)
        except yaml.YAMLError as e:
            console.print(f"[bold red]Error reading YAML file: {e}[/bold red]")
            raise typer.Exit(code=1) from e

    if not unknown_issuers:
        console.print("[bold green]No unknown issuers found.[/bold green]")
        raise typer.Exit()

    table = Table(title="Unknown Issuers", show_header=True, header_style="bold magenta")
    table.add_column("Issuer", style="cyan")
    table.add_column("AI-Suggested Sector", style="yellow")

    for entry in unknown_issuers:
        table.add_row(entry.get("issuer", "N/A"), entry.get("sector", "N/A"))

    console.print(table)


if __name__ == "__main__":
    app()
