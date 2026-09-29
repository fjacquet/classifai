"""
Tests for the background_watcher module.
"""

import queue

import pytest

from classifai.background_watcher import NewFileHandler, run_worker, wait_until_stable
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
    """A FileContext as returned by a successful pipeline run."""
    _, dest_dir = test_env
    return FileContext(
        source_path=dest_dir / "source" / "test.txt",
        destination_dir=dest_dir,
        final_destination_path=dest_dir / "final" / "test.txt",
        rename_files=False,
        use_vision=False,
        language_subfolders=False,
        categories=[],
    )


def _handler(test_env, mode="move"):
    source_dir, dest_dir = test_env
    return NewFileHandler(source_dir, dest_dir, mode, {}, queue.Queue())


@pytest.fixture
def stable(mocker):
    """Files are considered fully written immediately."""
    return mocker.patch("classifai.background_watcher.wait_until_stable", return_value=True)


@pytest.mark.parametrize("mode", ["move", "copy"])
def test_process_file_transfers(mocker, test_env, mock_file_context, stable, mode):
    """A processed file is transferred with the configured mode."""
    handler = _handler(test_env, mode)
    mock_pipeline = mocker.patch(
        "classifai.background_watcher.process_file_pipeline", return_value=mock_file_context
    )
    mock_transfer = mocker.patch("classifai.background_watcher.transfer_file", return_value=mock_file_context)
    test_file = test_env[0] / "test.txt"
    test_file.write_text("content")

    handler.process_file(test_file)

    mock_pipeline.assert_called_once()
    mock_transfer.assert_called_once_with(mock_file_context, mode)


def test_process_file_failure_skips_transfer(mocker, test_env, stable):
    """No file operation occurs if the pipeline returns None."""
    handler = _handler(test_env)
    mocker.patch("classifai.background_watcher.process_file_pipeline", return_value=None)
    mock_transfer = mocker.patch("classifai.background_watcher.transfer_file")
    test_file = test_env[0] / "test.txt"
    test_file.write_text("content")

    handler.process_file(test_file)

    mock_transfer.assert_not_called()


def test_process_file_waits_for_complete_write(mocker, test_env):
    """Files that never stabilise (or vanish) are not classified."""
    handler = _handler(test_env)
    mocker.patch("classifai.background_watcher.wait_until_stable", return_value=False)
    mock_pipeline = mocker.patch("classifai.background_watcher.process_file_pipeline")

    handler.process_file(test_env[0] / "partial.pdf")

    mock_pipeline.assert_not_called()


def test_events_are_queued_not_processed_inline(mocker, test_env):
    """The observer thread only enqueues; slow LLM work happens on the worker."""
    handler = _handler(test_env)
    mock_pipeline = mocker.patch("classifai.background_watcher.process_file_pipeline")
    created = test_env[0] / "invoice.pdf"
    created.write_text("x")
    renamed = test_env[0] / "download.pdf"
    renamed.write_text("x")

    handler.on_created(mocker.MagicMock(is_directory=False, src_path=str(created)))
    handler.on_moved(mocker.MagicMock(is_directory=False, src_path="x.crdownload", dest_path=str(renamed)))

    mock_pipeline.assert_not_called()
    assert [handler.queue.get_nowait(), handler.queue.get_nowait()] == [created, renamed]


@pytest.mark.parametrize("name", [".DS_Store", "~$report.docx", "file.pdf.part", "movie.crdownload", "x.xyz"])
def test_temporary_hidden_and_unsupported_files_are_ignored(mocker, test_env, name):
    """Temp, hidden, lock and unsupported files never reach the queue."""
    handler = _handler(test_env)
    path = test_env[0] / name
    path.write_text("x")

    handler.on_created(mocker.MagicMock(is_directory=False, src_path=str(path)))

    assert handler.queue.empty()


def test_files_in_destination_are_ignored(mocker, tmp_path):
    """Copying into a destination inside the watched folder must not loop."""
    source_dir = tmp_path
    dest_dir = tmp_path / "sorted"
    filed = dest_dir / "fr" / "a.pdf"
    filed.parent.mkdir(parents=True)
    filed.write_text("x")
    handler = NewFileHandler(source_dir, dest_dir, "copy", {}, queue.Queue())

    handler.on_created(mocker.MagicMock(is_directory=False, src_path=str(filed)))

    assert handler.queue.empty()


def test_wait_until_stable(mocker, tmp_path):
    """Stable once the size stops changing; False if the file disappears."""
    mocker.patch("classifai.background_watcher.time.sleep")
    path = tmp_path / "a.pdf"
    path.write_text("done")

    assert wait_until_stable(path) is True
    assert wait_until_stable(tmp_path / "missing.pdf") is False


def test_worker_survives_errors(mocker, test_env):
    """One failing file does not stop the watcher."""
    handler = _handler(test_env)
    process = mocker.patch.object(handler, "process_file", side_effect=[RuntimeError("bug"), None])
    handler.queue.put(test_env[0] / "a.pdf")
    handler.queue.put(test_env[0] / "b.pdf")
    handler.queue.put(None)

    run_worker(handler)

    assert process.call_count == 2
