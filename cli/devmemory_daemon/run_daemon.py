import time
import signal
import sys
from rich.console import Console
from pathlib import Path
from devmemory_daemon.fs_watcher import start_fs_watcher
from devmemory_daemon.snapshot_store import write_snapshot

console = Console()

running = True


def handle_signal(sig, frame):
    global running
    console.log("DevMemory daemon shutting down...")
    running = False


signal.signal(signal.SIGTERM, handle_signal)
signal.signal(signal.SIGINT, handle_signal)


def main():
    console.log("DevMemory daemon started.")

    project_root = Path.cwd()

    # Start filesystem watcher
    observer = start_fs_watcher(project_root, write_snapshot)
    console.log("FS Watcher started...")

    while running:
        time.sleep(1)

    observer.stop()
    observer.join()

    console.log("Daemon stopped cleanly.")
