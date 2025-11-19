# app/utils/pidfile.py
import os
from .config import PID_FILE
from pathlib import Path


def pid_alive(pid: int) -> bool:
    """Return True if a process with this PID exists."""
    try:
        os.kill(pid, 0)
        return True
    except OSError:
        return False


def write_pid(pid: int, project_root: str) -> None:
    PID_FILE.write_text(f"{pid}:{project_root}")


def remove_pid() -> None:
    if PID_FILE.exists():
        PID_FILE.unlink()


def read_pid():
    """Return (pid, root) or (None, None). Clean up stale files."""
    if not PID_FILE.exists():
        return None, None

    content = PID_FILE.read_text().strip()
    if ":" not in content:
        remove_pid()
        return None, None

    pid_str, root = content.split(":", 1)

    try:
        pid = int(pid_str)
    except ValueError:
        remove_pid()
        return None, None

    if not pid_alive(pid):
        remove_pid()
        return None, None

    return pid, root


def get_running_project_root() -> Path | None:
    pid, root = read_pid()
    if pid is None:
        return None
    return Path(root).resolve()
