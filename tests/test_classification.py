"""
Functional tests for the classification module.

This module tests the core classification functionality including:
- Rule-based classification
- Language detection
- Category translation
"""

from pathlib import Path

import pytest
from returns.result import Success

from classifai.core.classification import classify_document, detect_language, translate_category
from classifai.core.types import FileContext


@pytest.fixture
def test_context():
    """Create a test file context for classification tests."""
    test_file_path = Path("/test/document.pdf")
    return FileContext(
        source_path=test_file_path,
        destination_dir=Path("/test/dest"),
        rename_files=False,
        use_vision=False,
        language_subfolders=True,
        categories=["Invoice", "Contract", "Report"],
        content="This is a test invoice document for ABC Corp.",
        metadata={"title": "Invoice #12345", "author": "John Doe"},
    )


def test_rule_based_classification(mocker, test_context):
    """Test rule-based classification with matching rules."""
    # Mock the app_config where it's imported inside the function
    mock_config = mocker.patch("classifai.config.app_config")
    # Mock the rules engine to match a category
    mock_rules = [
        {
            "name": "Invoice Rule",
            "conditions": [{"type": "filename", "pattern": "*.pdf"}],
            "action": {"type": "categorize", "category": "Invoice"},
        },
    ]
    mock_config.rules = mock_rules

    # Call the classify_document function
    result = classify_document(test_context)

    # Check that the result is a Success and contains the expected category
    assert isinstance(result, Success)
    updated_context = result.unwrap()
    assert updated_context.category == "Invoice"


def test_no_rule_match(mocker, test_context):
    """Test classification when no rules match."""
    # Mock the app_config where it's imported inside the function
    mock_config = mocker.patch("classifai.config.app_config")
    # Mock the rules engine with no matching rules
    mock_rules = [
        {
            "name": "Contract Rule",
            "conditions": [{"type": "filename", "pattern": "*.docx"}],
            "action": {"type": "categorize", "category": "Contract"},
        },
    ]
    mock_config.rules = mock_rules

    # Call the classify_document function
    result = classify_document(test_context)

    # Check that the result is a Success but no category was assigned
    assert isinstance(result, Success)
    updated_context = result.unwrap()
    assert getattr(updated_context, "category", None) is None


def test_language_detection_english():
    """Test language detection for English text."""
    text = "This is a sample English text that should be detected correctly."
    lang = detect_language(text)
    assert lang == "en"


def test_language_detection_french():
    """Test language detection for French text."""
    text = "Ceci est un exemple de texte français qui devrait être détecté correctement."
    lang = detect_language(text)
    assert lang == "fr"


def test_language_detection_short_text():
    """Test language detection with very short text."""
    text = "Hi"
    lang = detect_language(text)
    assert lang == "N/A"


def test_language_detection_empty():
    """Test language detection with empty text."""
    text = ""
    lang = detect_language(text)
    assert lang == "N/A"


def test_category_translation():
    """Test category translation."""
    category = "Invoice"
    context = "This is a test document."
    translated = translate_category(category, context)
    # Currently, the function just returns the original category
    assert translated == category
