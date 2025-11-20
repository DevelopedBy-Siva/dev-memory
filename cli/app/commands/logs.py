from rich.console import Console
from app.utils.config import LOG_FILE

console = Console()


def logs(lines: int = 100):
    if not LOG_FILE.exists():
        console.print("[yellow]No logs yet.[/yellow]")
        return

    content = LOG_FILE.read_text().splitlines()
    for line in content[-lines:]:
        console.print(line)
