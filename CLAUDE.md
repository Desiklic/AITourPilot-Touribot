# TouriBot — Project Handbook

## What This Is

TouriBot is an AI-powered museum outreach assistant for AITourPilot. It helps Hermann draft personalized emails, track a pipeline of museum leads, and learn from every interaction. It has both a CLI interface and a web dashboard.

## Key Files

- `soul.md` — Touri's identity and email drafting principles (DO NOT auto-edit)
- `memory/USER.md` — Hermann's identity (NEVER auto-edit)
- `memory/MEMORY.md` — Working memory (auto-promoted facts)
- `ARCHITECTURE.md` — Full component design and data model
- `args/settings.yaml` — All configuration (memory, models, knowledge sources, email safety)

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
- **API**: `tools/api/` — FastAPI server with chat, file, calendar, and email routes
- **Calendar**: `tools/calendar/google_calendar.py` — Google Calendar provider
- **Email**: `tools/email/zoho_reader.py` + `tools/email/safety.py` — IMAP read + safety infrastructure

### Dashboard (`touri-dashboard/`)
- **Stack**: Next.js 16, React 19, shadcn/ui, Tailwind v4, Recharts, @hello-pangea/dnd
- **Pages**: Pipeline (kanban CRM), Chat, Stats, Calendar, Contacts, Tasks, Memory, Models, Settings
- **DB access**: better-sqlite3 reads `data/leads.db` and `data/memory.db` (WAL mode for concurrent access with Python)
- **Chat**: Connects to FastAPI at :8766 for SSE streaming; supports concurrent sessions and file drag/drop

### Databases
| DB | Location | Used by |
|----|----------|---------|
| `data/leads.db` | Museums, contacts, interactions, research, email queue, audit log | CLI + Dashboard |
| `data/memory.db` | Memories, embeddings, session chunks | CLI + Dashboard |
| `data/conversations.db` | Dashboard chat sessions | FastAPI only |
| `data/research.db` | Deep research state checkpoints | FastAPI only |

## Dashboard Pages

| Page | Route | What it does |
|------|-------|-------------|
| Pipeline CRM | /pipeline | Kanban board — museums tracked from identification to close |
| Chat | /chat | Multi-session streaming chat with Touri + file drag/drop |
| Stats | /stats | Funnel metrics, email stats, activity timeline |
| Calendar | /calendar | Week/Month/Year views with follow-up and demo events |
| Contacts | /contacts | People/Museums toggle — card and table layouts with search/filter/detail sheet |
| Tasks | /tasks | Follow-up task board |
| Memory | /memory | Browse and edit the memory database |
| Models | /models | Model config (read-only) |
| Settings | /settings | App configuration |

## Chat Tools (7 total)

Touri has access to 7 tools via an agentic tool-use loop (max 5 rounds):

| Tool | Capability | Activation |
|------|-----------|-----------|
| `browse_url` | Fetch any web page via Jina Reader | Always available (no key needed) |
| `web_search` | Search the web via Tavily | Needs `TAVILY_API_KEY` in .env |
| `check_calendar` | Read upcoming events and availability | Needs Google OAuth setup (see below) |
| `schedule_event` | Create demo events / follow-up reminders | Needs Google OAuth setup |
| `check_email` | Read Zoho inbox for museum replies (read-only) | Needs `ZOHO_IMAP_USER` + `ZOHO_IMAP_PASSWORD` |
| `list_files` | List files in configured knowledge source folders | Always available |
| `read_file` | Read file content (xlsx, csv, pdf, docx, txt, md, html) | Always available |

Tool calls emit SSE status events so the dashboard shows live progress.

## Knowledge Ingest Pipeline

Config-driven ingest at `args/settings.yaml` → `knowledge.sources`. Three configured sources:

| Label | Path | Glob | Access |
|-------|------|------|--------|
| Business Wiki | `~/Desktop/AITourPilot Project/BUSINESS_CONTENT/wiki` | `**/*.html` | read |
| Marketing Materials | `~/Desktop/AITourPilot Project/Marketing Automation` | `**/*.{txt,md,pdf,docx}` | read |
| Development Docs | `./docs_dev` | `**/*.md` | readwrite |

134 files processed to `knowledge/processed/`. Extractors: html_wiki, md, auto (pdf/docx). Max file size: 10 MB. Path traversal protection on all file endpoints.

To add a new source, append to `knowledge.sources` in `args/settings.yaml` and re-run ingest.

## Memory System 2.0

Museum-centric memory with structured types, Sonnet extraction, and tiered context loading.

### Schema (`data/memory.db` → `memories` table)
| Column | Type | Purpose |
|--------|------|---------|
| `id` | INTEGER PK | Auto-increment |
| `content` | TEXT | The fact/event/insight |
| `type` | TEXT | `contact_intel`, `museum_intel`, `interaction`, `strategy`, `research`, `general` |
| `importance` | INTEGER | 1-10 (8+ = permanent, never auto-expired) |
| `museum_id` | INTEGER | FK to `leads.db.museums.id` (nullable — NULL = global) |
| `tags` | TEXT | JSON array of categorization tags |
| `source` | TEXT | `extraction`, `manual`, `research`, `cli` |
| `created_at` | TIMESTAMP | Auto-set |
| `updated_at` | TIMESTAMP | Auto-set |

