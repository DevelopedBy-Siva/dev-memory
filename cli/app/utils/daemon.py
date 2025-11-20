from subprocess import Popen
import sys
import os
from rich.console import Console

from .pidfile import write_pid, read_pid, remove_pid
from .config import ensure_dirs, LOG_FILE

console = Console()


def start_daemon(project_root: str) -> None:
    ensure_dirs()

    pid, running_root = read_pid()
    if pid is not None:
        console.print(f"DevMemory is already running in {running_root} (PID {pid}).")
        return

    cmd = [
        sys.executable,
        "-m",
        "devmemory_daemon.run_daemon",
        project_root,
    ]

    with open(LOG_FILE, "a") as log:
        process = Popen(cmd, stdout=log, stderr=log, start_new_session=False)

    write_pid(process.pid, project_root)
    console.print("[green]DevMemory daemon started[/green]")


def stop_daemon() -> None:
    pid, _ = read_pid()
    if pid is None:
        raise RuntimeError("DevMemory not running")

    try:
        os.kill(pid, 15)
    except ProcessLookupError:
        pass

    remove_pid()


def is_running():
    pid, root = read_pid()
    return pid is not None, root, pid
