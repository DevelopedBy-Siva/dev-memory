import os
from .config import PID_FILE


def pid_alive(pid: int) -> bool:
    try:
        os.kill(pid, 0)
        # reject stale detached daemons
        if os.getppid() == 1:
            return False
        return True
    except OSError:
        return False


def write_pid(pid: int, project_root: str):
    with PID_FILE.open("w") as f:
        f.write(f"{pid}:{project_root}")


def remove_pid():
    if PID_FILE.exists():
        PID_FILE.unlink()


def read_pid():
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
