import typer
from rich.console import Console
from pathlib import Path
import json
from datetime import datetime

from app.utils.pidfile import get_running_project_root
from devmemory_daemon.git_engine import devmemory_root

console = Console()
note_app = typer.Typer(help="Add notes to current session")


@note_app.command("add")
def add_note(note: str):
    project_root = get_running_project_root()
    if not project_root:
        console.print("[red]DevMemory is not running.[/red]")
        console.print("Start it with: [bold]devmemory start[/bold]")
        raise typer.Exit(1)

    session_file = devmemory_root(project_root) / "current_session.json"

    if not session_file.exists():
        console.print("[red]No active session found.[/red]")
        raise typer.Exit(1)

    session_data = json.loads(session_file.read_text())

    session_data["notes"].append(
        {
            "text": note,
            "timestamp": datetime.now().isoformat(),
            "time": datetime.now().strftime("%H:%M:%S"),
        }
    )

    session_file.write_text(json.dumps(session_data, indent=2))

    console.print(f"[green]✓ Note added:[/green] {note}")


@note_app.command("list")
def list_notes():

    project_root = get_running_project_root()
    if not project_root:
        console.print("[red]DevMemory is not running.[/red]")
        raise typer.Exit(1)

    session_file = devmemory_root(project_root) / "current_session.json"

    if not session_file.exists():
        console.print("[yellow]No active session.[/yellow]")
        return

    session_data = json.loads(session_file.read_text())

    console.print(
        f"\n[bold cyan]Session Context:[/bold cyan] {session_data.get('context', 'None')}"
    )
    console.print(f"[dim]Started: {session_data['started_at']}[/dim]\n")

    if not session_data.get("notes"):
        console.print("[yellow]No notes yet.[/yellow]")
        return

    console.print("[bold]Notes:[/bold]")
    for i, note in enumerate(session_data["notes"], 1):
        console.print(f"  {i}. [{note['time']}] {note['text']}")
