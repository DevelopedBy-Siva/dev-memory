# app/commands/stop.py
from rich.console import Console
from app.utils.daemon import stop_daemon

console = Console()


def stop():
    try:
        stop_daemon()
        console.print("[yellow]DevMemory stopped[/yellow]")
    except RuntimeError:
        console.print("[red]DevMemory is not running[/red]")
