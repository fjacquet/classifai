"""
Watches a directory for new files and processes them.
"""

import time
from pathlib import Path
from typing import Any

from loguru import logger
from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

from classifai.config import app_config
from classifai.core.rules import RulesEngine
from classifai.infrastructure.file_system import transfer_file
from classifai.infrastructure.knowledge import KnowledgeBase
from classifai.pipeline import process_file_pipeline


class NewFileHandler(FileSystemEventHandler):
    def __init__(self, destination_dir: str, mode: str, scan_config: dict[str, Any]):
        self.destination_dir = destination_dir
        self.mode = mode
        self.scan_config = scan_config
        self.rules_engine = RulesEngine(app_config.rules)
        self.knowledge_base = KnowledgeBase(app_config.debitors)

    def on_created(self, event):
        if not event.is_directory:
            logger.info(f"New file detected: {event.src_path}")
            file_path = Path(event.src_path)

            # Create a fresh scan_config for each file to avoid side effects
            current_scan_config = {
                **self.scan_config,
                "dest_dir_str": self.destination_dir,
                "categories": app_config.categories,
            }

            result = process_file_pipeline(
                file_path,
                current_scan_config,
                self.rules_engine,
                self.knowledge_base,
            )

            result.bind(
                lambda context: transfer_file(context, self.mode).map(
                    lambda final_context: logger.info(
                        f"Moved '{file_path.name}' to '{final_context.final_destination_path}'"
                    )
                    if self.mode == "move"
                    else logger.info(f"Copied '{file_path.name}' to '{final_context.final_destination_path}'")
                )
            ).alt(lambda error: logger.error(f"Failed to process {file_path.name}: {error}"))


def start_watcher(source_dir: Path, destination_dir: Path, mode: str, **kwargs):
    """
    Starts the background watcher.
    """
    logger.info(f"Starting watcher on '{source_dir}'...")
    event_handler = NewFileHandler(str(destination_dir), mode, kwargs)
    observer = Observer()
    observer.schedule(event_handler, str(source_dir), recursive=True)
    observer.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()
