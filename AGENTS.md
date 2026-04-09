# TouriBot — Agent Instructions

## Server Architecture

TouriBot runs two persistent servers via macOS LaunchAgents. They auto-start on login and auto-restart on crash.

| Service | Port | Process | Plist |
|---------|------|---------|-------|
| **Dashboard** | **4003** | Next.js dev server | `com.touribot.dashboard` |
| **FastAPI** | **8766** | Python uvicorn | `com.touribot.api` |

**Dashboard URL:** http://localhost:4003
**API URL:** http://localhost:8766
**API docs:** http://localhost:8766/docs

### How they relate
- The **Dashboard** (Next.js) serves the web UI and reads databases directly via better-sqlite3 for pipeline, stats, calendar, memory, and settings pages.
- The **FastAPI** (Python) handles chat streaming, conversation persistence, and deep research. The dashboard calls it at `http://localhost:8766` for anything that needs the Anthropic API or Python backend logic.
- Both access `data/leads.db` and `data/memory.db` concurrently — WAL mode is enabled on all connections.

### Port map (all bots on this machine)
| Bot | Dashboard | API |
|-----|-----------|-----|
| HenryBot | 4001 | — |
| FelixBot | 4002 | — |
| **TouriBot** | **4003** | **8766** |

Do NOT use ports 3000, 4001, 4002, or 8765 — they conflict with other services.

## Server Management

```bash
# Check if running
curl -s http://localhost:4003 -o /dev/null -w "%{http_code}"   # 200/307 = OK
curl -s http://localhost:8766/docs -o /dev/null -w "%{http_code}" # 200 = OK

# Restart (unload + load)
launchctl unload ~/Library/LaunchAgents/com.touribot.dashboard.plist
launchctl load   ~/Library/LaunchAgents/com.touribot.dashboard.plist

launchctl unload ~/Library/LaunchAgents/com.touribot.api.plist
launchctl load   ~/Library/LaunchAgents/com.touribot.api.plist

# View logs
tail -f logs/dashboard.log
tail -f logs/api.log

# After making code changes to the dashboard, the Next.js dev server auto-reloads.
# After making code changes to tools/api/, restart the API service:
launchctl unload ~/Library/LaunchAgents/com.touribot.api.plist
launchctl load   ~/Library/LaunchAgents/com.touribot.api.plist
```

## Launchd Plist Locations

- Source (in repo): `launchd/com.touribot.dashboard.plist`, `launchd/com.touribot.api.plist`
- Installed: `~/Library/LaunchAgents/com.touribot.dashboard.plist`, `~/Library/LaunchAgents/com.touribot.api.plist`

After modifying a plist, copy it to `~/Library/LaunchAgents/` and reload:
```bash
cp launchd/com.touribot.dashboard.plist ~/Library/LaunchAgents/
launchctl unload ~/Library/LaunchAgents/com.touribot.dashboard.plist
launchctl load   ~/Library/LaunchAgents/com.touribot.dashboard.plist
```

## Dashboard Structure (`touri-dashboard/`)

| Page | Route | Data source |
|------|-------|-------------|
| Pipeline CRM | /pipeline | `data/leads.db` via better-sqlite3 |
| Chat | /chat | FastAPI :8766 via SSE |
| Stats | /stats | `data/leads.db` via better-sqlite3 |
| Calendar | /calendar | `data/leads.db` via better-sqlite3 |
| Tasks | /tasks | `data/leads.db` via better-sqlite3 |
| Memory | /memory | `data/memory.db` via better-sqlite3 |
| Models | /models | Hardcoded config (read-only) |
| Settings | /settings | `data/leads.db` + `data/memory.db` |

## FastAPI Endpoints

| Method | Path | Purpose |
|--------|------|---------|
| POST | /api/chat/stream | SSE streaming chat with Touri |
| GET | /api/chat/sessions | List chat sessions |
| GET | /api/chat/messages | Get messages (supports polling via since_id) |
| PATCH | /api/chat/sessions | Rename a session |
| DELETE | /api/chat/sessions/{id} | Delete a session |
| POST | /api/chat/research | Start deep research (background) |
| GET | /api/chat/research | List research sessions |
| GET | /api/chat/research/{id} | Get research status |
| GET | /api/chat/research/{id}/report | Get research report |

## Files NOT to Modify

These backend files are stable and must not be changed:
- `tools/memory/*.py` — Memory system (from HenryBot)
- `tools/chat/session.py` — Chat session logic
- `tools/leads/lead_db.py` — Lead database CRUD
- `tools/outreach/*.py` — Email drafting engine
- `run.py` — CLI entry point
- `soul.md` — Touri's identity
- `memory/USER.md` — Hermann's identity

New Python code goes in `tools/api/` (FastAPI) or `tools/research/` (deep research).
Dashboard code goes in `touri-dashboard/`.

## Environment

- **Python**: 3.12 via Miniforge comfyenv (`/Users/hermannkudlich/Documents/Miniforge3/envs/comfyenv/bin/python`)
- **Node.js**: v20.19.2 via nvm (`/Users/hermannkudlich/.nvm/versions/node/v20.19.2/bin/node`)
- **API keys**: In `.env` (ANTHROPIC_API_KEY, optionally TAVILY_API_KEY for deep research)
