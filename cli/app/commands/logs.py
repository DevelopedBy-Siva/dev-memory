from rich.console import Console
from app.utils.config import LOG_FILE

console = Console()


def logs():
    if LOG_FILE.exists():
        console.print(LOG_FILE.read_text())
    else:
        console.print("[red]No logs found[/red]")
