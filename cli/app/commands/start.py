import typer
from rich.console import Console
from pathlib import Path

from app.utils.daemon import start_daemon, is_running
from devmemory_daemon.project_root import find_git_root

console = Console()
app = typer.Typer()


@app.command()
def start():
    running, root, pid = is_running()

    if running:
        console.print(f"DevMemory is already running in {root} (PID {pid}).")
        return

    cwd = Path.cwd()
    detected = find_git_root(cwd)
    console.print(f"Detected project root: {detected}")

    confirm = input("Start DevMemory here? [Y/n]: ").strip().lower() or "y"
    if confirm != "y":
        console.print("Aborted.")
        return

    start_daemon(str(detected))
