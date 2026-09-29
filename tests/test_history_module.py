import json
from pathlib import Path

import pytest

from classifai.infrastructure.history import (
    get_last_operation,
    log_operation,
    remove_last_operation,
)


@pytest.fixture(autouse=True)
def mock_history_file(mocker, tmp_path: Path):
    """
    Mocks the HISTORY_FILE path to use a temporary file for all tests.
    """
    mock_path = tmp_path / "history.json"
    mocker.patch("classifai.infrastructure.history.HISTORY_FILE", mock_path)
    return mock_path


def test_log_and_get_history(mock_history_file: Path):
    """
    Tests logging an operation and retrieving it.
    """
    log_operation("move", "/src/file.txt", "/dest/file.txt")
    log_operation("copy", "/src/image.jpg", "/dest/image.jpg")

    last_op = get_last_operation()
    assert last_op is not None
    assert last_op["operation"] == "copy"
    assert last_op["source"] == "/src/image.jpg"

    with open(mock_history_file) as f:
        history = json.load(f)
    assert len(history) == 2


def test_remove_last_operation(mock_history_file: Path):
    """
    Tests removing the last operation from the history.
    """
    log_operation("move", "/src/file.txt", "/dest/file.txt")
    log_operation("copy", "/src/image.jpg", "/dest/image.jpg")

    remove_last_operation()

    last_op = get_last_operation()
    assert last_op is not None
    assert last_op["operation"] == "move"

    remove_last_operation()
    assert get_last_operation() is None


def test_empty_history(mock_history_file: Path):
    """
    Tests that functions handle an empty or non-existent history file.
    """
    assert get_last_operation() is None
    remove_last_operation()  # Should not raise an error


def test_history_write_is_atomic(mocker, tmp_path):
    """A crash while writing history must leave the previous history intact for undo."""
    from classifai.infrastructure import history

    history_file = tmp_path / "history.json"
    mocker.patch.object(history, "HISTORY_FILE", history_file)
    history.log_operation("move", "/a", "/b")
    mocker.patch("classifai.infrastructure.history.json.dumps", side_effect=RuntimeError("boom"))

    with pytest.raises(RuntimeError):
        history.log_operation("move", "/c", "/d")

    assert history.get_last_operation() == {"operation": "move", "source": "/a", "destination": "/b"}
