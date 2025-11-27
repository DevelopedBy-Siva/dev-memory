from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Optional
import google.generativeai as genai

from devmemory_daemon.git_engine import patches_dir
from app.utils.pidfile import get_running_project_root

# Configure Gemini (move to env var later!)
genai.configure(api_key="AIzaSyA9ISVUaLS-LWiq01IOKosIs2Fgv7DN930")

app = FastAPI(title="DevMemory API", version="1.0.0")

# Enable CORS for Vue.js dev server
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ===== Helper Functions =====


def get_patches_list(project_root: Path):
    """Get all patches with metadata"""
    pd = patches_dir(project_root)
    if not pd.exists():
        return []

    patches = []
    for f in pd.glob("*.patch"):
        try:
            ts_str, commit = f.name.split("_", 1)
            commit = commit.replace(".patch", "")
            ts = datetime.strptime(ts_str, "%Y%m%dT%H%M%SZ")

            patches.append(
                {
                    "timestamp": ts_str,
                    "commit": commit,
                    "file": f.name,
                    "datetime": ts.isoformat(),
                    "date": ts.strftime("%Y-%m-%d"),
                    "time": ts.strftime("%H:%M:%S"),
                }
            )
        except Exception:
            continue

    patches.sort(key=lambda x: x["timestamp"], reverse=True)
    return patches


def analyze_patch(patch_text: str) -> dict:
    """Extract stats from patch"""
    lines = patch_text.split("\n")

    files_changed = []
    additions = 0
    deletions = 0

    for line in lines:
        if line.startswith("diff --git"):
            parts = line.split()
            if len(parts) >= 3:
                files_changed.append(parts[-1].replace("b/", ""))
        elif line.startswith("+") and not line.startswith("+++"):
            additions += 1
        elif line.startswith("-") and not line.startswith("---"):
            deletions += 1

    return {
        "files_changed": files_changed,
        "additions": additions,
        "deletions": deletions,
        "total_changes": additions + deletions,
    }


# ===== API Endpoints =====


@app.get("/api/status")
def get_status():
    """Check if DevMemory is running"""
    project_root = get_running_project_root()
    if not project_root:
        raise HTTPException(status_code=503, detail="DevMemory daemon not running")

    patches = get_patches_list(project_root)

    return {
        "running": True,
        "projectRoot": str(project_root),
        "totalPatches": len(patches),
        "latestActivity": patches[0]["datetime"] if patches else None,
    }


@app.get("/api/patches")
def list_patches(limit: Optional[int] = None, date: Optional[str] = None):
    """Get all patches or filter by date"""
    project_root = get_running_project_root()
    if not project_root:
        raise HTTPException(status_code=503, detail="DevMemory not running")

    patches = get_patches_list(project_root)

    # Filter by date if provided
    if date:
        patches = [p for p in patches if p["date"] == date]

    # Limit results
    if limit:
        patches = patches[:limit]

    return {"patches": patches, "total": len(patches)}


@app.get("/api/patch/{commit_prefix}")
def get_patch(commit_prefix: str):
    """Get specific patch content"""
    project_root = get_running_project_root()
    if not project_root:
        raise HTTPException(status_code=503, detail="DevMemory not running")

    pd = patches_dir(project_root)
    if not pd.exists():
        raise HTTPException(status_code=404, detail="No patches found")

    for f in pd.glob("*.patch"):
        _, commit = f.name.split("_", 1)
        commit = commit.replace(".patch", "")
        if commit.startswith(commit_prefix):
            patch_text = f.read_text()
            stats = analyze_patch(patch_text)

            return {"commit": commit, "patch": patch_text, "stats": stats}

    raise HTTPException(status_code=404, detail="Patch not found")


@app.get("/api/sessions")
def get_sessions():
    """Group patches into coding sessions (separated by >30min gaps)"""
    project_root = get_running_project_root()
    if not project_root:
        raise HTTPException(status_code=503, detail="DevMemory not running")

    patches = get_patches_list(project_root)

    sessions = []
    current_session = []

    for i, patch in enumerate(patches):
        if not current_session:
            current_session.append(patch)
        else:
            prev_time = datetime.fromisoformat(current_session[-1]["datetime"])
            curr_time = datetime.fromisoformat(patch["datetime"])

            # If gap > 30 minutes, start new session
            if prev_time - curr_time > timedelta(minutes=30):
                sessions.append(
                    {
                        "start": current_session[-1]["datetime"],
                        "end": current_session[0]["datetime"],
                        "patches": len(current_session),
                        "commits": [p["commit"][:8] for p in current_session[:3]],
                    }
                )
                current_session = [patch]
            else:
                current_session.append(patch)

    if current_session:
        sessions.append(
            {
                "start": current_session[-1]["datetime"],
                "end": current_session[0]["datetime"],
                "patches": len(current_session),
                "commits": [p["commit"][:8] for p in current_session[:3]],
            }
        )

    return {"sessions": sessions}


