"""
Core application logic for ClassifAI.

This module contains the main orchestration logic for scanning directories,
classifying files, and preparing file operations. It is designed to be
used by both the CLI and the Streamlit UI.
"""

from datetime import datetime
from pathlib import Path

import pandas as pd
from loguru import logger

from classifai.embedding_module import cosine_similarity, get_embedding
from classifai.knowledge_base_module import KnowledgeBase
from classifai.ollama_classification_module import (
    classify_content,
    classify_image_with_vision,
    extract_issuer_with_ai,
    get_sector_with_ai,
)
from classifai.parsing_module import get_parser
from classifai.rules_engine_module import RulesEngine
from classifai.utils import detect_language

# Initialize engines
rules_engine = RulesEngine()
knowledge_base = KnowledgeBase()


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
                safe_location = "".join(
                    c for c in metadata["location"] if c.isalnum() or c in " -_,"
                ).rstrip()
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
    # 1. Rule-based pre-classification
    rule_category = rules_engine.match_category(str(item.absolute()))
    if rule_category:
        logger.info(f"Matched rule for {item.name}: Category '{rule_category}'")
        # If a rule matches, we might not have issuer/sector info, so we use defaults
        destination_path = destination_dir
        if language_subfolders:
            destination_path = destination_path / "N/A"
        destination_path = destination_path / "Unknown_Sector" / "Unknown_Issuer" / rule_category / item.name
        return item, rule_category, destination_path, "N/A", {}, "Unknown_Issuer"

    # 2. Parsing
    parser = get_parser(item.suffix)
    if not parser:
        logger.warning(f"No parser found for file type: {item.suffix}")
        return None

    content, metadata = parser(str(item.absolute()))
    if not content.strip():
        logger.info(f"Content for {item.name} is empty, falling back to filename for classification.")
        content = item.name

    if use_vision and item.suffix.lower() in [".png", ".jpg", ".jpeg", ".tiff", ".bmp"]:
        vision_content = classify_image_with_vision(str(item.absolute()), logger)
        if vision_content:
            content = vision_content

    language = detect_language(content) or "N/A"
    logger.info(f"Detected language for {item.name}: {language}")

    # 3. Keyword-based category matching
    category = None
    new_filename = None
    issuer = None

    # 4. AI-based classification if no keyword match
    if not category:
        if classification_mode == "embedding":
            content_embedding = get_embedding(content, model=embedding_model)
            if content_embedding:
                similarities = {
                    cat: cosine_similarity(content_embedding, cat_embedding)
                    for cat, cat_embedding in category_embeddings.items()
                }
                category = max(similarities, key=similarities.get)
            else:
                category = "Non Classé"
        else:  # completion mode
            result = classify_content(content, categories, str(item.absolute()), logger)
            category = result.get("category", "Non Classé")
            new_filename = result.get("new_filename")
            issuer = result.get("issuer")

    # 5. Issuer extraction (if not already extracted)
    if not issuer:
        issuer = extract_issuer_with_ai(content, logger)

    # 6. Knowledge Base Enrichment (Sector lookup)
    sector = knowledge_base.get_sector_for_issuer(issuer) if issuer else None
    if not sector and issuer:
        logger.info(f"Issuer '{issuer}' not found in knowledge base. Asking AI for sector.")
        sector = get_sector_with_ai(issuer, content, logger)

    if not sector:
        sector = "Secteur_Inconnu"

    # 7. Final Path Construction
    if rename_files and new_filename:
        # Sanitize AI-generated filename
        final_filename = "".join(c for c in new_filename if c.isalnum() or c in " -_.").rstrip()
        if not final_filename.endswith(item.suffix):
            final_filename += item.suffix
    else:
        final_filename = item.name

    if category == "Photos" and metadata.get("date"):
        destination_path = _get_photo_destination(
            destination_dir, metadata, final_filename, language if language_subfolders else None
        )
    else:
        # Build the path component by component for clarity and correctness
        current_path = destination_dir
        if language_subfolders and language != "N/A":
            current_path = current_path / language

        current_path = current_path / sector

        if issuer:
            safe_issuer = "".join(c for c in issuer if c.isalnum() or c in " -_").rstrip()
            current_path = current_path / safe_issuer
        else:
            current_path = current_path / "Unknown_Issuer"

        current_path = current_path / category
        destination_path = current_path / final_filename

    logger.info(f"Final destination for {item.name}: {destination_path}")
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
    categories: list[str],
):
    """
    Scans the source directory, classifies files, and returns a DataFrame.
    """
    source_path = Path(source_dir_str)
    destination_directory = Path(dest_dir_str)  # Renamed for clarity
    results = []

    if not source_path.is_dir():
        logger.error(f"Source directory not found: {source_path}")
        return pd.DataFrame()

    category_embeddings = {}
    if class_mode == "embedding":
        logger.info(f"Generating embeddings for {len(categories)} categories...")
        for category in categories:
            category_embeddings[category] = get_embedding(category, model=model)
        logger.info("Embeddings generated.")

    if recursive:
        files = [f for f in source_path.rglob("*") if f.is_file()]
    else:
        files = [f for f in source_path.iterdir() if f.is_file()]

    for item in files:
        result = process_file(
            item,
            destination_directory,  # Pass the base destination directory
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
            file, category, final_dest_path, language, metadata, issuer = result
            results.append(
                {
                    "File Name": file.name,
                    "Language": language,
                    "Category": category,
                    "Issuer": issuer,
                    "New Filename": final_dest_path.name,
                    "Destination Path": str(final_dest_path),
                    "Source Path": str(file.absolute()),
                    "Metadata": metadata,
                }
            )
    return pd.DataFrame(results)
