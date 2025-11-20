import subprocess
from pathlib import Path
from datetime import datetime
import os

IGNORE_DIRS = {".git", ".devmemory", "__pycache__", "node_modules", "venv", ".venv"}


def devmemory_root(project_root: Path) -> Path:
    return project_root / ".devmemory"


def shadow_repo_root(project_root: Path) -> Path:
    return devmemory_root(project_root) / "repo"


def patches_dir(project_root: Path) -> Path:
    return devmemory_root(project_root) / "patches"


def _gather_project_files(project_root: Path):
    project_files = set()
    for root, dirs, files in os.walk(project_root):
        dirs[:] = [d for d in dirs if d not in IGNORE_DIRS]
        root_path = Path(root)
        for name in files:
            rel = (root_path / name).relative_to(project_root)
            project_files.add(rel)
    return project_files


def _gather_repo_files(repo: Path):
    repo_files = set()
    for root, dirs, files in os.walk(repo):
        dirs[:] = [d for d in dirs if d != ".git"]
        root_path = Path(root)
        for name in files:
            rel = (root_path / name).relative_to(repo)
            repo_files.add(rel)
    return repo_files


def _sync_worktree(project_root: Path, repo: Path):
    project_root = project_root.resolve()
    repo = repo.resolve()

    project_files = _gather_project_files(project_root)
    repo_files = _gather_repo_files(repo)

    for rel in project_files:
        src = project_root / rel
        dst = repo / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        dst.write_bytes(src.read_bytes())

    for rel in repo_files:
        if rel not in project_files:
            if str(rel).startswith(".git"):
                continue
            (repo / rel).unlink(missing_ok=True)


def ensure_shadow_repo(project_root: Path) -> Path:
    project_root = project_root.resolve()
    dm_root = devmemory_root(project_root)
    repo = shadow_repo_root(project_root)

    dm_root.mkdir(parents=True, exist_ok=True)
    repo.mkdir(parents=True, exist_ok=True)

    if not (repo / ".git").exists():
        subprocess.run(["git", "init"], cwd=repo, check=True)
        subprocess.run(
            ["git", "config", "user.name", "DevMemory"], cwd=repo, check=True
        )
        subprocess.run(
            ["git", "config", "user.email", "devmemory@example.com"],
            cwd=repo,
            check=True,
        )

        _sync_worktree(project_root, repo)
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

    _sync_worktree(project_root, repo)

    subprocess.run(["git", "add", "-A"], cwd=repo, check=True)

    diff = subprocess.run(["git", "diff", "--cached", "--quiet"], cwd=repo)
    if diff.returncode == 0:
        return

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
