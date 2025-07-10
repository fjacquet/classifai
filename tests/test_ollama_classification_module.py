"""
Tests for the ollama_classification_module.
"""

import pytest
from classifai.ollama_classification_module import classify_content


def test_classify_content_success(mocker):
    """
    Tests successful classification.
    """
    mock_response = mocker.MagicMock()
    mock_response.choices[0].message.content = "Documents"
    mocker.patch(
        "classifai.ollama_classification_module.completion",
        return_value=mock_response,
    )
    mock_logger = mocker.MagicMock()

    categories = ["Documents", "Images"]
    result = classify_content("This is a test document.", categories, mock_logger)
    assert result == "Documents"


def test_classify_content_unexpected_category(mocker):
    """
    Tests when the model returns a category not in the provided list.
    """
    mock_response = mocker.MagicMock()
    mock_response.choices[0].message.content = "Invoices"
    mocker.patch(
        "classifai.ollama_classification_module.completion",
        return_value=mock_response,
    )
    mock_logger = mocker.MagicMock()

    categories = ["Documents", "Images"]
    result = classify_content("This is a test invoice.", categories, mock_logger)
    assert result == "Unknown"
    mock_logger.warning.assert_called_once()


def test_classify_content_api_error(mocker):
    """
    Tests the handling of an API error.
    """
    mocker.patch(
        "classifai.ollama_classification_module.completion",
        side_effect=Exception("API Error"),
    )
    mock_logger = mocker.MagicMock()

    categories = ["Documents", "Images"]
    result = classify_content("This is a test document.", categories, mock_logger)
    assert result == "Unknown"
    mock_logger.error.assert_called_once()