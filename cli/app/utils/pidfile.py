import os
from .config import PID_FILE


def write_pid(pid: int):
    PID_FILE.write_text(str(pid))


def read_pid():
    if PID_FILE.exists():
        return int(PID_FILE.read_text())
    return None


def remove_pid():
    if PID_FILE.exists():
        PID_FILE.unlink()
