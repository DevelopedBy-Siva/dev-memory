from pathlib import Path


def find_git_root(start: Path) -> Path:
    """
    Walk upward from `start` until we find a `.git` folder.
    Returns the repo root if found, otherwise returns `start`.
    """
    current = start.resolve()

    for parent in [current] + list(current.parents):
        if (parent / ".git").exists():
            return parent

    return start
