"""
Tests for the file_operations_module.
"""

from contextlib import contextmanager
from pathlib import Path
import tempfile
import shutil

from classifai.file_operations_module import copy_file, move_file


@contextmanager
def create_test_env():
    """
    Creates a temporary directory structure for testing file operations.
    Yields:
        tuple: A tuple containing the source directory path and the test file path.
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
        copied_path_str = copy_file(
            str(test_file.absolute()), str(dest_dir.absolute())
        )
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
        (dest_dir / "test.txt").write_text("existing content")

        moved_path_str = move_file(str(test_file.absolute()), str(dest_dir.absolute()))
        moved_path = Path(moved_path_str)

        assert moved_path.exists()
        assert moved_path.name == "test (1).txt"