import os
import json
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Optional
from collections import Counter

from devmemory_daemon.git_engine import patches_dir, devmemory_root
from app.utils.pidfile import get_running_project_root
from fastapi.responses import PlainTextResponse

try:
    import google.generativeai as genai

    api_key = os.environ.get("GENAI_KEY", "AIzaSyDT0Y3z_pO47ElDyIBDGDwTGRHLsDutX04")
    genai.configure(api_key=api_key)
    AI_AVAILABLE = True
except Exception:
    AI_AVAILABLE = False

app = FastAPI(title="DevMemory API", version="3.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def _summarize_session_with_ai(session_data: dict) -> dict:
    if not AI_AVAILABLE:
        return {"error": "AI not available", "use_facts": True}

    project_root = get_running_project_root()
    if not project_root:
        raise HTTPException(status_code=503, detail="DevMemory not running")

    all_patches = get_patches_list(project_root)
    session_start = datetime.fromisoformat(session_data["started_at"])
    session_end = datetime.fromisoformat(
        session_data.get("stopped_at", datetime.now().isoformat())
    )

    pd = patches_dir(project_root)
    all_todos, all_fixmes, files_modified = [], [], []
    combined_patches = ""

    for p in all_patches:
        ts = datetime.fromisoformat(p["datetime"])
        if not (session_start <= ts <= session_end):
            continue

        patch_file = pd / p["file"]
        if not patch_file.exists():
            continue

        content = patch_file.read_text()
        combined_patches += f"\n{content}\n"

        signals = extract_todos_fixmes(content)
        all_todos.extend(signals["todos"])
        all_fixmes.extend(signals["fixmes"])

        for line in content.split("\n"):
            if line.startswith("diff --git"):
                parts = line.split()
                if len(parts) >= 3:
                    files_modified.append(parts[-1].replace("b/", ""))

    if not session_data.get("context"):
        return {
            "mode": "facts_only",
            "message": "No session context provided. Showing facts only.",
            "files_modified": list(set(files_modified)),
            "todos": all_todos[:20],
            "fixmes": all_fixmes[:20],
        }

    model = genai.GenerativeModel("gemini-2.0-flash")
    prompt = f"""
You are helping a developer understand one coding session.

SESSION CONTEXT: {session_data['context']}

DEVELOPER NOTES:
{chr(10).join(f"- [{note['time']}] {note['text']}" for note in session_data.get('notes', [])) or "No notes added"}

CODE SIGNALS FOUND:
TODOs: {len(all_todos)}
{chr(10).join(f"  - {todo}" for todo in all_todos[:5])}

FIXMEs: {len(all_fixmes)}
{chr(10).join(f"  - {fixme}" for fixme in all_fixmes[:5])}

FILES MODIFIED:
{chr(10).join(set(files_modified[:10]))}

RECENT CODE CHANGES:
{combined_patches[:2000]}

Based on the SESSION CONTEXT, notes, and code changes, provide a clear summary:

1. Progress made
2. Current status
3. Open items (especially TODO/FIXMEs)
4. Next steps

Be specific and concise.
"""
    response = model.generate_content(prompt)

    return {
        "mode": "smart",
        "summary": response.text,
        "session_context": session_data["context"],
        "notes_count": len(session_data.get("notes", [])),
        "todos_found": len(all_todos),
        "fixmes_found": len(all_fixmes),
    }


def get_current_session(project_root: Path) -> dict:
    session_file = devmemory_root(project_root) / "current_session.json"
    if session_file.exists():
        return json.loads(session_file.read_text())
    return None


def get_all_sessions(project_root: Path) -> List[dict]:
    sessions_dir = devmemory_root(project_root) / "sessions"
    if not sessions_dir.exists():
        return []

    sessions = []
    for f in sessions_dir.glob("*.json"):
        try:
            sessions.append(json.loads(f.read_text()))
        except:
            continue

    sessions.sort(key=lambda x: x.get("started_at", ""), reverse=True)
    return sessions


def get_patches_list(project_root: Path):
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


def extract_todos_fixmes(patch_text: str) -> dict:
    todos = []
    fixmes = []
    notes = []

    for line in patch_text.split("\n"):
        if line.startswith("+") and not line.startswith("+++"):
            content = line[1:].strip()

            if "TODO" in content.upper():
                todos.append(content)
            if "FIXME" in content.upper():
                fixmes.append(content)
            if "NOTE:" in content.upper() or "HACK:" in content.upper():
                notes.append(content)

    return {"todos": todos, "fixmes": fixmes, "notes": notes}


@app.get("/")
def root():
    return {
        "message": "DevMemory API",
        "version": "3.0.0",
        "features": ["session_context", "notes", "ai_summary", "insights"],
    }


@app.get("/api/session/{session_id}/summary")
def get_session_summary(session_id: str):
    project_root = get_running_project_root()
    if not project_root:
        raise HTTPException(status_code=503, detail="DevMemory not running")

    current = get_current_session(project_root)
    if current and current["session_id"] == session_id:
        session_data = current
    else:
        session_file = devmemory_root(project_root) / "sessions" / f"{session_id}.json"
        if not session_file.exists():
            raise HTTPException(status_code=404, detail="Session not found")
        session_data = json.loads(session_file.read_text())

    return _summarize_session_with_ai(session_data)


@app.get("/api/patch/{patch_file}", response_class=PlainTextResponse)
def get_patch(patch_file: str):
    project_root = get_running_project_root()
    if not project_root:
        raise HTTPException(status_code=503, detail="DevMemory not running")

    pd = patches_dir(project_root)

    if "/" in patch_file or "\\" in patch_file or not patch_file.endswith(".patch"):
        raise HTTPException(status_code=400, detail="Invalid patch name")

    path = pd / patch_file
    if not path.is_file():
        raise HTTPException(status_code=404, detail="Patch not found")

    return path.read_text()


@app.get("/api/status")
def get_status():
    project_root = get_running_project_root()
    if not project_root:
        raise HTTPException(status_code=503, detail="DevMemory daemon not running")

    patches = get_patches_list(project_root)
    session = get_current_session(project_root)

    return {
        "running": True,
        "projectRoot": str(project_root),
        "totalPatches": len(patches),
        "latestActivity": patches[0]["datetime"] if patches else None,
        "currentSession": session,
    }


@app.get("/api/sessions")
def list_sessions():
    project_root = get_running_project_root()
    if not project_root:
        raise HTTPException(status_code=503, detail="DevMemory not running")

    sessions = get_all_sessions(project_root)

    current = get_current_session(project_root)
    if current:
        sessions.insert(0, current)

    return {"sessions": sessions, "total": len(sessions)}


@app.get("/api/insights")
def get_insights(days: int = 30):
    project_root = get_running_project_root()
    if not project_root:
        raise HTTPException(status_code=503, detail="DevMemory not running")

    patches = get_patches_list(project_root)

    cutoff = datetime.now() - timedelta(days=days)
    recent = [p for p in patches if datetime.fromisoformat(p["datetime"]) >= cutoff]

    pd = patches_dir(project_root)
    file_counter = Counter()
    date_counter = Counter()

    for p in recent:
        date_counter[p["date"]] += 1
        patch_file = pd / p["file"]
        if not patch_file.exists():
            continue
        content = patch_file.read_text()
        for line in content.split("\n"):
            if line.startswith("diff --git"):
                parts = line.split()
                if len(parts) >= 3:
                    fname = parts[-1].replace("b/", "")
                    file_counter[fname] += 1

    hot_files = [{"file": f, "edits": c} for f, c in file_counter.most_common(10)]

    all_dates = sorted(set(date_counter.keys()))
    longest_streak = 0
    current_streak = 0
    last_date = None

    for dstr in all_dates:
        d = datetime.strptime(dstr, "%Y-%m-%d").date()
        if last_date is None:
            current_streak = 1
        else:
            if d == last_date + timedelta(days=1):
                current_streak += 1
            else:
                longest_streak = max(longest_streak, current_streak)
                current_streak = 1
        last_date = d

    longest_streak = max(longest_streak, current_streak)

    today = datetime.now().date()
    cur_streak = 0
    day = today
    while True:
        key = day.strftime("%Y-%m-%d")
        if key in date_counter:
            cur_streak += 1
            day = day - timedelta(days=1)
        else:
            break

    heatmap = [
        {"date": d, "count": date_counter[d]} for d in sorted(date_counter.keys())
    ]

    return {
        "hot_files": hot_files,
        "longest_streak": longest_streak,
        "current_streak": cur_streak,
        "activity": heatmap,
        "window_days": days,
    }


@app.get("/api/session/{session_id}")
def get_session_detail(session_id: str):
    project_root = get_running_project_root()
    if not project_root:
        raise HTTPException(status_code=503, detail="DevMemory not running")

    current = get_current_session(project_root)
    if current and current["session_id"] == session_id:
        session_data = current
    else:
        session_file = devmemory_root(project_root) / "sessions" / f"{session_id}.json"
        if not session_file.exists():
            raise HTTPException(status_code=404, detail="Session not found")
        session_data = json.loads(session_file.read_text())

    patches = get_patches_list(project_root)
    session_start = datetime.fromisoformat(session_data["started_at"])
    session_end = datetime.fromisoformat(
        session_data.get("stopped_at", datetime.now().isoformat())
    )

    session_patches = [
        p
        for p in patches
        if session_start <= datetime.fromisoformat(p["datetime"]) <= session_end
    ]

    return {
        **session_data,
        "patches": session_patches,
        "patch_count": len(session_patches),
    }


@app.get("/api/context/smart")
def smart_context_summary():
    project_root = get_running_project_root()
    if not project_root:
        raise HTTPException(status_code=503, detail="DevMemory not running")

    session = get_current_session(project_root)
    if not session:
        return {"message": "No active session"}

    return _summarize_session_with_ai(session)


@app.get("/api/patches")
def list_patches(limit: Optional[int] = None):
    project_root = get_running_project_root()
    if not project_root:
        raise HTTPException(status_code=503, detail="DevMemory not running")

    patches = get_patches_list(project_root)
    if limit:
        patches = patches[:limit]

    return {"patches": patches}


@app.get("/api/productivity/patterns")
def get_productivity_patterns(days: int = 30):
    from app.ai_summary import get_productivity_patterns

    project_root = get_running_project_root()
    if not project_root:
        raise HTTPException(status_code=503, detail="DevMemory not running")

    patterns = get_productivity_patterns(project_root, days)
    return patterns


@app.get("/api/quality/trends")
def get_quality_trends(days: int = 30):
    from app.ai_summary import analyze_code_quality_trends

    project_root = get_running_project_root()
    if not project_root:
        raise HTTPException(status_code=503, detail="DevMemory not running")

    trends = analyze_code_quality_trends(project_root, days)
    return trends


@app.get("/api/session/{session_id}/insights")
def get_deep_insights(session_id: str):
    from app.ai_summary import generate_session_insights

    project_root = get_running_project_root()
    if not project_root:
        raise HTTPException(status_code=503, detail="DevMemory not running")

    current = get_current_session(project_root)
    if current and current["session_id"] == session_id:
        session_data = current
    else:
        session_file = devmemory_root(project_root) / "sessions" / f"{session_id}.json"
        if not session_file.exists():
            raise HTTPException(status_code=404, detail="Session not found")

        session_data = json.loads(session_file.read_text())

    insights = generate_session_insights(session_data)
    return insights


@app.get("/api/stats/performance")
def get_performance_stats():
    project_root = get_running_project_root()
    if not project_root:
        raise HTTPException(status_code=503, detail="DevMemory not running")

    from app.utils.config import LOG_FILE

    if not LOG_FILE.exists():
        return {"error": "No stats available"}

    logs = LOG_FILE.read_text().splitlines()
    stats_lines = [line for line in logs if "Stats:" in line or "Final stats:" in line]

    if not stats_lines:
        return {"message": "No stats recorded yet"}

    return {
        "message": "DevMemory running optimized",
        "log_file": str(LOG_FILE),
        "recent_activity": logs[-10:] if logs else [],
    }