@app.post("/api/summarize")
def summarize_patches(
    date: Optional[str] = None, commit_ids: Optional[List[str]] = None
):
    """AI-powered summary of patches"""
    project_root = get_running_project_root()
    if not project_root:
        raise HTTPException(status_code=503, detail="DevMemory not running")

    pd = patches_dir(project_root)
    patches_to_summarize = []

    # Get patches by date or specific commits
    if date:
        date_prefix = date.replace("-", "")
        patches_to_summarize = [
            f for f in pd.glob("*.patch") if f.name.startswith(date_prefix)
        ]
    elif commit_ids:
        for commit_id in commit_ids:
            for f in pd.glob("*.patch"):
                if commit_id in f.name:
                    patches_to_summarize.append(f)
    else:
        # Default: last 5 patches
        all_patches = sorted(pd.glob("*.patch"), reverse=True)
        patches_to_summarize = all_patches[:5]

    if not patches_to_summarize:
        raise HTTPException(status_code=404, detail="No patches found to summarize")

    # Combine patches
    combined = ""
    for f in patches_to_summarize:
        combined += f"\n=== {f.name} ===\n{f.read_text()}\n"

    # AI Summary
    model = genai.GenerativeModel("gemini-2.0-flash-exp")
    prompt = f"""Analyze these git patches and provide a developer-friendly summary.

Extract:
1. **What was accomplished**: Main changes, features added, bugs fixed
2. **Current focus**: What the developer is working on
3. **Open tasks**: TODOs, FIXMEs, incomplete work
4. **Key decisions**: Important choices made
5. **Next steps**: Suggested actions to continue

Be concise but informative. Format with markdown.

{combined}
"""

    response = model.generate_content(prompt)

    return {
        "summary": response.text,
        "patches_analyzed": len(patches_to_summarize),
        "period": date or "recent",
    }


@app.get("/api/context/restore")
def restore_context():
    """Get context for 'what was I working on?'"""
    project_root = get_running_project_root()
    if not project_root:
        raise HTTPException(status_code=503, detail="DevMemory not running")

    patches = get_patches_list(project_root)
    if not patches:
        return {"message": "No activity yet"}

    # Get recent patches (last hour or last 5, whichever is more)
    recent = []
    cutoff = datetime.now() - timedelta(hours=1)

    for p in patches:
        patch_time = datetime.fromisoformat(p["datetime"])
        if patch_time > cutoff or len(recent) < 5:
            recent.append(p)
        else:
            break

    # Get patch contents for AI
    pd = patches_dir(project_root)
    combined = ""
    files_touched = set()

    for p in recent[:5]:  # Limit to avoid token overflow
        patch_file = pd / p["file"]
        if patch_file.exists():
            content = patch_file.read_text()
            combined += f"\n{content}\n"

            # Extract file names
            for line in content.split("\n"):
                if line.startswith("diff --git"):
                    parts = line.split()
                    if len(parts) >= 3:
                        files_touched.add(parts[-1].replace("b/", ""))

    # AI context restoration
    model = genai.GenerativeModel("gemini-2.0-flash-exp")
    prompt = f"""You are helping a developer remember what they were working on.

Based on these recent code changes:

{combined}

Provide a clear, friendly summary:
1. **Current Task**: What they're building/fixing (1-2 sentences)
2. **Progress**: What's done vs. what's left
3. **Active Files**: Key files being modified
4. **Next Action**: Specific next step to take

Be conversational and actionable.
"""

    response = model.generate_content(prompt)

    return {
        "context": response.text,
        "recentPatches": len(recent),
        "activePeriod": f"{recent[-1]['time']} - {recent[0]['time']}",
        "filesInFocus": list(files_touched),
    }


@app.get("/api/search")
def search_patches(query: str):
    """Search patches by content"""
    project_root = get_running_project_root()
    if not project_root:
        raise HTTPException(status_code=503, detail="DevMemory not running")

    pd = patches_dir(project_root)
    results = []

    for f in pd.glob("*.patch"):
        content = f.read_text()
        if query.lower() in content.lower():
            ts_str, commit = f.name.split("_", 1)
            commit = commit.replace(".patch", "")

            # Get snippet
            lines = content.split("\n")
            matching_lines = [l for l in lines if query.lower() in l.lower()]

            results.append(
                {
                    "commit": commit[:8],
                    "timestamp": ts_str,
                    "matches": len(matching_lines),
                    "snippet": "\n".join(matching_lines[:3]),
                }
            )

    return {"results": results, "total": len(results)}
