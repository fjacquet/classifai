"""
Knowledge base infrastructure for ClassifAI.

This module provides functions for accessing and managing the knowledge base,
which includes categories, sector-issuer mappings, and other reference data.
"""

import re
from datetime import datetime
from pathlib import Path

import yaml
from loguru import logger
from returns.result import Failure, Result, Success

from classifai.config import app_config

# Path for recording unknown issuers
UNKNOWN_ISSUERS_PATH = Path("config/unknown_issuers.yaml")


def normalize_issuer_name(issuer: str) -> str:
    """
    Normalize issuer name for consistent matching.

    Args:
        issuer: The issuer name to normalize

    Returns:
        Normalized issuer name (lowercase, special characters removed)
    """
    if not issuer:
        return ""

    # Convert to lowercase and remove special characters, keeping only alphanumeric and spaces
    normalized = re.sub(r"[^a-zA-Z0-9\s]", "", issuer.lower())
    # Replace multiple spaces with single space and strip
    return re.sub(r"\s+", " ", normalized).strip()


def record_unknown_issuer(issuer: str) -> Result[None, str]:
    """
    Record an unknown issuer with timestamp for manual review.

    Args:
        issuer: The unknown issuer name

    Returns:
        Result indicating success or failure
    """
    try:
        unknown_issuers_file = Path(app_config.config_dir) / "unknown_issuers.yaml"

        # Load existing unknown issuers or create empty dict
        unknown_issuers = {}
        if unknown_issuers_file.exists():
            with open(unknown_issuers_file, encoding="utf-8") as f:
                content = f.read().strip()
                if content:
                    unknown_issuers = yaml.safe_load(content) or {}

        # Add new unknown issuer with timestamp
        from datetime import timezone

        timestamp = datetime.now(timezone.utc).isoformat()
        normalized_issuer = normalize_issuer_name(issuer)

        # Check if already recorded (avoid duplicates)
        if normalized_issuer not in unknown_issuers:
            unknown_issuers[normalized_issuer] = {
                "original_name": issuer,
                "first_seen": timestamp,
                "last_seen": timestamp,
                "count": 1,
            }
            logger.info(f"Recorded new unknown issuer: {issuer}")
        else:
            # Update existing entry
            unknown_issuers[normalized_issuer]["last_seen"] = timestamp
            unknown_issuers[normalized_issuer]["count"] += 1
            logger.debug(f"Updated unknown issuer count for: {issuer}")

        # Ensure parent directory exists
        unknown_issuers_file.parent.mkdir(parents=True, exist_ok=True)

        # Write back to file
        with open(unknown_issuers_file, "w", encoding="utf-8") as f:
            yaml.dump(unknown_issuers, f, default_flow_style=False, allow_unicode=True)

        return Success(None)

    except Exception as e:
        logger.error(f"Failed to record unknown issuer {issuer}: {e}")
        return Failure(f"Failed to record unknown issuer: {e}")


class KnowledgeBase:
    """
    Knowledge base for ClassifAI.

    Provides access to sector-issuer mappings and other reference data.
    This class is deprecated and will be removed in future versions.
    Use the module-level functions instead.
    """

    def __init__(self):
        """
        Initialize the knowledge base.

        Note: This class is deprecated. Use module-level functions instead.
        """
        logger.warning("KnowledgeBase class is deprecated. Use module-level functions instead.")

    def get_sector_for_issuer(self, issuer: str) -> str | None:
        """
        Find the sector for a given issuer.

        This method is deprecated. Use the module-level get_sector_for_issuer function instead.

        Args:
            issuer: The issuer name

        Returns:
            The sector name or None if not found
        """
        logger.warning(
            "KnowledgeBase.get_sector_for_issuer is deprecated. Use module-level function instead.",
        )
        result = get_sector_for_issuer(issuer)
        return result.unwrap() if isinstance(result, Success) else None


# Note: record_unknown_issuer function is implemented above with the new signature


