from rich.console import Console
from app.utils.daemon import is_running

console = Console()


def status():
    running, root, pid = is_running()

    if running:
        console.print(f"[green]DevMemory is running in {root} (PID {pid})[/green]")
    else:
        console.print("[red]DevMemory is not running[/red]")
