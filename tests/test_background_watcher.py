"""
Tests for the background_watcher module.
"""

from unittest.mock import MagicMock, patch

import pytest
from returns.result import Failure, Success

from classifai.background_watcher import NewFileHandler
from classifai.core.types import FileContext


@pytest.fixture
def test_env(tmp_path):
    """Creates a temporary source and destination directory for testing."""
    source_dir = tmp_path / "source"
    source_dir.mkdir()
    dest_dir = tmp_path / "destination"
    dest_dir.mkdir()
    return source_dir, dest_dir


@pytest.fixture
def mock_file_context(test_env):
    """
    Provides a mock FileContext object that would be the result of a
    successful pipeline run.
    """
    _, dest_dir = test_env
    return FileContext(
        source_path=dest_dir / "source" / "test.txt",  # Dummy source
        destination_dir=dest_dir,
        final_destination_path=dest_dir / "final" / "test.txt",
        rename_files=False,
        use_vision=False,
        language_subfolders=False,
        categories=[],
    )


@patch("classifai.background_watcher.process_file_pipeline")
@patch("classifai.background_watcher.transfer_file")
def test_new_file_handler_move(mock_transfer, mock_process_pipeline, test_env, mock_file_context):
    """
    Tests that the NewFileHandler correctly processes a new file in 'move' mode.
    """
    # Arrange
    source_dir, dest_dir = test_env
    handler = NewFileHandler(str(dest_dir), "move", {})
    mock_process_pipeline.return_value = Success(mock_file_context)
    mock_transfer.return_value = Success(mock_file_context)

    # Act
    test_file = source_dir / "test.txt"
    test_file.write_text("content")
    handler.on_created(MagicMock(is_directory=False, src_path=str(test_file)))

    # Assert
    mock_process_pipeline.assert_called_once()
    mock_transfer.assert_called_once_with(mock_file_context, "move")


@patch("classifai.background_watcher.process_file_pipeline")
@patch("classifai.background_watcher.transfer_file")
def test_new_file_handler_copy(mock_transfer, mock_process_pipeline, test_env, mock_file_context):
    """
    Tests that the NewFileHandler correctly processes a new file in 'copy' mode.
    """
    # Arrange
    source_dir, dest_dir = test_env
    handler = NewFileHandler(str(dest_dir), "copy", {})
    mock_process_pipeline.return_value = Success(mock_file_context)
    mock_transfer.return_value = Success(mock_file_context)

    # Act
    test_file = source_dir / "test.txt"
    test_file.write_text("content")
    handler.on_created(MagicMock(is_directory=False, src_path=str(test_file)))

    # Assert
    mock_process_pipeline.assert_called_once()
    mock_transfer.assert_called_once_with(mock_file_context, "copy")


@patch("classifai.background_watcher.process_file_pipeline")
@patch("classifai.background_watcher.transfer_file")
def test_new_file_handler_failure(mock_transfer, mock_process_pipeline, test_env):
    """
    Tests that no file operation occurs if the pipeline returns a Failure.
    """
    # Arrange
    source_dir, dest_dir = test_env
    handler = NewFileHandler(str(dest_dir), "move", {})
    mock_process_pipeline.return_value = Failure("Test Failure")

    # Act
    test_file = source_dir / "test.txt"
    test_file.write_text("content")
    handler.on_created(MagicMock(is_directory=False, src_path=str(test_file)))

    # Assert
    mock_process_pipeline.assert_called_once()
    mock_transfer.assert_not_called()
