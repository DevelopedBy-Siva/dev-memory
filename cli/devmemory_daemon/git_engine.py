import os
import json
from pathlib import Path
from datetime import datetime
import subprocess

IGNORE_DIRS = {".git", ".devmemory", "__pycache__", "node_modules", "venv", ".venv"}

STATE_FILE = "state.json"


def devmemory_root(project_root: Path) -> Path:
    return project_root / ".devmemory"


def shadow_repo_root(project_root: Path) -> Path:
    return devmemory_root(project_root) / "repo"


def patches_dir(project_root: Path) -> Path:
    return devmemory_root(project_root) / "patches"


def _load_state(project_root: Path):
    path = devmemory_root(project_root) / STATE_FILE
    if path.exists():
        try:
            return json.loads(path.read_text())
        except Exception:
            return {"files": {}}
    return {"files": {}}


def _save_state(project_root: Path, state):
    path = devmemory_root(project_root) / STATE_FILE
    path.write_text(json.dumps(state, indent=2))


def _scan_project_files(project_root: Path):
    files = {}
    for root, dirs, filenames in os.walk(project_root):
        dirs[:] = [d for d in dirs if d not in IGNORE_DIRS]
        root_path = Path(root)

        for name in filenames:
            abs_path = root_path / name
            rel_path = abs_path.relative_to(project_root)

            stat = abs_path.stat()
            files[str(rel_path)] = {
                "mtime": stat.st_mtime,
                "size": stat.st_size,
            }

    return files


def _incremental_sync(project_root: Path, repo: Path):
    """Only copy files that changed according to state.json"""

    state = _load_state(project_root)
    old_files = state.get("files", {})

    new_files = _scan_project_files(project_root)
    changed = []
    deleted = []

    for rel, meta in new_files.items():
        if rel not in old_files:
            changed.append(rel)
        else:
            old_meta = old_files[rel]
            if old_meta["mtime"] != meta["mtime"] or old_meta["size"] != meta["size"]:
                changed.append(rel)

    for rel in old_files:
        if rel not in new_files:
            deleted.append(rel)

    for rel in changed:
        src = project_root / rel
        dst = repo / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        dst.write_bytes(src.read_bytes())

    for rel in deleted:
        (repo / rel).unlink(missing_ok=True)

    state["files"] = new_files
    _save_state(project_root, state)


def ensure_shadow_repo(project_root: Path) -> Path:
    project_root = project_root.resolve()
    dm_root = devmemory_root(project_root)
    repo = shadow_repo_root(project_root)

    dm_root.mkdir(parents=True, exist_ok=True)
    repo.mkdir(parents=True, exist_ok=True)

    if not (repo / ".git").exists():
        subprocess.run(["git", "init"], cwd=repo, check=True)
        subprocess.run(["git", "config", "user.name", "DevMemory"], cwd=repo)
        subprocess.run(
            ["git", "config", "user.email", "devmemory@example.com"], cwd=repo
        )

        _incremental_sync(project_root, repo)

        subprocess.run(["git", "add", "-A"], cwd=repo, check=True)
        subprocess.run(
            ["git", "commit", "-m", "[DevMemory] Baseline", "--no-gpg-sign"],
            cwd=repo,
            check=True,
        )

    return repo


def commit_and_capture_patch(project_root: Path):
    project_root = project_root.resolve()
    repo = ensure_shadow_repo(project_root)

    _incremental_sync(project_root, repo)

    subprocess.run(["git", "add", "-A"], cwd=repo, check=True)

    diff = subprocess.run(["git", "diff", "--cached", "--quiet"], cwd=repo)
    if diff.returncode == 0:
        return  # no changes detected

    subprocess.run(
        ["git", "commit", "-m", "[DevMemory] Snapshot", "--no-gpg-sign"],
        cwd=repo,
        check=True,
    )

    commit_hash = (
        subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=repo).decode().strip()
    )
    patch_text = subprocess.check_output(
        ["git", "show", commit_hash], cwd=repo
    ).decode()

    pd = patches_dir(project_root)
    pd.mkdir(parents=True, exist_ok=True)

    ts = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    (pd / f"{ts}_{commit_hash}.patch").write_text(patch_text)
