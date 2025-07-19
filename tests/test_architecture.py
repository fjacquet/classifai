"""
Tests for the new layered architecture.

This module tests the basic functionality of the new layered architecture,
ensuring that the interfaces can be imported and initialized correctly.
"""

from pathlib import Path

from classifai.app.api import app as api_app
from classifai.app.cli import app as cli_app
from classifai.app.web_ui import main as web_ui_main
from classifai.core.classification import classify_document
from classifai.core.workflow import process_directory, process_single_file
from classifai.infrastructure.knowledge_base import load_categories, load_sector_issuer_mapping


def test_app_interfaces_importable():
    """Test that app interfaces can be imported."""
    assert cli_app is not None
    assert web_ui_main is not None
    assert api_app is not None


def test_core_modules_importable():
    """Test that core modules can be imported."""
    assert process_single_file is not None
    assert process_directory is not None
    assert classify_document is not None


def test_infrastructure_modules_importable():
    """Test that infrastructure modules can be imported."""
    assert load_categories is not None
    assert load_sector_issuer_mapping is not None


def test_process_single_file(mocker):
    """Test that process_single_file works correctly."""
    # Mock the read_file_content function to return a Success
    from returns.result import Success

    from classifai.core.types import FileContext

    mock_context = FileContext(
        source_path=Path("/test/file.pdf"),
        destination_dir=Path("/test/dest"),
        rename_files=False,
        use_vision=False,
        language_subfolders=True,
        categories=["Invoice", "Contract", "Report"],
    )
    mocker.patch("classifai.core.workflow.read_file_content", return_value=Success(mock_context))

    # Call the function with mock arguments
    with (
        mocker.patch("classifai.core.workflow.classify_document", return_value=Success(mock_context)),
        mocker.patch("classifai.core.workflow.enrich_with_ai", return_value=Success(mock_context)),
        mocker.patch("classifai.core.workflow.determine_final_path", return_value=mock_context),
        mocker.patch(
            "classifai.core.workflow.move_file_to_destination",
            return_value=Success(mock_context),
        ),
    ):
        result = process_single_file(
            file_path=Path("/test/file.pdf"),
            dest_dir=Path("/test/dest"),
        )

    # Check that the result is a Success
    assert isinstance(result, Success)
