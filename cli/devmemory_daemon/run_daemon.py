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

    # Lower priority so it doesn't fight with your editor / shell
    try:
        os.nice(10)
    except Exception:
        pass

    log.info(f"Starting DevMemory for {project_root}")

    # Adaptive interval parameters (overridable via env)
    min_interval = float(os.environ.get("DEVMEMORY_INTERVAL_MIN", "2"))
    max_interval = float(os.environ.get("DEVMEMORY_INTERVAL_MAX", "30"))
    backoff_factor = float(os.environ.get("DEVMEMORY_INTERVAL_BACKOFF", "1.7"))

    interval = min_interval

    while running:
        start = time.time()

        try:
            did_snapshot = commit_and_capture_patch(project_root)
        except Exception as e:
            did_snapshot = False
            log.exception(f"Error during snapshot: {e}")

        # Feedback: if we had a snapshot, stay fast; if not, back off
        if did_snapshot:
            interval = min_interval
            log.info(f"Snapshot captured. Reset interval to {interval:.2f}s")
        else:
            interval = min(max_interval, interval * backoff_factor)
            log.debug(f"No changes. Backing off to {interval:.2f}s")

        elapsed = time.time() - start
        sleep_for = max(0.0, interval - elapsed)
        if sleep_for > 0:
            time.sleep(sleep_for)

    log.info("DevMemory daemon stopped cleanly.")


if __name__ == "__main__":
    main()
