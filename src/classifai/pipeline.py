"""
Main pipeline orchestration for ClassifAI.

This module orchestrates the data processing pipeline for file classification.
It coordinates functions from the `core` and `infrastructure` modules to process files.
"""

from pathlib import Path

import pandas as pd
from loguru import logger

from classifai.config import app_config
from classifai.core.logic import create_summary, determine_final_path
from classifai.core.rules import RulesEngine, apply_early_rules, apply_full_rules
from classifai.core.types import FileContext
from classifai.exceptions import ClassifAIError
from classifai.infrastructure.file_system import read_and_parse_file
from classifai.infrastructure.llm import enrich_with_ai


def _is_supported_file(path: Path) -> bool:
    """Return True for non-hidden, non-lock files with a supported extension."""
    if path.name.startswith((".", "~$")):
        return False
    suffix = path.suffix.lower()
    return suffix in app_config.supported_extensions or suffix in app_config.generic_text_extensions


def process_file_pipeline(
    file_path: Path,
    scan_config: dict,
    rules_engine: RulesEngine,
) -> FileContext | None:
    """
    Orchestrates the full processing pipeline for a single file.

    Args:
        file_path: Path to the file to process
        scan_config: Configuration dictionary for the scan
        rules_engine: The rules engine to use for classification

    Returns:
        The processed FileContext, or None if processing failed
    """
    # File type validation - reject .zip files per functional specification
    if file_path.suffix.lower() == ".zip":
        logger.error(
            f"ZIP files are not supported for direct processing: {file_path.name}. "
            "Please decompress the archive before submitting files for classification."
        )
        return None

    try:
        # Create initial context
        context = FileContext(
            source_path=file_path,
            destination_dir=Path(scan_config["dest_dir_str"]),
            rename_files=scan_config["rename_files"],
            use_vision=scan_config["use_vision"],
            language_subfolders=scan_config["language_subfolders"],
            categories=scan_config["categories"],
            ollama_model=scan_config.get("ollama_model"),
            ollama_url=scan_config.get("ollama_url"),
        )

        # Step 1: Apply early rules (filename/path only - before parsing)
        context = apply_early_rules(context, rules_engine)

        # Step 2: Parse file (includes MIME detection and metadata extraction)
        context = read_and_parse_file(context)

        # Step 3: Apply full rules (MIME/metadata - only if no early match)
        if not context.rule_match_category:
            context = apply_full_rules(context, rules_engine)

        # Step 4: AI enrichment (only if no rule match) - includes the KB sector lookup
        context = enrich_with_ai(context)

        # Step 5: Determine final path and return
        return determine_final_path(context)

    except ClassifAIError as e:
        logger.error(f"Pipeline failed for {file_path.name}: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error processing {file_path.name}: {e}")
        return None


def run_scan(
    source_dir_str: str,
    dest_dir_str: str,
    rename_files: bool,
    use_vision: bool,
    language_subfolders: bool,
    recursive: bool,
    categories: list[str],
    *,
    ollama_model: str | None = None,
    ollama_url: str | None = None,
) -> pd.DataFrame:
    """
    Scans the source directory, classifies files using the pipeline,
    and returns a DataFrame of the results.

    Args:
        source_dir_str: Path to the source directory
        dest_dir_str: Path to the destination directory
        rename_files: Whether to rename files based on content
        use_vision: Whether to use vision models for images
        language_subfolders: Whether to create language-based subfolders
        recursive: Whether to search recursively
        categories: List of valid categories
        ollama_model: Ollama completion model override (None -> configured default)
        ollama_url: Ollama API URL override (None -> configured default)

    Returns:
        DataFrame with classification results
    """
    source_path = Path(source_dir_str)
    if not source_path.is_dir():
        return pd.DataFrame()

    # Initialize rules engine once per scan, using the centralized config
    rules_engine = RulesEngine(app_config.rules)

    scan_config = {
        "dest_dir_str": dest_dir_str,
        "rename_files": rename_files,
        "use_vision": use_vision,
        "language_subfolders": language_subfolders,
        "categories": categories,
        "ollama_model": ollama_model,
        "ollama_url": ollama_url,
    }

    files = source_path.rglob("*") if recursive else source_path.iterdir()
    file_paths = [f for f in files if f.is_file() and _is_supported_file(f)]

    results = []
    for item in file_paths:
        context = process_file_pipeline(
            item,
            scan_config,
            rules_engine,
        )
        summary = create_summary(context)
        if summary is not None:
            results.append(summary)

    return pd.DataFrame(results)