### Memory Types
| Type | What it captures |
|------|-----------------|
| `contact_intel` | Person info: role, preferences, communication style, response patterns |
| `museum_intel` | Institution facts: visitor numbers, tech stack, budget cycles, digital maturity |
| `interaction` | Dated events: email sent, meeting held, response received, demo given |
| `strategy` | Campaign learnings: what angles work, timing insights, template performance |
| `research` | Deep research findings auto-bridged from the research engine |
| `general` | Anything else: product facts, business context, Hermann's preferences |

### How extraction works
After every chat turn, **Sonnet** (not Haiku) extracts memories using JSON schema output:
1. **Classify-first gate**: `worth_saving: boolean` — trivial exchanges (greetings, thanks) produce zero writes
2. **Structured extraction**: each memory has `content`, `type`, `importance`, `museum_name`, `tags`
3. **Museum resolution**: museum_name is fuzzy-matched against `leads.db` to get `museum_id`
4. **Dedup check**: cosine similarity > 0.92 → update existing memory instead of creating duplicate
5. **Source tracking**: all auto-extracted memories get `source: "extraction"`

### How search works (RRF)
Search uses **Reciprocal Rank Fusion** (not weighted scoring):
- FTS5 full-text search + vector similarity (384-dim, all-MiniLM-L6-v2) run independently
- Results merged via RRF formula: `score(d) = Σ 1/(60 + rank)`
- When a museum is detected in the conversation, search is **entity-filtered** (museum_id WHERE clause) for precision
- Temporal decay and MMR diversity re-ranking applied post-RRF

### Tiered context assembly
Context is loaded progressively based on what the user is doing:

| Tier | When | What's loaded | Budget |
|------|------|---------------|--------|
| **T1** (always) | Every turn | soul.md, USER.md, business context, pipeline summary, top 5 global memories | ~4K tokens |
| **T2** (museum detected) | User mentions a museum | Museum record, contacts, museum-specific memories, last 3 interactions, research headline | ~4K tokens |
| **T3** (task detected) | Drafting/research/scoring | Email templates, full research doc, detailed history, objection handling | ~8K tokens |

Loading indicators print in CLI (`Loading context for SS Great Britain...`) and emit SSE status events for the dashboard.

### Research → Memory bridge
When deep research completes, key findings are automatically extracted and saved as `research`-type memories linked to the museum_id. This makes research intelligence available to hybrid_search without loading the full report.

### Curator (daily maintenance)
Runs automatically once per day at session start:
- **Expire**: deletes low-importance (<5) old (>90 days) memories of type interaction/general/event
- **Consolidate**: merges near-duplicate memories (cosine >0.85) within the same museum
- Never deletes memories with importance >= 8

## Credentials & Activation

| Capability | Required .env vars | Notes |
|------------|-------------------|-------|
| Core chat | `ANTHROPIC_API_KEY` | Always required |
| Web search | `TAVILY_API_KEY` | Without this, `web_search` tool returns error |
| Browser fetch | _(none)_ | Jina Reader is free, no key needed |
| Google Calendar | `GOOGLE_CALENDAR_CLIENT_ID`, `GOOGLE_CALENDAR_CLIENT_SECRET` | After setting vars, run OAuth flow: `python -c "from tools.calendar.google_calendar import authenticate; authenticate()"`. Token stored at `~/.touribot/google_token.json` |
| Zoho Email | `ZOHO_IMAP_USER`, `ZOHO_IMAP_PASSWORD` | App-specific password from Zoho. Inbox read-only. Auto-send kill switch defaults to false |
| Deep research | `TAVILY_API_KEY` | Same key as web search |

## Email Safety

The email system has layered safety controls:

- **Kill switch** (`settings.yaml → email.automated_send_enabled`): read at execution time, never cached. Defaults to `false`
- **.com account hard rule**: `hermann@aitourpilot.com` **never auto-sends** — code-level constraint in `tools/email/safety.py` regardless of kill switch
- **Rate limits**: 3/day .com (hardcoded floor), 20/day .co (configurable)
- **Duplicate detection**: 7-day recipient block + 30-day content hash block
- **Approval queue**: all emails must be manually approved via `/api/email/queue/{id}/approve`
- **Audit log**: every approve/cancel action logged to `email_audit_log` table in `leads.db`

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
- Do NOT modify: `tools/leads/lead_db.py`, `tools/outreach/*.py`, `run.py`
- Memory system (`tools/memory/`, `tools/chat/session.py`) may be modified for memory improvements only — with a plan documented in `docs_dev/`
- New Python files go in `tools/api/` or `tools/research/`
- Always back up `data/memory.db` before schema migrations
