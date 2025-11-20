import typer
from rich.console import Console
from pathlib import Path

from app.utils.daemon import start_daemon, is_running

console = Console()


def start(project_path: str = "."):
    running, root, pid = is_running()
    if running:
        console.print(f"DevMemory is already running in {root} (PID {pid})")
        return

    root = Path(project_path).resolve()
    console.print(f"Project root: {root}")

    confirm = input("Start DevMemory here? [Y/n]: ").strip().lower() or "y"
    if confirm != "y":
        console.print("[yellow]Aborted.[/yellow]")
        return

    start_daemon(str(root))
