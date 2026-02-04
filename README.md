# DevMemory

**AI-powered context restoration for developers**

Stop wasting 20 minutes remembering what you were working on. DevMemory automatically tracks your coding sessions and helps you pick up exactly where you left off.

---

## The Problem

> "I opened my project after a break and spent 20 minutes just remembering what I was doing."

Git commits don't capture your **thought process** or **session context**. DevMemory does.

---

## What It Does

### Session-Based Tracking
```bash
# Start working
devmemory start
> What are you working on? Implementing passwordless login

# Add notes as you code
devmemory note add "Added magic link endpoint"
devmemory note add "TODO: rate-limit email send"

# Stop when done
devmemory stop
```

### Smart File Watching
- **Event-driven snapshots** using `watchdog` - no polling lag
- **Debounced captures** - waits 1s after you stop typing
- **Shadow git repo** - tracks changes without touching your main history
- **Incremental sync** - only copies files that actually changed

### Web Dashboard
```bash
devmemory dashboard run
# View at http://localhost:5173
```

**Features:**
- Session timeline with notes
- Diff viewer for each snapshot
- Activity heatmap & coding streaks
- AI summaries powered by Google Gemini

---

## Quick Start

### Install
```bash
# Clone and install CLI
git clone https://github.com/DevelopedBy-Siva/dev-memory.git
cd dev-memory/cli
python -m venv .venv
source .venv/bin/activate
pip install -e .

# Install dashboard
cd dashboard && npm install
```

### Setup
```bash
export GENAI_KEY="your-gemini-api-key"
```

### Use
```bash
cd your-project
devmemory start
# Code...
devmemory stop
devmemory dashboard run
```

---

## Commands

| Command | Description |
|---------|-------------|
| `devmemory start` | Start tracking session |
| `devmemory stop` | Stop and archive session |
| `devmemory note add "..."` | Add context note |
| `devmemory note list` | View session notes |
| `devmemory status` | Check daemon status |
| `devmemory dashboard run` | Launch web UI |
| `devmemory logs` | View daemon logs |

---

## Architecture
```
devmemory CLI
    │
    ├── File Watcher Daemon (watchdog)
    │   └── Shadow Git Repo (.devmemory/repo)
    │       └── Patches + Snapshots
    │
    └── Dashboard (FastAPI + Vue)
        └── Session Viewer + AI Summaries
```

**Key Components:**
- **Incremental state diffing** - tracks file mtime/size
- **Shadow git repo** - separate history for DevMemory
- **Debounced events** - smart snapshot timing
- **Time-window filtering** - map patches to sessions

---

## Privacy

- **100% local** - all data in `.devmemory/` folder
- **No telemetry** - no tracking, no cloud sync
- **AI** - calls Gemini when you request summaries

Add `.devmemory/` to your `.gitignore`.

---

## Technical Highlights

- Event-driven architecture with watchdog file monitoring
- Incremental state diffing using mtime/size comparison
- Shadow git repository pattern for clean history separation
- Time-series analysis for streaks and activity heatmaps
- Multi-source AI prompts combining notes + code signals

