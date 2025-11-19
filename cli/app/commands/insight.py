import typer
from rich.console import Console
from rich.panel import Panel
from pathlib import Path
from datetime import datetime, timedelta
import re

from app.utils.pidfile import get_running_project_root
from devmemory_daemon.git_engine import patches_dir

console = Console()
insight_app = typer.Typer(help="Search or summarize DevMemory history.")


def _load_patches(project_root: Path):
    """Return list of (timestamp, commit_hash, full_patch_path)."""
    pd = patches_dir(project_root)
    if not pd.exists():
        return []

    entries = []
    for f in pd.glob("*.patch"):
        name = f.name  # 20250119T073455Z_<hash>.patch
        try:
            ts_str, commit = name.split("_", 1)
            commit = commit.replace(".patch", "")
            ts = datetime.strptime(ts_str, "%Y%m%dT%H%M%SZ")
            entries.append((ts, commit, f))
        except Exception:
            continue

    entries.sort(key=lambda x: x[0], reverse=True)
    return entries


@insight_app.command("last")
def insight_last():
    """Summarize the most recent snapshot patch."""

    project_root = get_running_project_root()
    if not project_root:
        console.print("[red]DevMemory is not running.[/red]")
        raise typer.Exit(1)

    patches = _load_patches(project_root)

    if not patches:
        console.print("[yellow]No patches available yet.[/yellow]")
        return

    ts, commit, path = patches[0]
    text = path.read_text()

    console.print(
        Panel(
            f"[bold]Last snapshot[/bold]\n\n{ts}\nCommit: {commit}\n\n"
            f"[dim]{text[:1500]}[/dim]\n\n(Truncated)",
            title="DevMemory Insight",
        )
    )


@insight_app.command("since")
def insight_since(interval: str):
    """Summarize patches since a time duration."""

    project_root = get_running_project_root()
    if not project_root:
        console.print("[red]DevMemory is not running.[/red]")
        raise typer.Exit(1)

    now = datetime.utcnow()
    m = re.match(r"(\d+)([dhm])$", interval)
    if not m:
        console.print("[red]Invalid interval. Use 2h, 1d, 30m[/red]")
        raise typer.Exit(1)

    val, unit = int(m.group(1)), m.group(2)

    if unit == "h":
        dt = now - timedelta(hours=val)
    elif unit == "d":
        dt = now - timedelta(days=val)
    else:
        dt = now - timedelta(minutes=val)

    patches = _load_patches(project_root)
    selected = [p for p in patches if p[0] >= dt]

    if not selected:
        console.print("[yellow]No patches in this timeframe.[/yellow]")
        return

    summary = ""
    for ts, commit, p in selected:
        summary += f"\n=== {ts} | {commit} ===\n{p.read_text()}\n"

    console.print(
        Panel(summary[:4000] + "\n\n(Truncated)", title=f"Patches since {interval}")
    )


@insight_app.command("search")
def insight_search(term: str):
    """Full-text search across all patches."""

    project_root = get_running_project_root()
    if not project_root:
        console.print("[red]DevMemory is not running.[/red]")
        raise typer.Exit(1)

    patches = _load_patches(project_root)
    results = []

    for ts, commit, p in patches:
        text = p.read_text()
        if term.lower() in text.lower():
            results.append((ts, commit, p))

    if not results:
        console.print("[yellow]No matches found.[/yellow]")
        return

    out = ""
    for ts, commit, p in results:
        out += f"\n--- {ts} | {commit} ---\n"
        snippet = "\n".join(
            line for line in p.read_text().splitlines() if term.lower() in line.lower()
        )
        out += snippet + "\n"

    console.print(
        Panel(out[:4000] + "\n(Truncated)", title=f"Search results for '{term}'")
    )
