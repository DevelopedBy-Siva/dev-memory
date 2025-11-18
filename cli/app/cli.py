import typer
from rich.console import Console

from .commands.start import start
from .commands.stop import stop
from .commands.status import status
from .commands.logs import logs
from .commands.insight import insight

app = typer.Typer(help="DevMemory CLI")
console = Console()

app.command()(start)
app.command()(stop)
app.command()(status)
app.command()(logs)
app.command()(insight)
