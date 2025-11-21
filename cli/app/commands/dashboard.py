import os
import time
import json
import socket
import threading
import subprocess
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse
from pathlib import Path

import typer
from rich.console import Console

from app.utils.pidfile import get_running_project_root
from devmemory_daemon.git_engine import patches_dir

console = Console()
dashboard_app = typer.Typer(help="Run DevMemory web dashboard (API + React UI)")


class DevMemoryAPI(BaseHTTPRequestHandler):
    def _json(self, obj, status=200):
        data = json.dumps(obj).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def log_message(self, format, *args):
        return  # silence logs

    @property
    def project_root(self) -> Path:
        return Path(self.server.project_root)

    def do_GET(self):
        path = urlparse(self.path).path
        project_root = self.project_root

        if path == "/api/status":
            return self._json({"running": True, "projectRoot": str(project_root)})

        if path == "/api/patches":
            pd = patches_dir(project_root)
            patches = []
            if pd.exists():
                for f in pd.glob("*.patch"):
                    ts, commit = f.name.split("_", 1)
                    commit = commit.replace(".patch", "")
                    patches.append({"timestamp": ts, "commit": commit, "file": f.name})
            patches.sort(key=lambda x: x["timestamp"], reverse=True)
            return self._json(patches)

        if path.startswith("/api/patch/"):
            commit_prefix = path.replace("/api/patch/", "")
            pd = patches_dir(project_root)

            if not pd.exists():
                return self._json({"error": "not found"}, 404)

            for f in pd.glob("*.patch"):
                _, commit = f.name.split("_", 1)
                commit = commit.replace(".patch", "")
                if commit.startswith(commit_prefix):
                    return self._json({"commit": commit, "patch": f.read_text()})

            return self._json({"error": "not found"}, 404)

        return self._json({"error": "unknown endpoint"}, 404)


def _find_free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("", 0))
        return s.getsockname()[1]


def _start_api_server(project_root: Path, port: int) -> ThreadingHTTPServer:
    server = ThreadingHTTPServer(("127.0.0.1", port), DevMemoryAPI)
    server.project_root = str(project_root)

    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()

    console.print(f"[green]DevMemory API running at http://127.0.0.1:{port}[/green]")
    return server


def _detect_react_port(start_port=3000, limit=10):
    import http.client

    for p in range(start_port, start_port + limit):
        try:
            conn = http.client.HTTPConnection("127.0.0.1", p, timeout=0.2)
            conn.request("GET", "/")
            resp = conn.getresponse()
            html = resp.read().decode("utf-8", errors="ignore")

            if '<div id="root"' in html or "<title>" in html:
                return p
        except Exception:
            pass
    return None


@dashboard_app.command("run")
def dashboard_run():
    project_root = get_running_project_root()
    if not project_root:
        console.print("[red]DevMemory daemon is not running.[/red]")
        console.print("Start it with: [bold]devmemory start[/bold]")
        raise typer.Exit(1)

    port = _find_free_port()
    api_server = _start_api_server(project_root, port)
    api_url = f"http://127.0.0.1:{port}"

    CLI_ROOT = Path(__file__).resolve().parents[2]
    dashboard_dir = CLI_ROOT / "dashboard"

    if not dashboard_dir.exists():
        console.print(f"[red]React dashboard not found at: {dashboard_dir}[/red]")
        console.print(f"[yellow]API is still running at {api_url}[/yellow]")
        return

    env = os.environ.copy()
    env["REACT_APP_DEVMEMORY_API"] = api_url
    env["BROWSER"] = "none"

    console.print(f"[cyan]Starting React dashboard in {dashboard_dir}[/cyan]")

    try:
        react_proc = subprocess.Popen(
            ["npm", "start"],
            cwd=str(dashboard_dir),
            env=env,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    except FileNotFoundError:
        console.print("[red]npm not found! Install Node.js + npm first.[/red]")
        return

    console.print("[green]React dashboard started.[/green]")

    time.sleep(2)
    react_port = _detect_react_port()

    if react_port:
        console.print(
            f"[bold]Dashboard running at http://localhost:{react_port}[/bold]"
        )
    else:
        console.print("[yellow]React started, but port not detected yet...[/yellow]")
        console.print(
            "[yellow]Try http://localhost:3000 or wait a few seconds.[/yellow]"
        )

    console.print("Press [magenta]Ctrl+C[/magenta] to stop.")

    try:
        while True:
            time.sleep(0.3)
            if react_proc.poll() is not None:
                console.print("[yellow]React exited.[/yellow]")
                break
    except KeyboardInterrupt:
        console.print("\n[cyan]Stopping dashboard...[/cyan]")
    finally:
        api_server.shutdown()
        if react_proc.poll() is None:
            react_proc.terminate()
        console.print("[green]Dashboard stopped.[/green]")
