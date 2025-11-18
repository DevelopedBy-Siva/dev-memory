from pathlib import Path

DEVMEMORY_HOME = Path.home() / ".devmemory"
PID_FILE = DEVMEMORY_HOME / "daemon.pid"
LOG_FILE = DEVMEMORY_HOME / "daemon.log"


def ensure_dirs():
    DEVMEMORY_HOME.mkdir(parents=True, exist_ok=True)
