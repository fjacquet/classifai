"""
Tests for the file_operations_module.
"""

import tempfile
from contextlib import contextmanager
from pathlib import Path

from classifai.file_operations_module import _get_photo_destination, copy_file, move_file


@contextmanager
def create_test_env():
    """
    Creates a temporary directory structure for testing file operations.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        source_dir = Path(tmpdir) / "source"
        source_dir.mkdir()
        test_file = source_dir / "test.txt"
        test_file.write_text("test content")
        yield source_dir, test_file


def test_move_file():
    """
    Tests the move_file function.
    """
    with create_test_env() as (source_dir, test_file):
        dest_dir = source_dir.parent / "destination"
        moved_path_str = move_file(str(test_file.absolute()), str(dest_dir.absolute()))
        moved_path = Path(moved_path_str)

        assert moved_path.exists()
        assert moved_path.name == "test.txt"
        assert not test_file.exists()
        assert moved_path.read_text() == "test content"


def test_copy_file():
    """
    Tests the copy_file function.
    """
    with create_test_env() as (source_dir, test_file):
        dest_dir = source_dir.parent / "destination"
        copied_path_str = copy_file(str(test_file.absolute()), str(dest_dir.absolute()))
        copied_path = Path(copied_path_str)

        assert copied_path.exists()
        assert copied_path.name == "test.txt"
        assert test_file.exists()  # Original file should still exist
        assert copied_path.read_text() == "test content"


def test_name_conflict():
    """
    Tests that name conflicts are handled correctly.
    """
    with create_test_env() as (source_dir, test_file):
        dest_dir = source_dir.parent / "destination"
        dest_dir.mkdir()

        # Create a file with the same name in the destination
        (dest_dir / "Unknown_Issuer").mkdir(parents=True, exist_ok=True)
        (dest_dir / "Unknown_Issuer" / "test.txt").write_text("existing content")

        moved_path_str = move_file(str(test_file.absolute()), str(dest_dir.absolute()))
        moved_path = Path(moved_path_str)

        assert moved_path.exists()
        assert moved_path.name == "test (1).txt"
        assert moved_path.parent.name == "Unknown_Issuer"


def test_photo_destination_with_full_metadata():
    """
    Tests the photo destination logic with complete EXIF data.
    """
    dest_dir = Path("/tmp/sorted")
    metadata = {"date": "2025:07:11 10:30:00", "location": "Paris, France"}
    filename = "photo.jpg"
    expected_path = dest_dir / "Photos/2025/07_July/Paris, France/photo.jpg"
    assert _get_photo_destination(dest_dir, metadata, filename) == expected_path


def test_photo_destination_with_date_only():
    """
    Tests the photo destination logic with only date information.
    """
    dest_dir = Path("/tmp/sorted")
    metadata = {"date": "2025:07:11 10:30:00"}
    filename = "photo.jpg"
    expected_path = dest_dir / "Photos/2025/07_July/photo.jpg"
    assert _get_photo_destination(dest_dir, metadata, filename) == expected_path


def test_photo_destination_with_no_metadata():
    """
    Tests the photo destination logic with no relevant EXIF data.
    """
    dest_dir = Path("/tmp/sorted")
    metadata = {}
    filename = "photo.jpg"
    expected_path = dest_dir / "Photos/photo.jpg"
    assert _get_photo_destination(dest_dir, metadata, filename) == expected_path


def test_language_subfolder_creation():
    """
    Tests that a language subfolder is created when a language is provided.
    """
    with create_test_env() as (source_dir, test_file):
        dest_dir = source_dir.parent / "destination"
        moved_path_str = move_file(str(test_file.absolute()), str(dest_dir.absolute()), language="en")
        moved_path = Path(moved_path_str)

        assert moved_path.exists()
        assert moved_path.parent.name == "en"
        assert moved_path.parent.parent.name == "Unknown_Issuer"
        assert moved_path.parent.parent.parent == dest_dir.absolute()


def test_file_renaming():
    """
    Tests that a file is correctly renamed during a move operation.
    """
    with create_test_env() as (source_dir, test_file):
        dest_dir = source_dir.parent / "destination"
        new_name = "renamed_file.txt"
        moved_path_str = move_file(str(test_file.absolute()), str(dest_dir.absolute()), new_filename=new_name)
        moved_path = Path(moved_path_str)

        assert moved_path.exists()
        assert moved_path.name == new_name


def test_issuer_subfolder_creation():
    """
    Tests that an issuer subfolder is created when an issuer is provided.
    """
    with create_test_env() as (source_dir, test_file):
        dest_dir = source_dir.parent / "destination"
        moved_path_str = move_file(
            str(test_file.absolute()),
            str(dest_dir.absolute()),
            issuer="TestIssuer",
        )
        moved_path = Path(moved_path_str)

        assert moved_path.exists()
        assert moved_path.parent.name == "TestIssuer"
        assert moved_path.parent.parent == dest_dir.absolute()


def test_full_path_creation():
    """
    Tests the creation of the full path with language, issuer, and category.
    """
    with create_test_env() as (source_dir, test_file):
        dest_dir = source_dir.parent / "destination"
        moved_path_str = move_file(
            str(test_file.absolute()),
            str(dest_dir.absolute()),
            language="en",
            issuer="TestIssuer",
        )
        moved_path = Path(moved_path_str)

        assert moved_path.exists()
        assert moved_path.name == "test.txt"
        assert moved_path.parent.name == "en"
        assert moved_path.parent.parent.name == "TestIssuer"
        assert moved_path.parent.parent.parent == dest_dir.absolute()


def test_full_path_creation_no_issuer():
    """
    Tests the creation of the full path when no issuer is provided.
    """
    with create_test_env() as (source_dir, test_file):
        dest_dir = source_dir.parent / "destination"
        moved_path_str = move_file(
            str(test_file.absolute()),
            str(dest_dir.absolute()),
            language="en",
        )
        moved_path = Path(moved_path_str)

        assert moved_path.exists()
        assert moved_path.name == "test.txt"
        assert moved_path.parent.name == "en"
        assert moved_path.parent.parent.name == "Unknown_Issuer"
        assert moved_path.parent.parent.parent == dest_dir.absolute()
