# cli/app/commands/summarize.py

import typer
from rich.console import Console
from app.ai_summary import summarize_snapshot

console = Console()
summarize_app = typer.Typer(help="AI-powered snapshot summarization")


@summarize_app.command("run")
def summarize_run(
    date: str = typer.Option(..., help="Snapshot date, e.g., 2025-11-18")
):
    """
    Summarize a .jsonl snapshot using Gemini AI and store output in memory folder.
    """
    console.print(f"[bold green]Summarizing snapshot for {date}...[/bold green]")

    try:
        out_path = summarize_snapshot(date)
        console.print(f"[bold cyan]Summary created:[/bold cyan] {out_path}")
    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {e}")
