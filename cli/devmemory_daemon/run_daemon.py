import os
import sys
import time
import signal
import logging
from pathlib import Path

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

from devmemory_daemon.git_engine import commit_and_capture_patch, devmemory_root
from app.utils.config import LOG_FILE  # global ~/.devmemory/daemon.log

logging.basicConfig(
    filename=str(LOG_FILE),
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)

log = logging.getLogger("devmemory-daemon")
running = True


def handle_signal(sig, frame):
    global running
    log.info("Stopping DevMemory daemon...")
    running = False


signal.signal(signal.SIGINT, handle_signal)
signal.signal(signal.SIGTERM, handle_signal)
signal.signal(signal.SIGHUP, handle_signal)


IGNORE_DIRS = {".git", ".devmemory", "__pycache__", "node_modules", "venv", ".venv"}


def _is_ignored(path: Path, project_root: Path) -> bool:
    try:
        rel = path.relative_to(project_root)
    except ValueError:
        return True

    # Ignore directories like node_modules, .git, etc.
    parts = rel.parts
    return any(part in IGNORE_DIRS for part in parts)


class DevMemoryEventHandler(FileSystemEventHandler):
    def __init__(self, project_root: Path):
        super().__init__()
        self.project_root = project_root
        self.last_event_ts = 0.0
        self.has_pending_change = False

    def on_any_event(self, event):
        src = Path(event.src_path)
        if _is_ignored(src, self.project_root):
            return

        # Mark that a relevant change happened
        self.last_event_ts = time.time()
        self.has_pending_change = True


def main():
    if len(sys.argv) < 2:
        print("run_daemon requires project root", file=sys.stderr)
        sys.exit(1)

    project_root = Path(sys.argv[1]).resolve()
    os.chdir(project_root)

    # Lower priority so it doesn't fight with your editor/shell
    try:
        os.nice(10)
    except Exception:
        pass

    log.info(f"Starting DevMemory (watch mode) for {project_root}")

    handler = DevMemoryEventHandler(project_root)
    observer = Observer()
    observer.schedule(handler, str(project_root), recursive=True)
    observer.start()

    debounce_seconds = float(os.environ.get("DEVMEMORY_DEBOUNCE", "1.0"))
    idle_snapshot_seconds = float(os.environ.get("DEVMEMORY_IDLE_SNAPSHOT", "120"))

    last_snapshot_time = 0.0

    try:
        while running:
            now = time.time()

            # 1) If we have pending changes and no new events in the last debounce window,
            #    take a snapshot.
            if handler.has_pending_change:
                if now - handler.last_event_ts >= debounce_seconds:
                    try:
                        did_snapshot = commit_and_capture_patch(project_root)
                        if did_snapshot:
                            log.info("Snapshot captured after file change.")
                            last_snapshot_time = now
                        else:
                            log.info("No changes to commit on file change.")
                    except Exception as e:
                        log.exception(f"Error during snapshot: {e}")
                    finally:
                        handler.has_pending_change = False

            # 2) Optional: periodic snapshot in case of long-lived edits that don't trigger writes
            if last_snapshot_time == 0.0:
                last_snapshot_time = now
            elif now - last_snapshot_time >= idle_snapshot_seconds:
                try:
                    did_snapshot = commit_and_capture_patch(project_root)
                    if did_snapshot:
                        log.info("Periodic idle snapshot captured.")
                    else:
                        log.info("Periodic snapshot: no changes.")
                except Exception as e:
                    log.exception(f"Error during periodic snapshot: {e}")
                finally:
                    last_snapshot_time = now

            time.sleep(0.5)

    finally:
        observer.stop()
        observer.join()
        log.info("DevMemory daemon stopped cleanly.")


if __name__ == "__main__":
    main()
