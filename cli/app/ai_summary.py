import os
import json
from pathlib import Path
from typing import List, Dict
from datetime import datetime, timedelta
from collections import Counter, defaultdict

import google.generativeai as genai
from devmemory_daemon.git_engine import patches_dir
from devmemory_daemon.syntax_diff import analyze_patch_with_syntax
from app.utils.pidfile import get_running_project_root

api_key = os.environ.get("GENAI_KEY")
genai.configure(api_key=api_key)

MODEL_NAME = "gemini-2.0-flash"


def get_productivity_patterns(project_root: Path, days: int = 30) -> Dict:
    pd = patches_dir(project_root)
    if not pd.exists():
        return {}

    cutoff = datetime.now() - timedelta(days=days)
    patches_by_hour = defaultdict(list)
    patches_by_day = defaultdict(int)
    patches_by_weekday = defaultdict(int)

    for patch_file in pd.glob("*.patch"):
        try:
            ts_str = patch_file.name.split("_")[0]
            ts = datetime.strptime(ts_str, "%Y%m%dT%H%M%SZ")

            if ts < cutoff:
                continue

            hour = ts.hour
            date = ts.date()
            weekday = ts.strftime("%A")

            content = patch_file.read_text()
            lines_changed = len(
                [
                    l
                    for l in content.split("\n")
                    if l.startswith("+") or l.startswith("-")
                ]
            )

            patches_by_hour[hour].append(lines_changed)
            patches_by_day[str(date)] += lines_changed
            patches_by_weekday[weekday] += lines_changed

        except Exception:
            continue

    hourly_avg = {
        h: sum(lines) / len(lines) for h, lines in patches_by_hour.items() if lines
    }
    peak_hours = sorted(hourly_avg.items(), key=lambda x: x[1], reverse=True)[:3]

    today = datetime.now().date()
    streak = 0
    day = today
    while str(day) in patches_by_day:
        streak += 1
        day = day - timedelta(days=1)

    if patches_by_weekday:
        best_day = max(patches_by_weekday.items(), key=lambda x: x[1])[0]
    else:
        best_day = None

    return {
        "peak_hours": [h for h, _ in peak_hours],
        "peak_hours_detail": [{"hour": h, "avg_lines": avg} for h, avg in peak_hours],
        "current_streak_days": streak,
        "total_active_days": len(patches_by_day),
        "most_productive_weekday": best_day,
        "weekday_breakdown": dict(patches_by_weekday),
        "avg_daily_output": sum(patches_by_day.values()) / max(len(patches_by_day), 1),
    }


def analyze_code_quality_trends(project_root: Path, days: int = 30) -> Dict:
    pd = patches_dir(project_root)
    if not pd.exists():
        return {}

    cutoff = datetime.now() - timedelta(days=days)

    todo_count = 0
    fixme_count = 0
    functions_added = 0
    functions_modified = 0
    total_patches = 0

    for patch_file in pd.glob("*.patch"):
        try:
            ts_str = patch_file.name.split("_")[0]
            ts = datetime.strptime(ts_str, "%Y%m%dT%H%M%SZ")

            if ts < cutoff:
                continue

            content = patch_file.read_text()
            total_patches += 1

            for line in content.split("\n"):
                if line.startswith("+"):
                    if "TODO" in line.upper():
                        todo_count += 1
                    if "FIXME" in line.upper():
                        fixme_count += 1

            syntax_stats = analyze_patch_with_syntax(content)
            functions_added += len(syntax_stats.get("functions_added", []))
            functions_modified += len(syntax_stats.get("functions_modified", []))

        except Exception:
            continue

    return {
        "total_patches": total_patches,
        "todos_added": todo_count,
        "fixmes_added": fixme_count,
        "functions_created": functions_added,
        "functions_modified": functions_modified,
        "avg_todos_per_patch": todo_count / max(total_patches, 1),
        "code_health_score": max(0, 100 - (fixme_count * 5) - (todo_count * 2)),
    }


