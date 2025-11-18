import time
import signal
import sys
from rich.console import Console

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
    while running:
        # For now, just sleep. Later we add watchers here.
        time.sleep(1)

    console.log("Daemon stopped cleanly.")


if __name__ == "__main__":
    main()
