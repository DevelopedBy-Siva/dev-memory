from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from pathlib import Path
import time
from datetime import datetime
import json


class FSWatcher(FileSystemEventHandler):
    """File system watcher that creates snapshot events on file changes."""

    def __init__(self, project_root: Path, snapshot_callback):
        super().__init__()
        self.project_root = Path(project_root)
        self.snapshot_callback = snapshot_callback

    def on_modified(self, event):
        if not event.is_directory:
            self._record("modified", event.src_path)

    def on_created(self, event):
        if not event.is_directory:
            self._record("created", event.src_path)

    def on_deleted(self, event):
        if not event.is_directory:
            self._record("deleted", event.src_path)

    def on_moved(self, event):
        if not event.is_directory:
            self._record("moved", event.dest_path)

    def _record(self, change_type, file_path):
        rel_path = str(Path(file_path).relative_to(self.project_root))

        event = {
            "type": "file_event",
            "change": change_type,
            "file": rel_path,
            "timestamp": datetime.utcnow().isoformat() + "Z",
        }

        self.snapshot_callback(event, self.project_root)


def start_fs_watcher(project_root, snapshot_callback):
    event_handler = FSWatcher(project_root, snapshot_callback)
    observer = Observer()
    observer.schedule(event_handler, project_root, recursive=True)
    observer.start()
    return observer
