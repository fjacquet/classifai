"""
Core classification logic for ClassifAI.

This module contains the pure functions responsible for document classification.
It applies rule-based classification and prepares documents for AI classification.
"""

from loguru import logger
from returns.result import Result, Success

from classifai.core.rules import RulesEngine, apply_rules
from classifai.core.types import FileContext


def classify_document(context: FileContext) -> Result[FileContext, str]:
    """
    Classify a document based on its content and metadata.
    This is a pure function that returns an updated context.

    Args:
        context: The current file context

    Returns:
        Result containing either the updated FileContext or an error message
    """
    logger.debug(f"Classifying document: {context.source_path.name}")

    # Get rules from config
    from classifai.config import app_config

    rules_engine = RulesEngine(app_config.rules)

    # First try rule-based classification
    rule_result = apply_rules(context, rules_engine)

    if isinstance(rule_result, Success):
        updated_context = rule_result.unwrap()
        # If a rule matched, update the context
        if updated_context.rule_match_category:
            logger.info(f"Rule-based classification: {updated_context.rule_match_category}")
            updated_context = context.copy(
                update={
                    "category": updated_context.rule_match_category,
                },
            )
            return Success(updated_context)

    # No rule matched, return the original context for AI classification
    logger.debug("No rule match, will use AI classification")
    return Success(context)


def detect_language(text: str) -> str:
    """
    Detect the language of a text.
    This is a pure function that returns the detected language code.

    Args:
        text: The text to analyze

    Returns:
        ISO 639-1 language code (e.g., 'en', 'fr')
    """
    from langdetect import detect

    try:
        if not text or len(text.strip()) < 20:
            return "N/A"

        lang = detect(text)
        logger.debug(f"Detected language: {lang}")
        return lang
    except Exception as e:
        logger.warning(f"Language detection failed: {e}")
        return "N/A"


def translate_category(category: str, context: str) -> str:
    """
    Translate a category to the target language if needed.
    This is a pure function that returns the translated category.

    Args:
        category: The category to translate
        context: The document context for language detection

    Returns:
        Translated category
    """
    # For now, we'll just return the original category
    # In a future version, this could use a translation service
    return category
