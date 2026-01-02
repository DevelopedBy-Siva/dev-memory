import os
import sys
import time
import signal
import logging
from pathlib import Path

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

from devmemory_daemon.git_engine import commit_and_capture_patch, devmemory_root
from devmemory_daemon.monitor_config import (
    should_ignore_path,
    DebounceManager,
)
from app.utils.config import LOG_FILE

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


class OptimizedEventHandler(FileSystemEventHandler):
    def __init__(self, project_root: Path):
        super().__init__()
        self.project_root = project_root
        self.debouncer = DebounceManager(debounce_ms=500)

        self.total_events = 0
        self.ignored_events = 0
        self.processed_events = 0

    def on_any_event(self, event):
        self.total_events += 1

        if event.is_directory:
            self.ignored_events += 1
            return

        src = Path(event.src_path)

        if should_ignore_path(src, self.project_root):
            self.ignored_events += 1
            return

        self.debouncer.add_event(str(src))
        self.processed_events += 1

    def get_stats(self):
        return {
            "total_events": self.total_events,
            "ignored_events": self.ignored_events,
            "processed_events": self.processed_events,
            "ignore_rate": (self.ignored_events / max(self.total_events, 1)) * 100,
        }


def main():
    if len(sys.argv) < 2:
        print("run_daemon requires project root", file=sys.stderr)
        sys.exit(1)

    project_root = Path(sys.argv[1]).resolve()
    os.chdir(project_root)

    try:
        os.nice(10)
    except Exception:
        pass

    log.info(f"Starting DevMemory (optimized mode) for {project_root}")

    handler = OptimizedEventHandler(project_root)
    observer = Observer()
    observer.schedule(handler, str(project_root), recursive=True)
    observer.start()

    debounce_seconds = float(os.environ.get("DEVMEMORY_DEBOUNCE", "1.0"))
    idle_snapshot_seconds = float(os.environ.get("DEVMEMORY_IDLE_SNAPSHOT", "120"))
    stats_interval = 300

    last_snapshot_time = 0.0
    last_stats_time = time.time()

    try:
        while running:
            now = time.time()

            if handler.debouncer.should_process():
                pending_files = handler.debouncer.get_pending_files()

                log.info(f"Processing {len(pending_files)} changed files")

                try:
                    did_snapshot = commit_and_capture_patch(project_root)
                    if did_snapshot:
                        log.info(
                            f"✓ Snapshot captured ({len(pending_files)} files changed)"
                        )
                        last_snapshot_time = now
                    else:
                        log.info("No substantive changes to commit")
                except Exception as e:
                    log.exception(f"Error during snapshot: {e}")

            if last_snapshot_time == 0.0:
                last_snapshot_time = now
            elif now - last_snapshot_time >= idle_snapshot_seconds:
                try:
                    did_snapshot = commit_and_capture_patch(project_root)
                    if did_snapshot:
                        log.info("Periodic idle snapshot captured")
                    last_snapshot_time = now
                except Exception as e:
                    log.exception(f"Error during periodic snapshot: {e}")

            if now - last_stats_time >= stats_interval:
                stats = handler.get_stats()
                log.info(
                    f"Stats: {stats['total_events']} events, "
                    f"{stats['ignore_rate']:.1f}% ignored, "
                    f"{stats['processed_events']} processed"
                )
                last_stats_time = now

            time.sleep(0.5)

    finally:
        observer.stop()
        observer.join()

        stats = handler.get_stats()
        log.info(f"Final stats: {stats}")
        log.info("DevMemory daemon stopped cleanly")


if __name__ == "__main__":
    main()
