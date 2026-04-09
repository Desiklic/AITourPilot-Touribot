# TouriBot — Project Handbook

## What This Is

TouriBot is an AI-powered museum outreach assistant for AITourPilot. It helps Hermann draft personalized emails, track a pipeline of museum leads, and learn from every interaction. It has both a CLI interface and a web dashboard.

## Key Files

- `soul.md` — Touri's identity and email drafting principles (DO NOT auto-edit)
- `memory/USER.md` — Hermann's identity (NEVER auto-edit)
- `memory/MEMORY.md` — Working memory (auto-promoted facts)
- `ARCHITECTURE.md` — Full component design and data model
- `args/settings.yaml` — All configuration

## Running

### CLI (standalone, no servers needed)
```bash
python run.py chat                    # Interactive chat with Touri
python run.py recall "<query>"        # Search memory
python run.py remember "<fact>"       # Save a fact
python run.py pipeline                # Show pipeline overview
python run.py status                  # Quick briefing
```

### Dashboard (persistent servers via macOS launchd)

| Service | Port | Purpose |
|---------|------|---------|
| **Dashboard** (Next.js) | **4003** | Web UI — http://localhost:4003 |
| **FastAPI** (Python) | **8766** | Chat backend — streams Touri's responses to browser, handles research |

Both run as macOS LaunchAgents — auto-start on login, auto-restart on crash. Logs: `logs/dashboard.log`, `logs/api.log`.

```bash
# Management
launchctl load   ~/Library/LaunchAgents/com.touribot.dashboard.plist   # Start dashboard
launchctl load   ~/Library/LaunchAgents/com.touribot.api.plist         # Start API
launchctl unload ~/Library/LaunchAgents/com.touribot.dashboard.plist   # Stop dashboard
launchctl unload ~/Library/LaunchAgents/com.touribot.api.plist         # Stop API

# Logs
tail -f logs/dashboard.log
tail -f logs/api.log
```

**Port map (all bots):** HenryBot=4001, FelixBot=4002, TouriBot=4003

## Architecture

### Python Backend
- **Memory**: `tools/memory/` — SQLite + FTS5 + vector search (from HenryBot)
- **Chat**: `tools/chat/session.py` — Context assembly, Anthropic API, memory extraction
- **Leads**: `tools/leads/` — Museum pipeline database (55 museums, 76 contacts)
- **Outreach**: `tools/outreach/` — Email drafting engine
- **Research**: `tools/research/` — Deep research engine (Tavily web search + Jina reader + Anthropic synthesis)
- **API**: `tools/api/` — FastAPI server wrapping session.py for dashboard streaming

### Dashboard (`touri-dashboard/`)
- **Stack**: Next.js 16, React 19, shadcn/ui, Tailwind v4, Recharts, @hello-pangea/dnd
- **Pages**: Pipeline (kanban CRM), Chat, Stats, Calendar, Tasks, Memory, Models, Settings
- **DB access**: better-sqlite3 reads `data/leads.db` and `data/memory.db` (WAL mode for concurrent access with Python)
- **Chat**: Connects to FastAPI at :8766 for SSE streaming

### Databases
| DB | Location | Used by |
|----|----------|---------|
| `data/leads.db` | Museums, contacts, interactions, research | CLI + Dashboard |
| `data/memory.db` | Memories, embeddings, session chunks | CLI + Dashboard |
| `data/conversations.db` | Dashboard chat sessions | FastAPI only |
| `data/research.db` | Deep research state checkpoints | FastAPI only |

## Memory System — How It Actually Works

Touri's memory uses `data/memory.db` with FTS5 full-text search + vector embeddings (hybrid_search: 70% vector + 30% FTS5). After every chat turn, Haiku extracts facts/events/insights and saves them.

**The `[MUSEUM: X]` tag is NOT a structured field.** There is no `tags` column in the live schema. The tag is plain text inside the `content` field. It improves search ranking because FTS5 and vector search match on it, but there is no tag-based filtering. This is by design — pragmatic for 50-150 memories.

**Memory extraction quality varies.** The Haiku model sometimes saves meta-commentary or uncertain statements as facts. When reviewing memories via `python run.py recall "<query>"`, look for junk entries and consider manually cleaning `data/memory.db` if needed.

**Context injection:** `session.py` runs `hybrid_search(query, limit=5)` per chat turn and injects the top-5 matches as a `## Relevant Memories` block in the user message. Memories with score < 0.1 are filtered out.

## Constraints

- Python 3.12 (Miniforge comfyenv)
- Anthropic SDK for LLM calls (not Agent SDK)
- SQLite for all persistence (WAL mode for concurrent reads)
- Emails always sent manually from hermann@aitourpilot.com (Zoho, .com domain)
- Never exceed 3 emails/day from .com domain
- Dashboard files live in `touri-dashboard/` — delete it to rollback, CLI unaffected

## Safety

- `.env` contains secrets — NEVER commit
- `memory/USER.md` is sacred — NEVER auto-modify
- `soul.md` is locked — only Hermann edits
- All email drafts saved to `output/emails/` before display
- Do NOT modify: `tools/memory/*.py`, `tools/chat/session.py`, `tools/leads/lead_db.py`, `tools/outreach/*.py`, `run.py`
- New Python files only in `tools/api/` and `tools/research/`
