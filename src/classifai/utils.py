"""
Utility functions for ClassifAI.
"""

from langdetect import LangDetectException, detect


def detect_language(text: str) -> str | None:
    """
    Detects the language of a given text.

    Args:
        text (str): The text to analyze.

    Returns:
        str | None: The two-letter ISO 639-1 language code (e.g., "en", "fr")
                     or None if detection fails.
    """
    if not text or not isinstance(text, str) or not text.strip():
        return None
    try:
        return detect(text)
    except LangDetectException:
        return None
