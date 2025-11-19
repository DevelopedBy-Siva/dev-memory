# devmemory_daemon/git_engine.py
import subprocess
from pathlib import Path
from datetime import datetime
from hashlib import sha1
import os

DEVMEMORY_HOME = Path.home() / ".devmemory"
#
# Basic ignore list so we don't pull .git, .devmemory etc.
IGNORE_DIRS = {".git", ".devmemory", "__pycache__", "node_modules", ".venv", "venv"}


def project_id(project_root: Path) -> str:
    return sha1(str(project_root).encode("utf-8")).hexdigest()[:12]


def shadow_root(project_root: Path) -> Path:
    return DEVMEMORY_HOME / "projects" / project_id(project_root) / "repo"


def patches_dir(project_root: Path) -> Path:
    return DEVMEMORY_HOME / "projects" / project_id(project_root) / "patches"


def ensure_shadow_repo(project_root: Path) -> Path:
    """Create/initialize a private Git repo for this project under ~/.devmemory."""
    repo = shadow_root(project_root)
    repo.mkdir(parents=True, exist_ok=True)

    if not (repo / ".git").exists():
        subprocess.run(["git", "init"], cwd=repo, check=True)
        # Set local identity so commits don't fail
        subprocess.run(
            ["git", "config", "user.name", "DevMemory"],
            cwd=repo,
            check=True,
        )
        subprocess.run(
            ["git", "config", "user.email", "devmemory@example.com"],
            cwd=repo,
            check=True,
        )

    return repo


def sync_worktree(project_root: Path, repo: Path) -> None:
    """
    Copy current project files into the shadow repo,
    ignoring .git/.devmemory and friends.
    """
    project_root = project_root.resolve()
    repo = repo.resolve()

    # Gather all files in project
    project_files = set()
    for root, dirs, files in os.walk(project_root):
        # prune ignored dirs
        dirs[:] = [d for d in dirs if d not in IGNORE_DIRS]

        root_path = Path(root)
        for name in files:
            rel = (root_path / name).relative_to(project_root)
            project_files.add(rel)

    # Gather all files currently in shadow repo
    repo_files = set()
    for root, dirs, files in os.walk(repo):
        dirs[:] = [d for d in dirs if d != ".git"]

        root_path = Path(root)
        for name in files:
            rel = (root_path / name).relative_to(repo)
            repo_files.add(rel)

    # Copy / update files from project -> repo
    for rel in project_files:
        src = project_root / rel
        dst = repo / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        # Just overwrite; git will track changes
        dst.write_bytes(src.read_bytes())

    # Delete files that were removed in project
    for rel in repo_files:
        if rel not in project_files:
            # don't delete .git or its contents
            if str(rel).startswith(".git"):
                continue
            (repo / rel).unlink(missing_ok=True)


def commit_and_capture_patch(project_root: Path) -> None:
    """
    Sync project into shadow repo, commit changes if any,
    and store patch under ~/.devmemory/projects/<id>/patches.
    """
    project_root = project_root.resolve()
    repo = ensure_shadow_repo(project_root)
    sync_worktree(project_root, repo)

    # Stage all changes
    subprocess.run(["git", "add", "-A"], cwd=repo, check=True)

    # Check if anything to commit
    diff = subprocess.run(
        ["git", "diff", "--cached", "--quiet"],
        cwd=repo,
    )
    if diff.returncode == 0:
        # no staged changes
        return

    # Commit
    subprocess.run(
        ["git", "commit", "-m", "[DevMemory] Snapshot", "--no-gpg-sign"],
        cwd=repo,
        check=True,
    )

    commit_hash = (
        subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=repo).decode().strip()
    )

    patch_text = subprocess.check_output(
        ["git", "show", commit_hash],
        cwd=repo,
    ).decode()

    pd = patches_dir(project_root)
    pd.mkdir(parents=True, exist_ok=True)
    ts = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    patch_file = pd / f"{ts}_{commit_hash}.patch"
    patch_file.write_text(patch_text)
