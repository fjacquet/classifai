"""
Tests for the core_logic module.
"""

from pathlib import Path
from unittest.mock import MagicMock, patch

from classifai.core_logic import _get_photo_destination, process_file


def test_get_photo_destination_with_full_metadata():
    """
    Tests the photo destination logic with complete EXIF data.
    """
    dest_dir = Path("/tmp/sorted")
    metadata = {"date": "2025:07:11 10:30:00", "location": "Paris, France"}
    filename = "photo.jpg"
    language = "fr"
    expected_path = dest_dir / "fr" / "Photos" / "2025" / "07_July" / "Paris, France" / "photo.jpg"
    assert _get_photo_destination(dest_dir, metadata, filename, language) == expected_path


def test_get_photo_destination_with_date_only():
    """
    Tests the photo destination logic with only date information.
    """
    dest_dir = Path("/tmp/sorted")
    metadata = {"date": "2025:07:11 10:30:00"}
    filename = "photo.jpg"
    language = "en"
    expected_path = dest_dir / "en" / "Photos" / "2025" / "07_July" / "photo.jpg"
    assert _get_photo_destination(dest_dir, metadata, filename, language) == expected_path


def test_get_photo_destination_with_no_metadata():
    """
    Tests the photo destination logic with no relevant EXIF data.
    """
    dest_dir = Path("/tmp/sorted")
    metadata = {}
    filename = "photo.jpg"
    language = None
    expected_path = dest_dir / "Photos" / "photo.jpg"
    assert _get_photo_destination(dest_dir, metadata, filename, language) == expected_path


def test_get_photo_destination_no_language():
    """
    Tests the photo destination logic when no language is provided.
    """
    dest_dir = Path("/tmp/sorted")
    metadata = {"date": "2025:07:11 10:30:00", "location": "Berlin, Germany"}
    filename = "photo.jpg"
    language = None
    expected_path = dest_dir / "Photos" / "2025" / "07_July" / "Berlin, Germany" / "photo.jpg"
    assert _get_photo_destination(dest_dir, metadata, filename, language) == expected_path


@patch("classifai.core_logic.get_parser")
@patch("classifai.core_logic.detect_language")
@patch("classifai.core_logic.classify_content")
@patch("classifai.core_logic.knowledge_base")
def test_process_file_final_path_construction(mock_kb, mock_classify, mock_detect_language, mock_get_parser):
    """
    Tests that the final destination path is constructed correctly according to the spec.
    """
    # Arrange
    mock_parser = MagicMock(return_value=("file content", {}))
    mock_get_parser.return_value = mock_parser
    mock_detect_language.return_value = "fr"
    mock_classify.return_value = {
        "category": "Relevés Bancaires",
        "new_filename": "2025-07-11_Relevé.pdf",
        "issuer": "Revolut",
    }
    mock_kb.get_sector_for_issuer.return_value = "Services Financiers"

    item = Path("/source/releve.pdf")
    dest_dir = Path("/Users/fjacquet/sorted")

    # Act
    _, _, destination_path, _, _, _ = process_file(
        item,
        dest_dir,
        "completion",
        None,
        True,
        False,
        True,
        MagicMock(),
        ["Relevés Bancaires"],
        {},
    )

    # Assert
    expected_path = Path(
        "/Users/fjacquet/sorted/fr/Services Financiers/Revolut/Relevés Bancaires/2025-07-11_Relevé.pdf"
    )
    assert destination_path == expected_path
