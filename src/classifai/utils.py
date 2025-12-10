"""
Utility functions for ClassifAI.

This module provides shared utilities following DRY principle.
All filename/path sanitization and date parsing should use these functions.
"""

import re
from datetime import datetime

from langdetect import LangDetectException, detect

# Pre-compiled patterns (performance optimization)
_SANITIZE_PATTERN = re.compile(r"[^\w\s\-_.]")
_WHITESPACE_PATTERN = re.compile(r"\s+")

# Date formats to try when parsing dates
DATE_FORMATS = [
    "%Y-%m-%d",
    "%Y:%m:%d %H:%M:%S",  # EXIF format
    "%d/%m/%Y",
    "%d.%m.%Y",
    "%Y%m%d",
    "%Y-%m-%d %H:%M:%S",
    "%d-%m-%Y",
]


def sanitize_filename(
    text: str,
    max_length: int = 100,
    allowed: str = " -_.",
    replace_spaces_with: str | None = None,
) -> str:
    """
    Sanitize text for use in filenames.

    This is the single source of truth for filename sanitization.
    Use this instead of inline `"".join(c for c in ...)` patterns.

    Args:
        text: The text to sanitize
        max_length: Maximum length of the result
        allowed: Additional characters to allow (beyond alphanumeric)
        replace_spaces_with: If provided, replace spaces with this character

    Returns:
        Sanitized string safe for use in filenames
    """
    if not text:
        return ""

    # Keep only alphanumeric characters and allowed characters
    safe = "".join(c for c in text if c.isalnum() or c in allowed)

    # Normalize whitespace
    safe = _WHITESPACE_PATTERN.sub(" ", safe).strip()

    # Optionally replace spaces
    if replace_spaces_with is not None:
        safe = safe.replace(" ", replace_spaces_with)

    return safe[:max_length].rstrip()


def sanitize_path_component(text: str, max_length: int = 100) -> str:
    """
    Sanitize text for use as a directory name.

    More restrictive than sanitize_filename - no dots allowed.

    Args:
        text: The text to sanitize
        max_length: Maximum length of the result

    Returns:
        Sanitized string safe for use as directory name
    """
    return sanitize_filename(text, max_length=max_length, allowed=" -_")


def parse_date_flexible(date_str: str) -> datetime | None:
    """
    Parse dates in multiple formats.

    This is the single source of truth for date parsing.

    Args:
        date_str: String representation of a date

    Returns:
        datetime object if parsing succeeded, None otherwise
    """
    if not date_str:
        return None

    date_str = date_str.strip()

    for fmt in DATE_FORMATS:
        try:
            return datetime.strptime(date_str, fmt)  # noqa: DTZ007 - intentionally naive
        except ValueError:
            continue

    return None


def format_date_for_filename(dt: datetime | None) -> str:
    """
    Format a datetime for use in filenames.

    Args:
        dt: datetime object to format

    Returns:
        Date string in YYYY-MM-DD format, or empty string if dt is None
    """
    if dt is None:
        return ""
    return dt.strftime("%Y-%m-%d")


def detect_language(text: str) -> str | None:
    """
    Detects the language of a given text.

    Args:
        text: The text to analyze.

    Returns:
        The two-letter ISO 639-1 language code (e.g., "en", "fr")
        or None if detection fails.
    """
    if not text or not isinstance(text, str) or not text.strip():
        return None
    try:
        return detect(text)
    except LangDetectException:
        return None
