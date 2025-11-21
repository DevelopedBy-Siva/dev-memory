import os
import sys
import time
import signal
import logging
from pathlib import Path

from devmemory_daemon.git_engine import commit_and_capture_patch
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


def main():
    if len(sys.argv) < 2:
        print("run_daemon requires project root", file=sys.stderr)
        sys.exit(1)

    project_root = Path(sys.argv[1]).resolve()
    os.chdir(project_root)

    log.info(f"Starting DevMemory for {project_root}")

    while running:
        try:
            commit_and_capture_patch(project_root)
        except Exception as e:
            log.exception(f"Error during snapshot: {e}")
        time.sleep(2)

    log.info("DevMemory daemon stopped cleanly.")


if __name__ == "__main__":
    main()
