import typer
from rich.console import Console

from app.commands.start import start
from app.commands.stop import stop
from app.commands.status import status
from app.commands.logs import logs
from app.commands.note import note_app


from app.commands.summarize import summarize_app
from app.commands.dashboard import dashboard_app

console = Console()
app = typer.Typer(help="DevMemory CLI")

app.command("start")(start)
app.command("stop")(stop)
app.command("status")(status)
app.command("logs")(logs)

app.add_typer(note_app, name="note")
app.add_typer(summarize_app, name="summarize")
app.add_typer(dashboard_app, name="dashboard")
