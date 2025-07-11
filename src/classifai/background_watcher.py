"""
Background watcher for ClassifAI.

This module uses the watchdog library to monitor a directory for new files
and trigger the classification process automatically.
"""

import time

from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

from classifai.classifai_app import process_file
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

            # This is a simplified version of the run command's logic
            # It won't support embedding mode for now to keep it simple
            categories = [
                "Documents",
                "Images",
                "Videos",
                "Audio",
                "Archives",
                "Scripts",
                "Misc",
            ]
            category_embeddings = {}

            result = process_file(
                event.src_path,
                self.destination_dir,
                self.classification_mode,
                None,  # No embedding model
                self.kwargs.get("rename_files", False),
                self.kwargs.get("use_vision", False),
                self.kwargs.get("language_subfolders", False),
                logger,
                categories,
                category_embeddings,
            )

            if result:
                file, category, dest_path, lang, meta = result
                dest_dir = dest_path.parent
                if self.mode == "move":
                    move_file(
                        str(file.absolute()),
                        str(dest_dir.parent),
                        meta,
                        lang if self.kwargs.get("language_subfolders") else None,
                        dest_path.name,
                    )
                elif self.mode == "copy":
                    copy_file(
                        str(file.absolute()),
                        str(dest_dir.parent),
                        meta,
                        lang if self.kwargs.get("language_subfolders") else None,
                        dest_path.name,
                    )


def start_watcher(source_dir, destination_dir, mode, classification_mode, **kwargs):
    """
    Starts the background file watcher.
    """
    event_handler = NewFileHandler(
        destination_dir, mode, classification_mode, **kwargs
    )
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
