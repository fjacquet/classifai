"""
Tests for the background_watcher module.
"""
import time
from pathlib import Path

import pytest

from classifai.background_watcher import NewFileHandler


@pytest.fixture
def test_env(tmp_path: Path):
    """
    Sets up a temporary environment for testing the watcher.
    """
    source_dir = tmp_path / "source"
    dest_dir = tmp_path / "destination"
    source_dir.mkdir()
    dest_dir.mkdir()
    return source_dir, dest_dir


def test_new_file_handler(mocker, test_env):
    """
    Tests that the NewFileHandler correctly processes a new file.
    """
    source_dir, dest_dir = test_env
    mock_process_file = mocker.patch(
        "classifai.background_watcher.process_file",
        return_value=(
            source_dir / "test.txt",
            "Documents",
            dest_dir / "Documents" / "test.txt",
            "en",
            {},
        ),
    )
    mock_move_file = mocker.patch("classifai.background_watcher.move_file")

    handler = NewFileHandler(dest_dir, "move", "completion")

    # Simulate a new file event
    new_file_path = source_dir / "test.txt"
    new_file_path.write_text("test content")

    # The event object needs a src_path attribute
    class MockEvent:
        is_directory = False
        src_path = new_file_path

    handler.on_created(MockEvent())

    # Allow some time for the event to be processed
    time.sleep(0.1)

    mock_process_file.assert_called_once()
    mock_move_file.assert_called_once()
