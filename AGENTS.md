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
| DELETE | /api/chat/memory/{id} | Delete a memory |
| PATCH | /api/chat/memory/{id} | Edit a memory (content, type, importance, museum_id) |
| POST | /api/chat/research | Start deep research (background) |
| GET | /api/chat/research | List research sessions |
| GET | /api/chat/research/{id} | Get research status |
| GET | /api/chat/research/{id}/report | Get research report |

## Memory System 2.0

### Schema
The `memories` table has: `id, content, type, importance, museum_id, tags, source, created_at, updated_at`.

- **`museum_id`** is a nullable FK to `leads.db.museums.id`. When set, the memory is linked to a specific museum. When NULL, it's a global memory.
- **`tags`** is a JSON array string for flexible categorization.
- **`source`** tracks provenance: `extraction` (auto-extracted from chat), `manual`, `research` (from deep research bridge), `cli`.

### Memory Types
Use domain-specific types, NOT the old generic ones:
- `contact_intel` — person info (role, preferences, communication style)
- `museum_intel` — institution facts (visitor numbers, tech stack, budget cycles)
- `interaction` — dated events (email sent, meeting held, response received)
- `strategy` — campaign learnings (what angles work, timing insights)
- `research` — deep research findings (auto-bridged from research engine)
- `general` — anything else

Legacy types (`fact`, `event`, `insight`, `error`) still exist in some old memories but should NOT be used for new writes.

### Extraction
Memory extraction uses **Sonnet** (claude-sonnet-4-6) with JSON schema output. The extraction includes:
1. A `worth_saving: boolean` gate — trivial exchanges produce zero writes
2. Structured fields: `content`, `type`, `importance`, `museum_name`, `tags`
3. Museum name resolution: `_resolve_museum_id()` fuzzy-matches against leads.db

### Search (RRF)
`hybrid_search(query, limit, include_sessions, museum_id)` uses **Reciprocal Rank Fusion**:
- Runs FTS5 + vector search independently, merges via RRF formula
- When `museum_id` is provided: museum-filtered results rank higher than global
- Score range: ~0.001-0.03 (much smaller than the old 0-1 range)
- Downstream score threshold: 0.005 (not 0.1)

### Tiered Context
`_assemble_context(user_message)` in session.py loads context progressively:
- **Tier 1** (always): soul.md + USER.md + pipeline summary + top global memories (~4K tokens)
- **Tier 2** (museum detected): museum record + contacts + museum memories + interactions (~4K tokens)
- **Tier 3** (drafting/research): email templates + research doc + full history (~8K tokens)

Museum detection: `_detect_museum(message)` fuzzy-matches against leads.db museum names.

### Research Bridge
When `tools/research/orchestrator.py` completes a research session, `_bridge_to_memory()` auto-extracts key findings and writes them as `research`-type memories with the museum_id. Max 10 memories per research session.

### Curator
Runs daily at session start via `_maybe_run_curator()`:
- Expires low-importance old memories (type interaction/general/event, importance <5, >90 days)
- Consolidates near-duplicates (cosine >0.85 within same museum_id)
- Never deletes importance >= 8

### Writing Memories
```python
from tools.memory.memory_write import write_memory
write_memory(
    content="Lisa Witschnig prefers German-language emails",
    memory_type="contact_intel",    # use domain types
    importance=7,
    museum_id=1,                     # FK to leads.db museums.id
    source="extraction",             # or "manual", "research", "cli"
    tags='["language", "preference"]',  # JSON string
)
```

### Searching Memories
```python
from tools.memory.memory_db import hybrid_search, list_memories
# Global search
results = hybrid_search("email strategy", limit=10)
# Museum-filtered search
results = hybrid_search("contact", museum_id=1, limit=10)
# List by type
results = list_memories(limit=20, memory_type="contact_intel", museum_id=1)
```

## Files NOT to Modify

These backend files are stable and must not be changed without explicit instruction:
- `tools/leads/lead_db.py` — Lead database CRUD
- `tools/leads/pipeline.py` — Pipeline display
- `tools/outreach/*.py` — Email drafting engine (except personalizer.py for memory integration)
- `run.py` — CLI entry point
- `soul.md` — Touri's identity
- `memory/USER.md` — Hermann's identity

Memory system files (`tools/memory/`, `tools/chat/session.py`) may be modified for memory improvements — always with a plan in `docs_dev/` and a backup of `data/memory.db`.

New Python code goes in `tools/api/` (FastAPI) or `tools/research/` (deep research).
Dashboard code goes in `touri-dashboard/`.

## Environment

- **Python**: 3.12 via Miniforge comfyenv (`/Users/hermannkudlich/Documents/Miniforge3/envs/comfyenv/bin/python`)
- **Node.js**: v20.19.2 via nvm (`/Users/hermannkudlich/.nvm/versions/node/v20.19.2/bin/node`)
- **API keys**: In `.env` (ANTHROPIC_API_KEY, optionally TAVILY_API_KEY for deep research)
