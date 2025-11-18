from rich.console import Console
from app.utils.daemon import start_daemon

console = Console()


def start():
    try:
        pid = start_daemon()
        console.print(f"[green]DevMemory daemon started (PID {pid})[/green]")
    except RuntimeError as e:
        console.print(f"[red]{str(e)}[/red]")
