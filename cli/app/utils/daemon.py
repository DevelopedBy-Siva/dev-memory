import subprocess
import sys
import os
from .pidfile import write_pid, read_pid, remove_pid
from .config import ensure_dirs, LOG_FILE


def start_daemon():
    ensure_dirs()

    if read_pid():
        raise RuntimeError("Daemon already running")

    log = open(LOG_FILE, "a")

    # Launch daemon in background
    process = subprocess.Popen(
        [sys.executable, "-m", "devmemory_daemon.run_daemon"],
        stdout=log,
        stderr=log,
        start_new_session=True,
    )

    write_pid(process.pid)
    return process.pid


def stop_daemon():
    pid = read_pid()
    if not pid:
        raise RuntimeError("Daemon not running")

    try:
        os.kill(pid, 15)
    except ProcessLookupError:
        pass

    remove_pid()


def is_running():
    pid = read_pid()
    if not pid:
        return False
    try:
        os.kill(pid, 0)
        return True
    except:
        return False
