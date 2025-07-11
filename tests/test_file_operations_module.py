"""
Tests for the file_operations_module.
"""

import tempfile
from contextlib import contextmanager
from pathlib import Path

from classifai.file_operations_module import copy_file, move_file


@contextmanager
def create_test_env():
    """
    Creates a temporary directory structure for testing file operations.
    Yields the source directory path and the path to a test file.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        source_dir = Path(tmpdir) / "source"
        source_dir.mkdir()
        test_file = source_dir / "test.txt"
        test_file.write_text("test content")
        yield source_dir, test_file


def test_move_file():
    """
    Tests the move_file function with a simple move operation.
    """
    with create_test_env() as (source_dir, test_file):
        dest_dir = source_dir.parent / "destination"
        dest_path = dest_dir / "test.txt"

        moved_path_str = move_file(str(test_file.absolute()), str(dest_path.absolute()))
        moved_path = Path(moved_path_str)

        assert moved_path.exists()
        assert moved_path.name == "test.txt"
        assert not test_file.exists()
        assert moved_path.read_text() == "test content"
        assert moved_path.parent == dest_dir.absolute()


def test_copy_file():
    """
    Tests the copy_file function.
    """
    with create_test_env() as (source_dir, test_file):
        dest_dir = source_dir.parent / "destination"
        dest_path = dest_dir / "test.txt"

        copied_path_str = copy_file(str(test_file.absolute()), str(dest_path.absolute()))
        copied_path = Path(copied_path_str)

        assert copied_path.exists()
        assert copied_path.name == "test.txt"
        assert test_file.exists()  # Original file should still exist
        assert copied_path.read_text() == "test content"
        assert copied_path.parent == dest_dir.absolute()


def test_name_conflict_resolution():
    """
    Tests that name conflicts are handled correctly by appending a counter.
    """
    with create_test_env() as (source_dir, test_file):
        dest_dir = source_dir.parent / "destination"
        dest_dir.mkdir()

        # Create a file with the same name in the destination
        existing_file = dest_dir / "test.txt"
        existing_file.write_text("existing content")

        # The destination path for the move is the same as the existing file
        dest_path = dest_dir / "test.txt"

        moved_path_str = move_file(str(test_file.absolute()), str(dest_path.absolute()))
        moved_path = Path(moved_path_str)

        assert moved_path.exists()
        assert moved_path.name == "test (1).txt"
        assert moved_path.parent == dest_dir.absolute()
        assert existing_file.exists()  # The original conflicting file should still be there