def generate_session_insights(session_data: Dict) -> Dict:
    if not session_data.get("context"):
        return {"error": "No session context available"}

    project_root = get_running_project_root()
    if not project_root:
        return {"error": "DevMemory not running"}

    pd = patches_dir(project_root)
    session_start = datetime.fromisoformat(session_data["started_at"])
    session_end = datetime.fromisoformat(
        session_data.get("stopped_at", datetime.now().isoformat())
    )

    all_patches = []
    functions_changed = []
    files_touched = set()

    for patch_file in pd.glob("*.patch"):
        try:
            ts_str = patch_file.name.split("_")[0]
            ts = datetime.strptime(ts_str, "%Y%m%dT%H%M%SZ")

            if not (session_start <= ts <= session_end):
                continue

            content = patch_file.read_text()
            all_patches.append(content)

            for line in content.split("\n"):
                if line.startswith("diff --git"):
                    parts = line.split()
                    if len(parts) >= 4:
                        files_touched.add(parts[3].replace("b/", ""))

            syntax_stats = analyze_patch_with_syntax(content)
            functions_changed.extend(syntax_stats.get("functions_added", []))
            functions_changed.extend(syntax_stats.get("functions_modified", []))

        except Exception:
            continue

    model = genai.GenerativeModel(MODEL_NAME)

    combined_context = f"""
SESSION GOAL: {session_data['context']}

DEVELOPER NOTES:
{chr(10).join(f"- [{n['time']}] {n['text']}" for n in session_data.get('notes', []))}

FILES MODIFIED: {len(files_touched)}
{chr(10).join(list(files_touched)[:10])}

FUNCTIONS CHANGED: {len(set(functions_changed))}
{chr(10).join(list(set(functions_changed))[:15])}

CODE SAMPLE (last patch):
{all_patches[-1][:1500] if all_patches else 'No patches yet'}
"""

    prompt = f"""
You are analyzing a developer's coding session. Based on the context below, provide:

1. **Progress Assessment**: What % complete is the work? (0-100)
2. **Status**: blocked | in_progress | ready_for_review | complete
3. **Key Achievements**: Bullet list of what was accomplished
4. **Blockers**: Any issues or dependencies preventing progress
5. **Next Steps**: Specific 2-3 actions to take next
6. **Time Estimate**: How much more time needed to complete

Be specific, concise, and actionable. Use the function names and file changes as evidence.

{combined_context}

Respond in JSON format:
{{
  "progress_percent": 0-100,
  "status": "blocked|in_progress|ready_for_review|complete",
  "achievements": ["item1", "item2"],
  "blockers": ["item1"] or [],
  "next_steps": ["step1", "step2", "step3"],
  "time_remaining": "X hours/days",
  "confidence": "high|medium|low"
}}
"""

    try:
        response = model.generate_content(prompt)
        result = json.loads(
            response.text.strip().replace("```json", "").replace("```", "")
        )

        return {
            "mode": "smart",
            "insights": result,
            "context": session_data["context"],
            "files_touched": len(files_touched),
            "functions_changed": len(set(functions_changed)),
            "patches_analyzed": len(all_patches),
        }

    except Exception as e:
        return {
            "error": f"AI analysis failed: {str(e)}",
            "fallback_stats": {
                "files_touched": len(files_touched),
                "functions_changed": len(set(functions_changed)),
                "patches": len(all_patches),
            },
        }


def summarize_snapshot(date: str) -> Path:
    project_root = get_running_project_root()
    if not project_root:
        raise RuntimeError("DevMemory is not running")

    pd = patches_dir(project_root)
    if not pd.exists():
        raise RuntimeError("No patches found")

    date_prefix = date.replace("-", "")
    matched = [
        f for f in pd.glob("*.patch") if f.name.split("_")[0].startswith(date_prefix)
    ]

    if not matched:
        raise FileNotFoundError(f"No patches for {date}")

    combined = ""
    all_functions = []

    for f in matched:
        content = f.read_text()
        combined += f"\n--- PATCH: {f.name} ---\n{content}"

        stats = analyze_patch_with_syntax(content)
        all_functions.extend(stats.get("functions_added", []))
        all_functions.extend(stats.get("functions_modified", []))

    model = genai.GenerativeModel(MODEL_NAME)
    resp = model.generate_content(
        f"""
Summarize this day of coding:

Functions worked on: {', '.join(set(all_functions[:20]))}

Patches:
{combined[:3000]}

Provide:
1. Main work accomplished
2. Features added/modified
3. Bugs fixed
4. Key decisions
5. Technical debt added
"""
    )

    memory_dir = project_root / ".devmemory" / "memory"
    memory_dir.mkdir(parents=True, exist_ok=True)

    out_path = memory_dir / f"{date}-summary.json"
    summary_data = {
        "date": date,
        "summary": resp.text.strip(),
        "functions_changed": list(set(all_functions)),
        "patches_count": len(matched),
        "generated_at": datetime.now().isoformat(),
    }

    out_path.write_text(json.dumps(summary_data, indent=2))
    return out_path
