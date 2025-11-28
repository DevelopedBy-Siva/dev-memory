import os
import json
from pathlib import Path
from typing import List, Dict, Iterable

import google.generativeai as genai
from devmemory_daemon.git_engine import patches_dir  # ✅ use patches_dir
from app.utils.pidfile import get_running_project_root

api_key = os.environ.get("GENAI_KEY")
genai.configure(api_key=api_key)

MODEL_NAME = "gemini-2.5-flash"


def resolve_dirs():
    """
    Always return snapshot & memory folders based on the project root
    where DevMemory daemon is running.
    """
    project_root = get_running_project_root()
    if not project_root:
        raise RuntimeError("DevMemory is not running. Start with: devmemory start")

    # we mainly use memory_dir; snapshot_dir is reserved for future
    snapshot_dir = project_root / ".devmemory" / "snapshots"
    memory_dir = project_root / ".devmemory" / "memory"

    memory_dir.mkdir(parents=True, exist_ok=True)

    return snapshot_dir, memory_dir


def stream_jsonl(path: Path) -> Iterable[Dict]:
    with path.open("r", encoding="utf-8") as file:
        for line in file:
            line = line.strip()
            if not line:
                continue
            try:
                yield json.loads(line)
            except Exception:
                continue


INTERESTING = {
    "task",
    "todo",
    "note",
    "decision",
    "problem",
    "fix",
    "context",
    "command",
}


def extract_signals(snapshot_path: Path) -> List[str]:
    lines = []

    for entry in stream_jsonl(snapshot_path):
        etype = entry.get("type", "").lower()
        content = entry.get("content") or entry.get("text") or ""

        if not content:
            continue

        if etype in INTERESTING:
            lines.append(f"{etype.upper()}: {content}")
            continue

        low = content.lower()
        if any(kw in low for kw in ["todo", "fix", "next step"]):
            lines.append(f"NOTE: {content}")

    return lines


def chunk_text(lines: List[str], max_chars: int = 8000) -> List[str]:
    chunks = []
    current = []
    cur_len = 0

    for line in lines:
        if cur_len + len(line) + 1 > max_chars:
            chunks.append("\n".join(current))
            current = []
            cur_len = 0

        current.append(line)
        cur_len += len(line)

    if current:
        chunks.append("\n".join(current))

    return chunks


def gsum(text: str) -> str:
    model = genai.GenerativeModel(MODEL_NAME)

    prompt = f"""
Summarize the developer logs below.

Extract:
- tasks completed
- tasks in progress
- pending tasks
- key decisions
- problems encountered
- solutions
- notes
- reasoning steps

Be concise and structured.

--- LOGS START ---
{text}
--- LOGS END ---
"""
    response = model.generate_content(prompt)
    return response.text.strip()


def summarize_snapshot(date: str) -> Path:
    """
    Summarize all DevMemory git patches for a given date (YYYY-MM-DD)
    and store the result in <project>/.devmemory/memory/<date>-summary.json
    """
    # Resolve dirs (ensures memory dir exists)
    _, memory_dir = resolve_dirs()

    project_root = get_running_project_root()
    if not project_root:
        raise RuntimeError("DevMemory is not running")

    patch_dir = patches_dir(project_root)  # ✅ new per-project location
    if not patch_dir.exists():
        raise RuntimeError("No patches found for this project.")

    # Convert date "2025-11-19" → "20251119"
    date_prefix = date.replace("-", "")

    # Gather matching patches
    matched = []
    for f in patch_dir.glob("*.patch"):
        ts = f.name.split("_")[0]  # 20251119T072344Z
        if ts.startswith(date_prefix):
            matched.append(f)

    if not matched:
        raise FileNotFoundError(f"No patches found for date {date}")

    # Merge patch texts
    combined = ""
    for f in matched:
        combined += f"\n--- PATCH: {f.name} ---\n"
        combined += f.read_text()

    # Run AI summary
    model = genai.GenerativeModel(MODEL_NAME)
    resp = model.generate_content(
        f"""
Summarize these git patches.

Extract:
- Work done
- Tasks in progress
- Bugs fixed
- Decisions
- Key context
- Future work

{combined}
"""
    )

    result = resp.text.strip()

    # Save output
    out_path = memory_dir / f"{date}-summary.json"
    out_path.write_text(result)

    return out_path
