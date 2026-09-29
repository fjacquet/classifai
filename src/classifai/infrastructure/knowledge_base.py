"""
Knowledge base infrastructure for ClassifAI.

This module provides functions for accessing and managing the knowledge base,
which includes categories, sector-issuer mappings, and other reference data.
"""

import re
import unicodedata
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, NamedTuple

import yaml
from loguru import logger

from classifai.config import app_config
from classifai.exceptions import ConfigurationError, KnowledgeBaseError
from classifai.utils import write_text_atomic


class IssuerMatch(NamedTuple):
    """Result of a knowledge-base lookup: sector and the issuer name as written in the mapping."""

    sector: str | None
    canonical_name: str | None


def unknown_issuers_path() -> Path:
    """Return the file where unknown issuers are recorded for manual review."""
    return Path(app_config.config_dir) / "unknown_issuers.yaml"


def normalize_issuer_name(issuer: str) -> str:
    """
    Normalize issuer name for consistent matching.

    Args:
        issuer: The issuer name to normalize

    Returns:
        Normalized issuer name (lowercase, accents folded, punctuation replaced by spaces)
    """
    if not issuer:
        return ""

    # Fold accents (é -> e), lowercase, then drop remaining special characters
    decomposed = unicodedata.normalize("NFKD", issuer)
    folded = "".join(c for c in decomposed if not unicodedata.combining(c))
    normalized = re.sub(r"[^a-z0-9\s]", " ", folded.lower())
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
        unknown_issuers_file = unknown_issuers_path()

        # Load existing unknown issuers or create empty dict
        unknown_issuers: dict[str, dict[str, Any]] = {}
        if unknown_issuers_file.exists():
            with open(unknown_issuers_file, encoding="utf-8") as f:
                content = f.read().strip()
                if content:
                    loaded = yaml.safe_load(content)
                    if isinstance(loaded, dict):
                        unknown_issuers = loaded

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

        write_text_atomic(
            unknown_issuers_file,
            yaml.dump(unknown_issuers, default_flow_style=False, allow_unicode=True),
        )

    except Exception as e:
        logger.error(f"Failed to record unknown issuer {issuer}: {e}")
        raise KnowledgeBaseError(f"Failed to record unknown issuer: {e}") from e


def load_sector_issuer_mapping() -> dict[str, Any]:
    """
    Return the sector-issuer mapping loaded once at startup by ``config``.

    Returns:
        Dictionary mapping sectors to lists of issuers, plus an optional ``aliases`` dict

    Raises:
        ConfigurationError: If no mapping is configured
    """
    if not app_config.sector_issuer_mapping:
        raise ConfigurationError("No sector-issuer mapping configured")
    return app_config.sector_issuer_mapping


def _resolve_alias(normalized_issuer: str, aliases: Any) -> str:
    """Map a normalized issuer to its normalized canonical name when an alias exists."""
    if not isinstance(aliases, dict):
        return normalized_issuer
    for alias, canonical in aliases.items():
        if normalize_issuer_name(str(alias)) == normalized_issuer:
            return normalize_issuer_name(str(canonical))
    return normalized_issuer


def _contains_words(text: str, words: str) -> bool:
    """Return True if *words* appears in *text* on word boundaries."""
    return re.search(rf"\b{re.escape(words)}\b", text) is not None


def lookup_issuer(issuer: str) -> IssuerMatch:
    """
    Find the sector and canonical name of an issuer, resolving aliases.
    Records unknown issuers for manual review.

    Args:
        issuer: The issuer name as extracted from the document

    Returns:
        IssuerMatch(sector, canonical_name); both None when the issuer is unknown
    """
    no_match = IssuerMatch(None, None)
    if not issuer or not issuer.strip():
        return no_match

    try:
        mapping = load_sector_issuer_mapping()
    except ConfigurationError as e:
        logger.warning(f"Could not load sector mapping: {e}")
        return no_match

    normalized_issuer = _resolve_alias(normalize_issuer_name(issuer), mapping.get("aliases"))

    for sector, issuers in mapping.items():
        if not isinstance(issuers, list):
            continue
        for mapped_issuer in issuers:
            normalized_mapped = normalize_issuer_name(mapped_issuer)
            if normalized_mapped and _contains_words(normalized_issuer, normalized_mapped):
                logger.debug(f"Found sector '{sector}' for issuer '{issuer}' (match with '{mapped_issuer}')")
                return IssuerMatch(sector, mapped_issuer)

    logger.info(f"No sector found for issuer '{issuer}'. Recording as unknown.")
    try:
        record_unknown_issuer(issuer)
    except KnowledgeBaseError as e:
        logger.warning(f"Failed to record unknown issuer: {e}")
    return no_match


def get_sector_for_issuer(issuer: str) -> str | None:
    """
    Find the sector for a given issuer with alias support and normalization.

    Args:
        issuer: The issuer name

    Returns:
        The sector name if found, None otherwise
    """
    return lookup_issuer(issuer).sector
