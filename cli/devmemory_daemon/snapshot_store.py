from pathlib import Path
import json
from datetime import datetime


def get_snapshot_path(project_root):
    root = Path(project_root) / ".devmemory" / "snapshots"
    root.mkdir(parents=True, exist_ok=True)
    filename = datetime.utcnow().strftime("%Y-%m-%d") + ".jsonl"
    return root / filename


def write_snapshot(event: dict, project_root: Path):
    path = get_snapshot_path(project_root)
    with path.open("a") as f:
        f.write(json.dumps(event) + "\n")
