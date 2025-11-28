import typer
from rich.console import Console
from pathlib import Path
import json
from datetime import datetime

from app.utils.daemon import start_daemon, is_running
from devmemory_daemon.git_engine import devmemory_root

console = Console()


def start(project_path: str = "."):
    running, root, pid = is_running()
    if running:
        console.print(f"DevMemory is already running in {root} (PID {pid})")
        return

    root = Path(project_path).resolve()
    console.print(f"[cyan]Project root: {root}[/cyan]")

    confirm = input("Start DevMemory here? [Y/n]: ").strip().lower() or "y"
    if confirm != "y":
        console.print("[yellow]Aborted.[/yellow]")
        return

    console.print("\n[bold cyan]Session Context (Optional but Recommended)[/bold cyan]")
    console.print(
        "[dim]Tell DevMemory what you're working on. This helps AI provide better summaries.[/dim]"
    )
    context = input("What are you working on? (press Enter to skip): ").strip()

    if not context:
        console.print(
            "[yellow]No context provided. DevMemory will work with code analysis only.[/yellow]"
        )
        context = None

    session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    session_data = {
        "session_id": session_id,
        "started_at": datetime.now().isoformat(),
        "context": context,
        "notes": [],
        "status": "active",
    }

    dm_root = devmemory_root(root)
    dm_root.mkdir(parents=True, exist_ok=True)
    session_file = dm_root / "current_session.json"
    session_file.write_text(json.dumps(session_data, indent=2))

    start_daemon(str(root))

    if context:
        console.print(f"\n[green]✓ Session started with context: '{context}'[/green]")
    else:
        console.print(f"\n[green]✓ Session started[/green]")

    console.print('[dim]Add notes anytime: devmemory note "your note here"[/dim]')
    console.print("[dim]Open dashboard (optional): devmemory dashboard run[/dim]")
