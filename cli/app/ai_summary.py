from pathlib import Path
import google.generativeai as genai
from app.utils.pidfile import get_running_project_root

genai.configure(api_key="AIzaSyA9ISVUaLS-LWiq01IOKosIs2Fgv7DN930")
MODEL_NAME = "gemini-2.5-flash"


def get_patch_dir() -> Path:
    """Return the .devmemory/patches directory for the running project."""
    project_root = get_running_project_root()
    if not project_root:
        raise RuntimeError("DevMemory is not running")

    patch_dir = project_root / ".devmemory" / "patches"
    if not patch_dir.exists():
        raise RuntimeError("No patches found yet.")

    return patch_dir


def summarize_snapshot(date: str) -> Path:
    """Summarize all git patches for a given date (YYYY-MM-DD)."""

    project_root = get_running_project_root()
    if not project_root:
        raise RuntimeError("DevMemory is not running")

    patch_dir = get_patch_dir()

    # Convert "2025-11-19" → "20251119"
    prefix = date.replace("-", "")

    # Find matching patches
    matched = []
    for f in patch_dir.glob("*.patch"):
        ts = f.name.split("_")[0]
        if ts.startswith(prefix):
            matched.append(f)

    if not matched:
        raise FileNotFoundError(f"No patches found for date {date}")

    # Combine patch text
    combined = ""
    for f in matched:
        combined += f"\n\n--- PATCH: {f.name} ---\n"
        combined += f.read_text()

    # AI summary
    model = genai.GenerativeModel(MODEL_NAME)
    resp = model.generate_content(
        f"""
Summarize these git patches.

Extract:
- Work done
- Tasks in progress
- Bugs fixed
- Key changes
- Notes
- Future work ideas

{combined}
"""
    )

    result = resp.text.strip()

    # Save summary
    output_dir = project_root / ".devmemory" / "memory"
    output_dir.mkdir(parents=True, exist_ok=True)

    out_path = output_dir / f"{date}-summary.txt"
    out_path.write_text(result)

    return out_path
