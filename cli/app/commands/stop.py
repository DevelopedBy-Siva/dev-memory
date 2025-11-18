from rich.console import Console
from app.utils.daemon import stop_daemon

console = Console()


def stop():
    try:
        stop_daemon()
        console.print("[yellow]DevMemory daemon stopped[/yellow]")
    except RuntimeError as e:
        console.print(f"[red]{str(e)}[/red]")
