import typer
from rich.console import Console
from rich.panel import Panel
from pathlib import Path
from datetime import datetime

from app.utils.pidfile import get_running_project_root
from devmemory_daemon.git_engine import patches_dir

console = Console()
diff_app = typer.Typer(help="Show DevMemory snapshot diffs.")


def _load_patches(project_root: Path):
    pd = patches_dir(project_root)
    if not pd.exists():
        return []

    entries = []
    for f in pd.glob("*.patch"):
        name = f.name
        try:
            ts_str, commit = name.split("_", 1)
            commit = commit.replace(".patch", "")
            ts = datetime.strptime(ts_str, "%Y%m%dT%H%M%SZ")
            entries.append((ts, commit, f))
        except Exception:
            continue

    entries.sort(key=lambda x: x[0], reverse=True)
    return entries


@diff_app.command("show")
def diff_show(patch_id: str):
    """Show full patch for specific commit hash prefix."""

    project_root = get_running_project_root()
    if not project_root:
        console.print("[red]DevMemory is not running.[/red]")
        raise typer.Exit(1)

    patches = _load_patches(project_root)

    for ts, commit, path in patches:
        if commit.startswith(patch_id):
            console.print(Panel(path.read_text(), title=f"{ts} | {commit}"))
            return

    console.print("[red]Patch not found.[/red]")


@diff_app.command("last")
def diff_last(n: int = 1):
    """Show last N diffs."""

    project_root = get_running_project_root()
    if not project_root:
        console.print("[red]DevMemory is not running.[/red]")
        raise typer.Exit(1)

    patches = _load_patches(project_root)
    if not patches:
        console.print("[yellow]No patches yet.[/yellow]")
        return

    for ts, commit, p in patches[:n]:
        console.print(Panel(p.read_text(), title=f"{ts} | {commit}"))


@diff_app.command("from-date")
def diff_from(date: str):
    """Show diffs from a specific date (YYYY-MM-DD)."""

    project_root = get_running_project_root()
    if not project_root:
        console.print("[red]DevMemory is not running.[/red]")
        raise typer.Exit(1)

    try:
        start = datetime.strptime(date, "%Y-%m-%d")
    except:
        console.print("[red]Invalid date format.[/red]")
        raise typer.Exit(1)

    patches = _load_patches(project_root)
    selected = [p for p in patches if p[0] >= start]

    if not selected:
        console.print("[yellow]No patches in this timeframe.[/yellow]")
        return

    for ts, commit, p in selected:
        console.print(Panel(p.read_text(), title=f"{ts} | {commit}"))
