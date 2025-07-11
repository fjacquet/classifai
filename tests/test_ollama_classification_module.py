"""
Tests for the ollama_classification_module.
"""

from classifai.ollama_classification_module import classify_content


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

    assert result == "Invoices"
    mock_rules_engine.match_category.assert_called_once_with("/path/to/invoice_123.pdf")
    mock_completion.assert_not_called()


def test_classify_content_with_kb_match(mocker):
    """
    Tests that a knowledge base match returns a category and skips AI call.
    """
    mocker.patch("classifai.ollama_classification_module.rules_engine.match_category", return_value=None)
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

    assert result == "Receipts"
    mock_kb.match_category.assert_called_once_with("Content mentioning a known debitor.")
    mock_completion.assert_not_called()


def test_classify_content_success(mocker):
    """
    Tests successful classification via AI fallback.
    """
    mocker.patch("classifai.ollama_classification_module.rules_engine.match_category", return_value=None)
    mocker.patch("classifai.ollama_classification_module.knowledge_base.match_category", return_value=None)
    mock_response = mocker.MagicMock()
    mock_response.choices[0].message.content = "Documents"
    mocker.patch(
        "classifai.ollama_classification_module.completion",
        return_value=mock_response,
    )
    mock_logger = mocker.MagicMock()

    categories = ["Documents", "Images"]
    result = classify_content("This is a test document.", categories, "/path/to/doc.txt", mock_logger)
    assert result == "Documents"


def test_classify_content_unexpected_category(mocker):
    """
    Tests when the model returns a category not in the provided list.
    """
    mocker.patch("classifai.ollama_classification_module.rules_engine.match_category", return_value=None)
    mocker.patch("classifai.ollama_classification_module.knowledge_base.match_category", return_value=None)
    mock_response = mocker.MagicMock()
    mock_response.choices[0].message.content = "Invoices"
    mocker.patch(
        "classifai.ollama_classification_module.completion",
        return_value=mock_response,
    )
    mock_logger = mocker.MagicMock()

    categories = ["Documents", "Images"]
    result = classify_content("This is a test invoice.", categories, "/path/to/invoice.pdf", mock_logger)
    assert result == "Unknown"
    mock_logger.warning.assert_called_once()


def test_classify_content_api_error(mocker):
    """
    Tests the handling of an API error.
    """
    mocker.patch("classifai.ollama_classification_module.rules_engine.match_category", return_value=None)
    mocker.patch("classifai.ollama_classification_module.knowledge_base.match_category", return_value=None)
    mocker.patch(
        "classifai.ollama_classification_module.completion",
        side_effect=Exception("API Error"),
    )
    mock_logger = mocker.MagicMock()

    categories = ["Documents", "Images"]
    result = classify_content("This is a test document.", categories, "/path/to/another.txt", mock_logger)
    assert result == "Unknown"
    mock_logger.error.assert_called_once()
