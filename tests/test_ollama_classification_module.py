"""
Tests for the ollama_classification_module.
"""

import json

from classifai.ollama_classification_module import (
    classify_content,
    classify_image_with_vision,
)


def test_classify_content_with_rule_match(mocker):
    """
    Tests that a rule match correctly returns a category and skips AI call.
    """
    mock_rules_engine = mocker.patch("classifai.ollama_classification_module.rules_engine")
    mock_rules_engine.match_category.return_value = "Invoices"
    mock_completion = mocker.patch("classifai.ollama_classification_module.completion")
    mock_logger = mocker.MagicMock()

    categories = ["Documents", "Images", "Invoices"]
    result = classify_content(
        "This is content for an invoice.",
        categories,
        "/path/to/invoice_123.pdf",
        mock_logger,
    )

    assert result == {"category": "Invoices", "new_filename": None}
    mock_rules_engine.match_category.assert_called_once_with("/path/to/invoice_123.pdf")
    mock_completion.assert_not_called()


def test_classify_content_with_kb_match(mocker):
    """
    Tests that a knowledge base match returns a category and skips AI call.
    """
    mocker.patch(
        "classifai.ollama_classification_module.rules_engine.match_category",
        return_value=None,
    )
    mock_kb = mocker.patch("classifai.ollama_classification_module.knowledge_base")
    mock_kb.match_category.return_value = "Receipts"
    mock_completion = mocker.patch("classifai.ollama_classification_module.completion")
    mock_logger = mocker.MagicMock()

    categories = ["Documents", "Images", "Receipts"]
    result = classify_content(
        "Content mentioning a known debitor.",
        categories,
        "/path/to/some_file.txt",
        mock_logger,
    )

    assert result == {"category": "Receipts", "new_filename": None}
    mock_kb.match_category.assert_called_once_with("Content mentioning a known debitor.")
    mock_completion.assert_not_called()


def test_classify_content_success(mocker):
    """
    Tests successful classification via AI fallback.
    """
    mocker.patch(
        "classifai.ollama_classification_module.rules_engine.match_category",
        return_value=None,
    )
    mocker.patch(
        "classifai.ollama_classification_module.knowledge_base.match_category",
        return_value=None,
    )
    mock_response = mocker.MagicMock()
    mock_response.choices[0].message.content = json.dumps(
        {
            "category": "Documents",
            "new_filename": "2025-07-11-test-document.txt",
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
        "issuer": None,
    }


def test_classify_content_unexpected_category(mocker):
    """
    Tests when the model returns a category not in the provided list.
    """
    mocker.patch(
        "classifai.ollama_classification_module.rules_engine.match_category",
        return_value=None,
    )
    mocker.patch(
        "classifai.ollama_classification_module.knowledge_base.match_category",
        return_value=None,
    )
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
    assert result["category"] == "Unknown"
    mock_logger.warning.assert_called_once()


def test_classify_content_api_error(mocker):
    """
    Tests the handling of an API error.
    """
    mocker.patch(
        "classifai.ollama_classification_module.rules_engine.match_category",
        return_value=None,
    )
    mocker.patch(
        "classifai.ollama_classification_module.knowledge_base.match_category",
        return_value=None,
    )
    mocker.patch(
        "classifai.ollama_classification_module.completion",
        side_effect=Exception("API Error"),
    )
    mock_logger = mocker.MagicMock()

    categories = ["Documents", "Images"]
    result = classify_content("This is a test document.", categories, "/path/to/another.txt", mock_logger)
    assert result == {"category": "Unknown", "new_filename": None, "issuer": None}
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
    mocker.patch(
        "classifai.ollama_classification_module.rules_engine.match_category",
        return_value=None,
    )
    mocker.patch(
        "classifai.ollama_classification_module.knowledge_base.match_category",
        return_value=None,
    )
    mock_response = mocker.MagicMock()
    mock_response.choices[0].message.content = "not a valid json"
    mocker.patch(
        "classifai.ollama_classification_module.completion",
        return_value=mock_response,
    )
    mock_logger = mocker.MagicMock()

    categories = ["Documents", "Images"]
    result = classify_content("This is a test document.", categories, "/path/to/doc.txt", mock_logger)
    assert result == {"category": "Unknown", "new_filename": None, "issuer": None}
    mock_logger.error.assert_called_once()
