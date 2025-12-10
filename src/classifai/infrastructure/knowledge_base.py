"""
Knowledge base infrastructure for ClassifAI.

This module provides functions for accessing and managing the knowledge base,
which includes categories, sector-issuer mappings, and other reference data.
"""

import re
from datetime import datetime, timezone
from pathlib import Path

import yaml
from loguru import logger

from classifai.config import app_config
from classifai.exceptions import ConfigurationError, KnowledgeBaseError

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


def record_unknown_issuer(issuer: str) -> None:
    """
    Record an unknown issuer with timestamp for manual review.

    Args:
        issuer: The unknown issuer name

    Raises:
        KnowledgeBaseError: If recording fails
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

    except Exception as e:
        logger.error(f"Failed to record unknown issuer {issuer}: {e}")
        raise KnowledgeBaseError(f"Failed to record unknown issuer: {e}") from e


class KnowledgeBase:
    """
    Knowledge base for ClassifAI.

    Provides access to sector-issuer mappings and other reference data.

    .. deprecated::
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
        return get_sector_for_issuer(issuer)


def load_categories() -> list[str]:
    """
    Load categories from the configuration.

    Returns:
        List of categories from configuration

    Raises:
        ConfigurationError: If no categories are configured
    """
    categories = app_config.categories
    if not categories:
        raise ConfigurationError("No categories configured")
    logger.debug(f"Loaded {len(categories)} categories")
    return categories


def load_sector_issuer_mapping() -> dict[str, list[str]]:
    """
    Load sector-issuer mappings from the configuration file.

    Returns:
        Dictionary mapping sectors to lists of issuers

    Raises:
        ConfigurationError: If the mapping file cannot be loaded
    """
    try:
        mapping_path = app_config.config_dir / "sector_issuer_mapping.yaml"

        if not mapping_path.exists():
            raise ConfigurationError(f"Sector-issuer mapping file not found: {mapping_path}")

        with open(mapping_path, encoding="utf-8") as f:
            mapping = yaml.safe_load(f)

        logger.debug(f"Loaded sector-issuer mappings for {len(mapping)} sectors")
        return mapping
    except ConfigurationError:
        raise
    except Exception as e:
        raise ConfigurationError(f"Failed to load sector-issuer mapping: {e}") from e


def get_sector_for_issuer(issuer: str) -> str | None:
    """
    Find the sector for a given issuer with alias support and normalization.
    Records unknown issuers for manual review.

    Args:
        issuer: The issuer name

    Returns:
        The sector name if found, None otherwise
    """
    try:
        if not issuer or not issuer.strip():
            return None

        # Load the sector-issuer mapping
        try:
            mapping = load_sector_issuer_mapping()
        except ConfigurationError as e:
            logger.warning(f"Could not load sector mapping: {e}")
            return None

        normalized_issuer = normalize_issuer_name(issuer)

        # Search through all sectors and their issuers with normalization
        for sector, issuers in mapping.items():
            if isinstance(issuers, list):
                for mapped_issuer in issuers:
                    normalized_mapped = normalize_issuer_name(mapped_issuer)
                    if normalized_mapped == normalized_issuer:
                        logger.debug(f"Found sector '{sector}' for issuer '{issuer}' (normalized match)")
                        return sector

                    # Also check for partial matches (issuer contains mapped issuer or vice versa)
                    if (
                        normalized_issuer in normalized_mapped or normalized_mapped in normalized_issuer
                    ) and len(normalized_mapped) > 3:
                        logger.debug(
                            f"Found sector '{sector}' for issuer '{issuer}' (partial match with '{mapped_issuer}')",
                        )
                        return sector

        # No match found - record as unknown issuer
        logger.info(f"No sector found for issuer '{issuer}'. Recording as unknown.")
        try:
            record_unknown_issuer(issuer)
        except KnowledgeBaseError as e:
            logger.warning(f"Failed to record unknown issuer: {e}")

        return None

    except Exception as e:
        logger.error(f"Error finding sector for issuer '{issuer}': {e}")
        return None


def get_category_suggestions(text: str, max_suggestions: int = 3) -> list[str]:
    """
    Get category suggestions based on document content.

    Matches category names against the document text using simple substring matching.

    Args:
        text: The document text
        max_suggestions: Maximum number of suggestions to return

    Returns:
        List of category suggestions (may be empty if no matches or no categories)
    """
    categories = app_config.categories
    if not categories:
        return []

    text_lower = text.lower()
    matches = []

    # Simple matching: check if category name appears in text
    for category in categories:
        category_lower = category.lower()
        count = text_lower.count(category_lower)
        if count > 0:
            matches.append((category, count))

    # Sort by match count and take top suggestions
    matches.sort(key=lambda x: x[1], reverse=True)
    return [category for category, _ in matches[:max_suggestions]]
