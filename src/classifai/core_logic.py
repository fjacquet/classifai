"""
Core application logic for ClassifAI.

This module contains the main orchestration logic for scanning directories,
classifying files, and preparing file operations. It is designed to be
used by both the CLI and the Streamlit UI.
"""

from pathlib import Path
from datetime import datetime

import pandas as pd
from loguru import logger

from classifai.embedding_module import cosine_similarity, get_embedding
from classifai.ollama_classification_module import (
    classify_content,
    classify_image_with_vision,
    extract_issuer,
)
from classifai.parsing_module import get_parser
from classifai.utils import detect_language


def _get_photo_destination(
    destination_dir: Path, metadata: dict, original_filename: str, language: str | None
) -> Path:
    """Constructs a destination path for photos based on EXIF data."""
    try:
        # Start with a base path including language if available
        base_path = destination_dir
        if language and language != "N/A":
            base_path = base_path / language

        # Add category
        photo_path = base_path / "Photos"

        if "date" in metadata and metadata["date"]:
            date = datetime.strptime(metadata["date"], "%Y:%m:%d %H:%M:%S")
            year = date.strftime("%Y")
            month = date.strftime("%m_%B")
            dest = photo_path / year / month
            if "location" in metadata and metadata["location"]:
                # Sanitize location to be a valid directory name
                safe_location = "".join(c for c in metadata["location"] if c.isalnum() or c in " -_,").rstrip()
                dest = dest / safe_location
            return dest / original_filename
    except (ValueError, KeyError) as e:
        logger.warning(f"Could not parse photo metadata: {e}")

    # Fallback to a generic 'Photos' directory within the language folder
    fallback_path = destination_dir
    if language and language != "N/A":
        fallback_path = fallback_path / language
    return fallback_path / "Photos" / original_filename


def process_file(
    item: Path,
    destination_dir: Path,
    classification_mode: str,
    embedding_model: str,
    rename_files: bool,
    use_vision: bool,
    language_subfolders: bool,
    logger,
    categories: list[str],
    category_embeddings: dict,
):
    """
    Processes a single file: parses, classifies, and determines the destination.
    """
    parser = get_parser(item.suffix)
    if not parser:
        logger.warning(f"No parser found for file type: {item.suffix}")
        return None

    content, metadata = parser(str(item.absolute()))
    if not content.strip():
        logger.info(f"Content for {item.name} is empty, falling back to filename for classification.")
        content = item.name

    if use_vision and item.suffix.lower() in [
        ".png",
        ".jpg",
        ".jpeg",
        ".tiff",
        ".bmp",
    ]:
        vision_content = classify_image_with_vision(str(item.absolute()), logger)
        if vision_content:
            content = vision_content

    language = detect_language(content) or "N/A"

    if classification_mode == "embedding":
        content_embedding = get_embedding(content, model=embedding_model)
        if content_embedding:
            similarities = {
                category: cosine_similarity(content_embedding, cat_embedding)
                for category, cat_embedding in category_embeddings.items()
            }
            category = max(similarities, key=similarities.get)
            new_filename = None
            issuer = extract_issuer(content, logger)
        else:
            category = "Unknown"
            new_filename = None
            issuer = None
    else:
        result = classify_content(content, categories, str(item.absolute()), logger)
        category = result.get("category", "Unknown")
        new_filename = result.get("new_filename")
        issuer = result.get("issuer")

    final_filename = new_filename if rename_files and new_filename else item.name

    # Handle photo-specific destination path
    if category == "Photos" and metadata.get("date"):
        destination_path = _get_photo_destination(
            destination_dir, metadata, final_filename, language if language_subfolders else None
        )
    else:
        # General path construction: base / language / issuer / category / filename
        destination_path = destination_dir
        if language_subfolders and language != "N/A":
            destination_path = destination_path / language

        # Sanitize issuer to be a valid directory name
        if issuer:
            safe_issuer = "".join(c for c in issuer if c.isalnum() or c in " -_").rstrip()
            destination_path = destination_path / safe_issuer
        else:
            destination_path = destination_path / "Unknown_Issuer"

        destination_path = destination_path / category
        destination_path = destination_path / final_filename

    return item, category, destination_path, language, metadata, issuer


def run_scan(
    source_dir_str: str,
    dest_dir_str: str,
    class_mode: str,
    model: str,
    rename_files: bool,
    use_vision: bool,
    language_subfolders: bool,
    recursive: bool,
):
    """
    Scans the source directory, classifies files, and returns a DataFrame.
    """
    source_path = Path(source_dir_str)
    dest_path = Path(dest_dir_str)
    results = []

    if not source_path.is_dir():
        logger.error(f"Source directory not found: {source_path}")
        return pd.DataFrame()

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

    category_embeddings = {}
    if class_mode == "embedding":
        for category in categories:
            category_embeddings[category] = get_embedding(category, model=model)

    if recursive:
        files = [f for f in source_path.rglob("*") if f.is_file()]
    else:
        files = [f for f in source_path.iterdir() if f.is_file()]

    for item in files:
        result = process_file(
            item,
            dest_path,
            class_mode,
            model,
            rename_files,
            use_vision,
            language_subfolders,
            logger,
            categories,
            category_embeddings,
        )
        if result:
            file, category, dest_path, language, metadata, issuer = result
            results.append(
                {
                    "File Name": file.name,
                    "Language": language,
                    "Category": category,
                    "Issuer": issuer,
                    "New Filename": dest_path.name,
                    "Destination Path": str(dest_path),
                    "Source Path": str(file.absolute()),
                    "Metadata": metadata,
                }
            )
    return pd.DataFrame(results)
