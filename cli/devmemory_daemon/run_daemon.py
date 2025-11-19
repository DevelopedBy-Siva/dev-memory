import time
import signal
from pathlib import Path
import logging
import sys
import os

from devmemory_daemon.fs_watcher import start_fs_watcher
from devmemory_daemon.snapshot_store import write_snapshot

LOG_DIR = Path.home() / ".devmemory"
LOG_DIR.mkdir(exist_ok=True)
LOG_FILE = LOG_DIR / "daemon.log"

logging.basicConfig(
    filename=str(LOG_FILE),
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)

log = logging.getLogger("devmemory-daemon")

running = True


def handle_signal(sig, frame):
    global running
    log.info("DevMemory daemon shutting down...")
    running = False


signal.signal(signal.SIGTERM, handle_signal)
signal.signal(signal.SIGINT, handle_signal)
signal.signal(signal.SIGHUP, handle_signal)


def main():
    if len(sys.argv) < 2:
        print("Error: run_daemon requires project root argument", file=sys.stderr)
        sys.exit(1)

    project_root = Path(sys.argv[1]).resolve()
    log.info(f"Project root detected: {project_root}")

    observer = start_fs_watcher(project_root, write_snapshot)
    log.info("FS Watcher started...")

    # Track parent PID so we know when session ends
    parent_pid = os.getppid()

    while running:
        # parent PID changed → logout / session ended
        if os.getppid() != parent_pid:
            log.info("Parent session ended — shutting down daemon...")
            break

        time.sleep(0.2)

    observer.stop()
    observer.join()

    log.info("DevMemory daemon stopped cleanly.")


if __name__ == "__main__":
    main()