def load_categories() -> Result[dict[str, list[str]], str]:
    """
    Load categories from the configuration file.

    Returns:
        Result containing either the categories dictionary or an error message
    """
    try:
        categories_path = app_config.config_dir / "categories.yaml"

        if not categories_path.exists():
            return Failure(f"Categories file not found: {categories_path}")

        with open(categories_path, encoding="utf-8") as f:
            categories = yaml.safe_load(f)

        logger.debug(f"Loaded {len(categories)} categories")
        return Success(categories)
    except Exception as e:
        return Failure(f"Failed to load categories: {e}")


def load_sector_issuer_mapping() -> Result[dict[str, list[str]], str]:
    """
    Load sector-issuer mappings from the configuration file.

    Returns:
        Result containing either the mapping dictionary or an error message
    """
    try:
        mapping_path = app_config.config_dir / "sector_issuer_mapping.yaml"

        if not mapping_path.exists():
            return Failure(f"Sector-issuer mapping file not found: {mapping_path}")

        with open(mapping_path, encoding="utf-8") as f:
            mapping = yaml.safe_load(f)

        logger.debug(f"Loaded sector-issuer mappings for {len(mapping)} sectors")
        return Success(mapping)
    except Exception as e:
        return Failure(f"Failed to load sector-issuer mapping: {e}")


def get_sector_for_issuer(issuer: str) -> Result[str, str]:
    """
    Find the sector for a given issuer with alias support and normalization.
    Records unknown issuers for manual review.

    Args:
        issuer: The issuer name

    Returns:
        Result containing either the sector name or an error message
    """
    try:
        if not issuer or not issuer.strip():
            return Failure("Empty issuer name provided")

        # Load the sector-issuer mapping
        mapping_result = load_sector_issuer_mapping()
        if isinstance(mapping_result, Failure):
            return mapping_result

        mapping = mapping_result.unwrap()
        normalized_issuer = normalize_issuer_name(issuer)

        # Search through all sectors and their issuers with normalization
        for sector, issuers in mapping.items():
            if isinstance(issuers, list):
                for mapped_issuer in issuers:
                    normalized_mapped = normalize_issuer_name(mapped_issuer)
                    if normalized_mapped == normalized_issuer:
                        logger.debug(f"Found sector '{sector}' for issuer '{issuer}' (normalized match)")
                        return Success(sector)

                    # Also check for partial matches (issuer contains mapped issuer or vice versa)
                    if (
                        normalized_issuer in normalized_mapped or normalized_mapped in normalized_issuer
                    ) and len(normalized_mapped) > 3:
                        logger.debug(
                            f"Found sector '{sector}' for issuer '{issuer}' (partial match with '{mapped_issuer}')",
                        )
                        return Success(sector)

        # No match found - record as unknown issuer
        logger.info(f"No sector found for issuer '{issuer}'. Recording as unknown.")
        record_result = record_unknown_issuer(issuer)
        if isinstance(record_result, Failure):
            logger.warning(f"Failed to record unknown issuer: {record_result.failure()}")

        return Failure(f"No sector found for issuer: {issuer}")

    except Exception as e:
        logger.error(f"Error finding sector for issuer '{issuer}': {e}")
        return Failure(f"Error finding sector for issuer: {e}")


def get_category_suggestions(text: str, max_suggestions: int = 3) -> Result[list[str], str]:
    """
    Get category suggestions based on document content.

    Args:
        text: The document text
        max_suggestions: Maximum number of suggestions to return

    Returns:
        Result containing either a list of category suggestions or an error message
    """
    categories_result = load_categories()

    if isinstance(categories_result, Failure):
        return categories_result

    categories = categories_result.unwrap()

    # Simple keyword-based matching for now
    # In a real implementation, this would use more sophisticated techniques
    matches = []

    for category, keywords in categories.items():
        for keyword in keywords:
            if keyword.lower() in text.lower():
                matches.append((category, text.lower().count(keyword.lower())))

    # Sort by match count and take top suggestions
    matches.sort(key=lambda x: x[1], reverse=True)
    suggestions = [category for category, _ in matches[:max_suggestions]]

    return Success(suggestions)
