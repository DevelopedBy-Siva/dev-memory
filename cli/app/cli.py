import typer
from rich.console import Console

from app.commands.start import start
from app.commands.stop import stop
from app.commands.status import status
from app.commands.logs import logs

# NEW
from app.commands.insight import insight_app
from app.commands.diff import diff_app

console = Console()
app = typer.Typer(help="DevMemory CLI")

# Existing
app.command("start")(start)
app.command("stop")(stop)
app.command("status")(status)
app.command("logs")(logs)

# NEW subcommand groups
app.add_typer(insight_app, name="insight")
app.add_typer(diff_app, name="diff")
