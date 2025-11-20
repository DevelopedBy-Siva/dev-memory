import typer
from rich.console import Console

from app.commands.start import start
from app.commands.stop import stop
from app.commands.status import status
from app.commands.logs import logs

from app.commands.insight import insight_app
from app.commands.diff import diff_app
from app.commands.summarize import summarize_app

console = Console()
app = typer.Typer(help="DevMemory CLI")

# Core commands
app.command("start")(start)
app.command("stop")(stop)
app.command("status")(status)
app.command("logs")(logs)

# Submodules
app.add_typer(insight_app, name="insight")
app.add_typer(diff_app, name="diff")
app.add_typer(summarize_app, name="summarize")
