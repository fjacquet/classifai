"""
Watches a directory for new files and processes them.

The watchdog observer thread only filters and enqueues paths; a single worker
thread waits for each file to be fully written, classifies it and transfers it.
"""

import queue
import threading
import time
from pathlib import Path
from typing import Any

from loguru import logger
from watchdog.events import FileSystemEvent, FileSystemEventHandler
from watchdog.observers import Observer

from classifai.config import app_config
from classifai.core.rules import RulesEngine
from classifai.exceptions import FileOperationError
from classifai.infrastructure.file_system import transfer_file
from classifai.pipeline import is_in_destination, is_supported_file, process_file_pipeline

# Suffixes used by browsers, scanners and sync tools for files still being written
TEMPORARY_SUFFIXES = (".tmp", ".part", ".partial", ".crdownload", ".download")
STABLE_POLL_SECONDS = 1.0
STABLE_CHECKS = 2  # consecutive polls with an unchanged size
STABLE_TIMEOUT_SECONDS = 300


def wait_until_stable(path: Path) -> bool:
    """
    Wait until *path* stops growing.

    Returns:
        True once the size is unchanged for STABLE_CHECKS polls,
        False if the file disappears or keeps changing until the timeout.
    """
    deadline = time.monotonic() + STABLE_TIMEOUT_SECONDS
    last_size, unchanged = -1, 0
    while time.monotonic() < deadline:
        try:
            size = path.stat().st_size
        except FileNotFoundError:
            return False
        unchanged = unchanged + 1 if size == last_size else 0
        if unchanged >= STABLE_CHECKS:
            return True
        last_size = size
        time.sleep(STABLE_POLL_SECONDS)
    return False


class NewFileHandler(FileSystemEventHandler):
    """Filters filesystem events and queues new files for the worker."""

    def __init__(
        self,
        source_dir: Path,
        destination_dir: Path,
        mode: str,
        scan_config: dict[str, Any],
        work_queue: "queue.Queue[Path | None]",
    ):
        self.source_dir = Path(source_dir)
        self.destination_dir = Path(destination_dir)
        self.mode = mode
        self.scan_config = scan_config
        self.queue = work_queue
        self.rules_engine = RulesEngine(app_config.rules)

    def on_created(self, event: FileSystemEvent) -> None:
        if not event.is_directory:
            self._enqueue(Path(str(event.src_path)))

    def on_moved(self, event: FileSystemEvent) -> None:
        # "download to a temp name, then rename" shows up as a move
        if not event.is_directory:
            self._enqueue(Path(str(event.dest_path)))

    def _enqueue(self, path: Path) -> None:
        if path.name.lower().endswith(TEMPORARY_SUFFIXES) or not is_supported_file(path):
            return
        if is_in_destination(path, self.source_dir, self.destination_dir):
            return
        logger.info(f"New file detected: {path}")
        self.queue.put(path)

    def process_file(self, file_path: Path) -> None:
        """Classify and transfer one file once it is fully written."""
        if not wait_until_stable(file_path):
            logger.warning(f"Skipping {file_path.name}: file vanished or never finished writing")
            return

        current_scan_config = {
            **self.scan_config,
            "dest_dir_str": str(self.destination_dir),
            "categories": app_config.categories,
        }
        context = process_file_pipeline(file_path, current_scan_config, self.rules_engine)
        if context is None:
            logger.error(f"Failed to process {file_path.name}")
            return

        try:
            final_context = transfer_file(context, self.mode)
            verb = "Moved" if self.mode == "move" else "Copied"
            logger.info(f"{verb} '{file_path.name}' to '{final_context.final_destination_path}'")
        except FileOperationError as e:
            logger.error(f"Failed to transfer {file_path.name}: {e}")


def run_worker(handler: NewFileHandler) -> None:
    """Process queued files until a None sentinel is received."""
    while (path := handler.queue.get()) is not None:
        try:
            handler.process_file(path)
        except Exception:
            logger.exception(f"Unexpected error while handling {path}")


def start_watcher(source_dir: Path, destination_dir: Path, mode: str, scan_config: dict[str, Any]):
    """
    Starts the background watcher.

    Args:
        source_dir: Directory to watch
        destination_dir: Root of the classified tree
        mode: "move" or "copy"
        scan_config: Pipeline options (rename_files, use_vision, language_subfolders,
            ollama_model, ollama_url)
    """
    logger.info(f"Starting watcher on '{source_dir}'...")
    work_queue: queue.Queue[Path | None] = queue.Queue()
    event_handler = NewFileHandler(source_dir, destination_dir, mode, scan_config, work_queue)
    worker = threading.Thread(target=run_worker, args=(event_handler,), daemon=True)
    worker.start()

    observer = Observer()
    observer.schedule(event_handler, str(source_dir), recursive=True)
    observer.start()
    try:
        while observer.is_alive():
            observer.join(timeout=1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()
    work_queue.put(None)
    worker.join()
