import time
from pathlib import Path
from typing import Set, Dict
from collections import defaultdict

IGNORE_PATTERNS = {
    ".git",
    ".gitignore",
    ".gitmodules",
    "node_modules",
    "venv",
    ".venv",
    "env",
    "__pycache__",
    "vendor",
    "packages",
    ".npm",
    ".yarn",
    "dist",
    "build",
    "out",
    ".next",
    ".nuxt",
    "target",
    ".parcel-cache",
    ".cache",
    ".temp",
    "tmp",
    ".vscode",
    ".idea",
    ".eclipse",
    "*.swp",
    "*.swo",
    ".DS_Store",
    "Thumbs.db",
    "*.log",
    "logs",
    ".devmemory",
    "*.pyc",
    "*.pyo",
    "*.class",
    "*.o",
    "*.so",
    "*.dll",
    "package-lock.json",
    "yarn.lock",
    "Cargo.lock",
}

IGNORE_EXTENSIONS = {
    ".pyc",
    ".pyo",
    ".pyd",
    ".so",
    ".dll",
    ".dylib",
    ".class",
    ".jar",
    ".war",
    ".ear",
    ".o",
    ".obj",
    ".a",
    ".lib",
    ".log",
    ".tmp",
    ".temp",
    ".swp",
    ".swo",
    ".DS_Store",
    ".min.js",
    ".min.css",
}


class DebounceManager:

    def __init__(self, debounce_ms: int = 500):
        self.debounce_ms = debounce_ms / 1000.0
        self.pending_files: Dict[str, float] = {}
        self.last_process_time = 0.0

    def add_event(self, file_path: str):
        self.pending_files[file_path] = time.time()

    def should_process(self) -> bool:
        if not self.pending_files:
            return False

        now = time.time()
        oldest_event = min(self.pending_files.values())

        return (now - oldest_event) >= self.debounce_ms

    def get_pending_files(self) -> Set[str]:
        files = set(self.pending_files.keys())
        self.pending_files.clear()
        self.last_process_time = time.time()
        return files

    def clear(self):
        self.pending_files.clear()


def should_ignore_path(path: Path, project_root: Path) -> bool:
    try:
        rel_path = path.relative_to(project_root)
    except ValueError:
        return True

    for part in rel_path.parts:
        if part in IGNORE_PATTERNS:
            return True

        if part.startswith(".") and len(part) > 1:
            return True

    if path.suffix.lower() in IGNORE_EXTENSIONS:
        return True

    return False


def get_file_stats(path: Path) -> Dict:
    try:
        stat = path.stat()
        return {
            "size": stat.st_size,
            "mtime": stat.st_mtime,
        }
    except Exception:
        return None
