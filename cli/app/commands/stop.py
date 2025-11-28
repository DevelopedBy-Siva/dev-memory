from rich.console import Console
import json
from datetime import datetime

from app.utils.daemon import stop_daemon
from app.utils.pidfile import get_running_project_root
from devmemory_daemon.git_engine import devmemory_root

console = Console()


def stop():
    project_root = get_running_project_root()

    if not project_root:
        console.print("[red]DevMemory is not running[/red]")
        return

    # Archive current session (existing code...)
    session_file = devmemory_root(project_root) / "current_session.json"

    if session_file.exists():
        session_data = json.loads(session_file.read_text())
        session_data["stopped_at"] = datetime.now().isoformat()
        session_data["status"] = "completed"

        sessions_dir = devmemory_root(project_root) / "sessions"
        sessions_dir.mkdir(exist_ok=True)

        archive_file = sessions_dir / f"{session_data['session_id']}.json"
        archive_file.write_text(json.dumps(session_data, indent=2))

        session_file.unlink()

        console.print(f"[cyan]Session archived: {session_data['session_id']}[/cyan]")

    try:
        stop_daemon()
        console.print("[yellow]DevMemory daemon stopped[/yellow]")
    except RuntimeError:
        console.print("[red]DevMemory daemon is not running[/red]")
