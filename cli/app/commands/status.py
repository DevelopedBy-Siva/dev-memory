from rich.console import Console
from app.utils.daemon import is_running, read_pid

console = Console()


def status():
    if is_running():
        console.print(f"[green]DevMemory daemon is running (PID {read_pid()})[/green]")
    else:
        console.print("[red]DevMemory daemon is not running[/red]")
