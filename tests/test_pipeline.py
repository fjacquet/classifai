"""
Tests for the refactored core logic and pipeline.
"""

from pathlib import Path

import pytest

# Code under test is now in `core.logic` and `pipeline`
from classifai.core.logic import (
    _calculate_general_destination,
    _calculate_photo_destination,
    determine_final_path,
)
from classifai.core.types import FileContext
from classifai.pipeline import process_file_pipeline


@pytest.fixture
def base_context():
    """Provides a base FileContext for tests, mirroring the new frozen dataclass."""
    return FileContext(
        source_path=Path("/source/file.txt"),
        destination_dir=Path("/dest"),
        rename_files=False,
        use_vision=False,
        language_subfolders=True,
        categories=["Invoices", "Photos", "Reports"],
        language="en",
        sector="Technology",
        issuer="TestCorp",
        ai_results={"category": "Reports"},
    )


# --- Tests for Pure Path Calculation Functions in core.logic ---


def test_calculate_photo_destination_with_full_metadata(base_context):
    """Tests photo destination with complete EXIF data."""
    # Create a new context with updated values instead of modifying the fixture
    context = base_context.__class__(
        **{
            **base_context.__dict__,
            "metadata": {"date": "2025:07:11 10:30:00", "location": "Paris, France"},
            "source_path": Path("photo.jpg"),
            "language": "fr",
        },
    )
    expected_path = Path("/dest") / "fr" / "Photos" / "2025" / "07_July" / "Paris, France" / "photo.jpg"
    assert _calculate_photo_destination(context) == expected_path


def test_calculate_photo_destination_with_date_only(base_context):
    """Tests photo destination with only date information."""
    context = base_context.__class__(
        **{
            **base_context.__dict__,
            "metadata": {"date": "2025:07:11 10:30:00"},
            "source_path": Path("photo.jpg"),
            "language": "en",
        },
    )
    expected_path = Path("/dest") / "en" / "Photos" / "2025" / "07_July" / "photo.jpg"
    assert _calculate_photo_destination(context) == expected_path


def test_calculate_general_destination(base_context):
    """Tests the general destination logic."""
    context = base_context.__class__(
        **{
            **base_context.__dict__,
            "source_path": Path("report.docx"),
            "language": "de",
            "sector": "Finance",
            "issuer": "Global Bank",
            "ai_results": {"category": "Reports"},
        },
    )
    expected_path = Path("/dest") / "de" / "Finance" / "Global Bank" / "Reports" / "report.docx"
    assert _calculate_general_destination(context) == expected_path


def test_determine_final_path_dispatches_to_photo(mocker, base_context):
    """Ensures determine_final_path calls the correct photo helper."""
    context = base_context.__class__(
        **{
            **base_context.__dict__,
            "ai_results": {"category": "Photos"},
            "metadata": {"date": "2025:01:01 00:00:00"},
        },
    )
    mock_photo_calc = mocker.patch("classifai.core.logic._calculate_photo_destination")
    # Make the mock return a valid Path object
    mock_photo_calc.return_value = Path("/test/photo/path.jpg")
    determine_final_path(context)
    mock_photo_calc.assert_called_once_with(context)


def test_determine_final_path_dispatches_to_general(mocker, base_context):
    """Ensures determine_final_path calls the correct general helper."""
    context = base_context.__class__(**{**base_context.__dict__, "ai_results": {"category": "Invoices"}})
    mock_general_calc = mocker.patch("classifai.core.logic._calculate_general_destination")
    # Make the mock return a valid Path object
    mock_general_calc.return_value = Path("/test/general/path.pdf")
    determine_final_path(context)
    mock_general_calc.assert_called_once_with(context)


# --- Integration Test for the Full Pipeline in core_logic.py ---


def test_process_file_pipeline_orchestration(mocker):
    """
    Tests that the pipeline calls all steps in the correct order.
    Now using native Python with two-phase rule matching.
    """
    # Arrange - create a mock FileContext that can be returned by each step
    mock_context = mocker.MagicMock(spec=FileContext)
    mock_context.source_path = Path("/source/file.txt")
    mock_context.rule_match_category = None  # No early rule match

    mock_apply_early_rules = mocker.patch(
        "classifai.pipeline.apply_early_rules", return_value=mock_context
    )
    mock_apply_full_rules = mocker.patch(
        "classifai.pipeline.apply_full_rules", return_value=mock_context
    )
    mock_read_parse = mocker.patch("classifai.pipeline.read_and_parse_file", return_value=mock_context)
    mock_enrich_ai = mocker.patch("classifai.pipeline.enrich_with_ai", return_value=mock_context)
    mock_enrich_knowledge = mocker.patch(
        "classifai.pipeline.enrich_with_knowledge", return_value=mock_context
    )
    mock_determine_path = mocker.patch("classifai.pipeline.determine_final_path", return_value=mock_context)

    scan_config = {
        "dest_dir_str": "/dest",
        "rename_files": False,
        "use_vision": False,
        "language_subfolders": True,
        "categories": ["Test"],
    }
    mock_rules_engine = mocker.MagicMock()

    # Act
    process_file_pipeline(Path("/source/file.txt"), scan_config, mock_rules_engine)

    # Assert - two-phase rule matching
    mock_apply_early_rules.assert_called_once()
    mock_read_parse.assert_called_once()
    mock_apply_full_rules.assert_called_once()  # Called because no early match
    mock_enrich_ai.assert_called_once()
    mock_enrich_knowledge.assert_called_once()
    mock_determine_path.assert_called_once()
