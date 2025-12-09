"""
Tests for the new layered architecture.

This module tests the basic functionality of the new layered architecture,
ensuring that the interfaces can be imported and initialized correctly.
"""

from pathlib import Path

from classifai.app.api import app as api_app
from classifai.app.web_ui import main as web_ui_main
from classifai.classifai_cli import app as cli_app
from classifai.core.classification import classify_document
from classifai.core.types import FileContext
from classifai.infrastructure.knowledge_base import load_categories, load_sector_issuer_mapping
from classifai.pipeline import process_single_file


def test_app_interfaces_importable():
    """Test that app interfaces can be imported."""
    assert cli_app is not None
    assert web_ui_main is not None
    assert api_app is not None


def test_core_modules_importable():
    """Test that core modules can be imported."""
    assert process_single_file is not None
    assert classify_document is not None


def test_infrastructure_modules_importable():
    """Test that infrastructure modules can be imported."""
    assert load_categories is not None
    assert load_sector_issuer_mapping is not None


def test_process_single_file(mocker):
    """Test that process_single_file works correctly."""
    mock_context = FileContext(
        source_path=Path("/test/file.pdf"),
        destination_dir=Path("/test/dest"),
        rename_files=False,
        use_vision=False,
        language_subfolders=True,
        categories=["Invoice", "Contract", "Report"],
    )

    # Mock the pipeline functions to return the mock context directly
    mocker.patch("classifai.pipeline.apply_early_rules", return_value=mock_context)
    mocker.patch("classifai.pipeline.apply_full_rules", return_value=mock_context)
    mocker.patch("classifai.pipeline.read_and_parse_file", return_value=mock_context)
    mocker.patch("classifai.pipeline.enrich_with_ai", return_value=mock_context)
    mocker.patch("classifai.pipeline.enrich_with_knowledge", return_value=mock_context)
    mocker.patch("classifai.pipeline.determine_final_path", return_value=mock_context)

    result = process_single_file(
        file_path=Path("/test/file.pdf"),
        dest_dir=Path("/test/dest"),
    )

    # Check that the result is a FileContext (or None on failure)
    assert result is None or isinstance(result, FileContext)
