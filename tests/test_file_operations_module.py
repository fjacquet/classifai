"""
Tests for the file_operations_module.
"""

import tempfile
from contextlib import contextmanager
from pathlib import Path

import pytest

from classifai.core.types import FileContext
from classifai.exceptions import FileOperationError
from classifai.infrastructure.file_system import transfer_file


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

        context = FileContext(
            source_path=test_file,
            destination_dir=dest_dir,
            rename_files=False,
            use_vision=False,
            language_subfolders=False,
            categories=[],
            final_destination_path=dest_path,
        )

        result = transfer_file(context, "move")
        # transfer_file now returns FileContext directly (or raises exception)
        assert isinstance(result, FileContext)

        moved_path = Path(result.final_destination_path)
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

        context = FileContext(
            source_path=test_file,
            destination_dir=dest_dir,
            rename_files=False,
            use_vision=False,
            language_subfolders=False,
            categories=[],
            final_destination_path=dest_path,
        )

        result = transfer_file(context, "copy")
        # transfer_file now returns FileContext directly (or raises exception)
        assert isinstance(result, FileContext)

        copied_path = Path(result.final_destination_path)
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

        context = FileContext(
            source_path=test_file,
            destination_dir=dest_dir,
            rename_files=False,
            use_vision=False,
            language_subfolders=False,
            categories=[],
            final_destination_path=dest_path,
        )

        result = transfer_file(context, "move")
        # transfer_file now returns FileContext directly (or raises exception)
        assert isinstance(result, FileContext)

        moved_path = Path(result.final_destination_path)
        assert moved_path.exists()
        assert moved_path.name == "test (1).txt"
        assert moved_path.parent == dest_dir.absolute()
        assert existing_file.exists()  # The original conflicting file should still be there


def _context_for(source, destination):
    return FileContext(
        source_path=source,
        destination_dir=destination.parent,
        rename_files=False,
        use_vision=False,
        language_subfolders=False,
        categories=[],
        final_destination_path=destination,
    )


def test_identical_file_already_filed_is_not_duplicated(tmp_path):
    """Re-filing the same content does not create 'name (1).ext' copies."""
    source = tmp_path / "in" / "invoice.pdf"
    source.parent.mkdir()
    source.write_bytes(b"same content")
    destination = tmp_path / "out" / "invoice.pdf"
    destination.parent.mkdir()
    destination.write_bytes(b"same content")

    result = transfer_file(_context_for(source, destination), "copy")

    assert Path(result.final_destination_path) == destination
    assert sorted(p.name for p in destination.parent.iterdir()) == ["invoice.pdf"]
    assert source.exists()  # never delete the user's file on a duplicate


def test_different_content_with_same_name_gets_a_counter(tmp_path):
    """Name clashes with different content still keep both files."""
    source = tmp_path / "in" / "invoice.pdf"
    source.parent.mkdir()
    source.write_bytes(b"new")
    destination = tmp_path / "out" / "invoice.pdf"
    destination.parent.mkdir()
    destination.write_bytes(b"old")

    result = transfer_file(_context_for(source, destination), "move")

    assert Path(result.final_destination_path).name == "invoice (1).pdf"
    assert destination.read_bytes() == b"old"


def test_failed_transfer_leaves_no_placeholder(mocker, tmp_path):
    """If the move fails, the reserved destination name is released."""
    source = tmp_path / "in" / "a.pdf"
    source.parent.mkdir()
    source.write_bytes(b"x")
    destination = tmp_path / "out" / "a.pdf"
    mocker.patch("classifai.infrastructure.file_system.shutil.move", side_effect=OSError("disk full"))

    with pytest.raises(FileOperationError):
        transfer_file(_context_for(source, destination), "move")

    assert not destination.exists()
