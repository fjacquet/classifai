"""
Tests for the ollama_classification_module.
"""

import json

from classifai.ollama_classification_module import (
    classify_content,
    classify_image_with_vision,
)


def test_classify_content_success(mocker):
    """
    Tests successful classification via AI fallback.
    """
    mock_response = mocker.MagicMock()
    mock_response.choices[0].message.content = json.dumps(
        {
            "category": "Documents",
            "new_filename": "2025-07-11-test-document.txt",
            "issuer": "TestCorp",
        }
    )
    mocker.patch(
        "classifai.ollama_classification_module.completion",
        return_value=mock_response,
    )
    mock_logger = mocker.MagicMock()

    categories = ["Documents", "Images"]
    result = classify_content("This is a test document.", categories, "/path/to/doc.txt", mock_logger)
    assert result == {
        "category": "Documents",
        "new_filename": "2025-07-11-test-document.txt",
        "issuer": "TestCorp",
    }


def test_classify_content_unexpected_category(mocker):
    """
    Tests when the model returns a category not in the provided list.
    """
    mock_response = mocker.MagicMock()
    mock_response.choices[0].message.content = json.dumps(
        {"category": "Invoices", "new_filename": "2025-07-11-invoice.pdf"}
    )
    mocker.patch(
        "classifai.ollama_classification_module.completion",
        return_value=mock_response,
    )
    mock_logger = mocker.MagicMock()

    categories = ["Documents", "Images"]
    result = classify_content("This is a test invoice.", categories, "/path/to/invoice.pdf", mock_logger)
    assert result["category"] == "Non Classé"
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
    result = classify_content("This is a test document.", categories, "/path/to/another.txt", mock_logger)
    assert result == {"category": "Non Classé", "new_filename": None, "issuer": None}
    mock_logger.error.assert_called_once()


def test_classify_image_with_vision_success(mocker):
    """
    Tests successful image description with a vision model.
    """
    mock_response = mocker.MagicMock()
    mock_response.choices[0].message.content = "A beautiful landscape."
    mock_completion = mocker.patch(
        "classifai.ollama_classification_module.completion",
        return_value=mock_response,
    )
    mocker.patch("builtins.open", mocker.mock_open(read_data=b"imagedata"))
    mock_logger = mocker.MagicMock()

    description = classify_image_with_vision("/path/to/image.png", mock_logger)

    assert description == "A beautiful landscape."
    mock_completion.assert_called_once()


def test_classify_content_json_error(mocker):
    """
    Tests the handling of a JSON decoding error.
    """
    mock_response = mocker.MagicMock()
    mock_response.choices[0].message.content = "not a valid json"
    mocker.patch(
        "classifai.ollama_classification_module.completion",
        return_value=mock_response,
    )
    mock_logger = mocker.MagicMock()

    categories = ["Documents", "Images"]
    result = classify_content("This is a test document.", categories, "/path/to/doc.txt", mock_logger)
    assert result == {"category": "Non Classé", "new_filename": None, "issuer": None}
    mock_logger.error.assert_called_once()
