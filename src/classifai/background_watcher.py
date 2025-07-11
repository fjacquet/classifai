"""
Background watcher for ClassifAI.

This module uses the watchdog library to monitor a directory for new files
and trigger the classification process automatically.
"""

import time
from pathlib import Path

from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

from classifai.core_logic import run_scan
from classifai.file_operations_module import copy_file, move_file
from classifai.logging_module import setup_logger


class NewFileHandler(FileSystemEventHandler):
    """
    An event handler that triggers when a new file is created.
    """

    def __init__(self, destination_dir, mode, classification_mode, **kwargs):
        self.destination_dir = destination_dir
        self.mode = mode
        self.classification_mode = classification_mode
        self.kwargs = kwargs

    def on_created(self, event):
        if not event.is_directory:
            logger = setup_logger()
            logger.info(f"New file detected: {event.src_path}")

            results_df = run_scan(
                str(Path(event.src_path).parent),
                self.destination_dir,
                self.classification_mode,
                self.kwargs.get("embedding_model"),
                self.kwargs.get("rename_files", False),
                self.kwargs.get("use_vision", False),
                self.kwargs.get("language_subfolders", False),
            )

            for _, row in results_df.iterrows():
                if row["Source Path"] == event.src_path:
                    if self.mode == "move":
                        move_file(
                            row["Source Path"],
                            str(Path(row["Destination Path"]).parent.parent),
                            row["Metadata"],
                            row["Language"] if self.kwargs.get("language_subfolders") else None,
                            row["New Filename"],
                            row["Issuer"],
                        )
                    elif self.mode == "copy":
                        copy_file(
                            row["Source Path"],
                            str(Path(row["Destination Path"]).parent.parent),
                            row["Metadata"],
                            row["Language"] if self.kwargs.get("language_subfolders") else None,
                            row["New Filename"],
                            row["Issuer"],
                        )


def start_watcher(source_dir, destination_dir, mode, classification_mode, **kwargs):
    """
    Starts the background file watcher.
    """
    event_handler = NewFileHandler(destination_dir, mode, classification_mode, **kwargs)
    observer = Observer()
    observer.schedule(event_handler, source_dir, recursive=False)
    observer.start()
    print(f"Watching directory: {source_dir}")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()
