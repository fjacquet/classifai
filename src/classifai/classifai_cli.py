"""
CLI for ClassifAI.
"""

from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console
from rich.table import Table

from classifai.embedding_module import (
    EmbeddingModelNotFoundError,
    cosine_similarity,
    get_embedding,
)
from classifai.file_operations_module import copy_file, move_file
from classifai.logging_module import setup_logger
from classifai.ollama_classification_module import classify_content
from classifai.parsing_module import get_parser

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

    table = Table(title="Classification Preview")
    table.add_column("File Name", style="cyan")
    table.add_column("Proposed Category", style="magenta")
    table.add_column("Destination Path", style="green")

    files_to_process = []

    for item in source_dir.iterdir():
        if item.is_file():
            parser = get_parser(item.suffix)
            if parser:
                content, metadata = parser(str(item.absolute()))

                # Fallback to filename if content is empty
                if not content.strip():
                    logger.info(
                        f"Content for {item.name} is empty, falling back to filename for classification."
                    )
                    content = item.name

                if classification_mode == "embedding":
                    content_embedding = get_embedding(
                        content, model=embedding_model
                    )
                    if content_embedding:
                        similarities = {
                            category: cosine_similarity(
                                content_embedding, cat_embedding
                            )
                            for category, cat_embedding in category_embeddings.items()
                        }
                        category = max(similarities, key=similarities.get)
                    else:
                        category = "Unknown"
                else:
                    category = classify_content(content, categories, logger)

                destination_path = destination_dir / category / item.name
                table.add_row(item.name, category, str(destination_path))
                files_to_process.append((item, category, destination_path))
            else:
                logger.warning(f"No parser found for file type: {item.suffix}")

    console.print(table)

    if mode != "dry-run":
        if typer.confirm("Do you want to proceed with the file operations?"):
            for file, category, dest_path in files_to_process:
                dest_dir = dest_path.parent
                if mode == "move":
                    move_file(str(file.absolute()), str(dest_dir), metadata)
                elif mode == "copy":
                    copy_file(str(file.absolute()), str(dest_dir), metadata)
            logger.info("File operations completed.")
        else:
            logger.info("File operations cancelled.")


if __name__ == "__main__":
    app()
