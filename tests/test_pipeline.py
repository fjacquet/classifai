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
            "category": "Images",
            "ai_results": {"category": "Images"},
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

    mock_apply_early_rules = mocker.patch("classifai.pipeline.apply_early_rules", return_value=mock_context)
    mock_apply_full_rules = mocker.patch("classifai.pipeline.apply_full_rules", return_value=mock_context)
    mock_read_parse = mocker.patch("classifai.pipeline.read_and_parse_file", return_value=mock_context)
    mock_enrich_ai = mocker.patch("classifai.pipeline.enrich_with_ai", return_value=mock_context)
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
    mock_determine_path.assert_called_once()


# --- Regression tests ---


def test_rule_match_path_has_no_na_folders(base_context):
    """'N/A' contains a slash and must never become a path segment."""
    context = base_context.model_copy(update={"rule_match_category": "Factures", "language": "N/A"})

    final_path = determine_final_path(context).final_destination_path

    assert "N" not in final_path.relative_to(Path("/dest")).parts
    assert final_path.name == "file.txt"
    assert final_path.parent.name == "Factures"


def test_images_category_uses_photo_layout(base_context):
    """Images with an EXIF date are filed by year/month."""
    context = base_context.model_copy(
        update={
            "category": "Images",
            "ai_results": {"category": "Images"},
            "metadata": {"date": "2024:05:01 10:00:00"},
            "source_path": Path("/source/IMG_1.jpg"),
        },
    )

    final_path = determine_final_path(context).final_destination_path

    assert final_path == Path("/dest/en/Photos/2024/05_May/IMG_1.jpg")


def test_unknown_issuer_recorded_once_per_file(mocker, tmp_path, isolated_unknown_issuers):
    """The KB lookup runs once per file, so unknown issuers are counted once."""
    import yaml

    source = tmp_path / "doc.txt"
    source.write_text("hello")
    mocker.patch(
        "classifai.infrastructure.knowledge_base.load_sector_issuer_mapping",
        return_value={"Banque": ["UBS"]},
    )
    mocker.patch("classifai.pipeline.apply_early_rules", side_effect=lambda c, _: c)
    mocker.patch("classifai.pipeline.read_and_parse_file", side_effect=lambda c: c)
    mocker.patch(
        "classifai.infrastructure.llm.get_completion",
        return_value={"response": '{"issuer": "Nobody Corp", "category": "Reports"}'},
    )
    mocker.patch("classifai.infrastructure.llm.get_sector_with_ai", return_value=None)
    scan_config = {
        "dest_dir_str": str(tmp_path / "out"),
        "rename_files": False,
        "use_vision": False,
        "language_subfolders": True,
        "categories": ["Reports"],
    }

    mocker.patch("classifai.pipeline.apply_full_rules", side_effect=lambda c, _: c)

    assert process_file_pipeline(source, scan_config, mocker.MagicMock()) is not None

    data = yaml.safe_load(isolated_unknown_issuers.read_text())
    assert data["nobody corp"]["count"] == 1


def test_run_scan_skips_unsupported_and_hidden_files(mocker, tmp_path):
    """Only supported, non-hidden files reach the pipeline."""
    from classifai.pipeline import run_scan

    for name in ("invoice.pdf", "SCAN.PDF", ".DS_Store", "~$report.docx", "notes.xyz"):
        (tmp_path / name).write_text("x")
    mock_process = mocker.patch("classifai.pipeline.process_file_pipeline", return_value=None)

    run_scan(str(tmp_path), str(tmp_path / "out"), False, False, True, False, ["Reports"])

    processed = sorted(call.args[0].name for call in mock_process.call_args_list)
    assert processed == ["SCAN.PDF", "invoice.pdf"]


def test_punctuation_only_issuer_falls_back_to_unknown(base_context):
    """An issuer that sanitizes to nothing must not produce an empty path segment."""
    context = base_context.model_copy(update={"issuer": "***"})

    path = _calculate_general_destination(context)

    assert "" not in path.parts
    assert path.parent.parent.name in {"Unknown_Issuer", "Émetteur_Inconnu"}
