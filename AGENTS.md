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
- The **Dashboard** (Next.js) serves the web UI and reads databases directly via better-sqlite3 for pipeline, stats, calendar, contacts, memory, and settings pages.
- The **FastAPI** (Python) handles chat streaming, conversation persistence, tool execution, and deep research. The dashboard calls it at `http://localhost:8766` for anything that needs the Anthropic API or Python backend logic.
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
| Contacts | /contacts | `data/leads.db` via better-sqlite3 |
| Tasks | /tasks | `data/leads.db` via better-sqlite3 |
| Memory | /memory | `data/memory.db` via better-sqlite3 |
| Models | /models | Hardcoded config (read-only) |
| Settings | /settings | `data/leads.db` + `data/memory.db` |

## FastAPI Endpoints

### Chat
| Method | Path | Purpose |
|--------|------|---------|
| POST | /api/chat/stream | SSE streaming chat with Touri (with agentic tool-use loop) |
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

### Files
| Method | Path | Purpose |
|--------|------|---------|
| GET | /api/files/list | List files in a configured knowledge source (`?source_label=Business+Wiki`) |
| GET | /api/files/read | Read a single file (`?source_label=...&path=relative/path.html`) |

### Calendar
| Method | Path | Purpose |
|--------|------|---------|
| GET | /api/calendar/events | Upcoming events (`?days=14`). Returns 503 if OAuth not configured |
| GET | /api/calendar/availability | Free/busy slots (`?start=...&end=...` ISO 8601). Returns 503 if not configured |
| POST | /api/calendar/events | Create event or reminder (body: `title`, `start`, `end`, `type`, `description`, `attendee_email`) |

### Email
| Method | Path | Purpose |
|--------|------|---------|
| GET | /api/email/inbox | Check Zoho inbox (`?days=7&contacts_only=true`). Returns 503 if not configured |
| GET | /api/email/queue | List email approval queue (`?status=PENDING_APPROVAL&limit=50`) |
| POST | /api/email/queue/{id}/approve | Approve a queued email (moves to APPROVED; does not send) |
| POST | /api/email/queue/{id}/cancel | Cancel a queued email (moves to CANCELLED) |
| GET | /api/email/audit | View audit log (`?queue_id=...&limit=100`) |
| GET | /api/email/status | Kill switch state and rate limit counters (no credentials needed) |

## Chat Tool Registry (7 tools)

Tools are registered in `tools/api/tool_registry.py` and dispatched from `tools/api/chat_handler.py`. The agentic loop runs up to **5 rounds** of tool calls per user message.

| Tool name | Module | What it does | Credential needed |
|-----------|--------|-------------|------------------|
| `browse_url` | `browse_tools.py` | Fetches a URL via Jina Reader and returns rendered text | None |
| `web_search` | `browse_tools.py` | Searches the web via Tavily; returns top results with snippets | `TAVILY_API_KEY` |
| `check_calendar` | `calendar_tools.py` | Returns upcoming Google Calendar events and free/busy slots | Google OAuth |
| `schedule_event` | `calendar_tools.py` | Creates a demo event or all-day reminder on Google Calendar | Google OAuth |
| `check_email` | `email_tools.py` | Reads recent Zoho inbox messages from known CRM contacts (read-only) | `ZOHO_IMAP_USER`, `ZOHO_IMAP_PASSWORD` |
| `list_files` | `file_tools.py` | Lists files in a configured knowledge source folder | None |
| `read_file` | `file_tools.py` | Reads a file (txt, md, html, csv, xlsx, pdf, docx) | None |

Tools that require unconfigured credentials return a plain-text error string — they never crash the chat loop.

SSE events emitted during tool execution:
- `status` — what tool is running (`"Searching the web..."`, `"Reading file..."`)
- `tool_result` — summary of what was found

To add a new tool: implement it in `tools/api/`, add its spec to the `*_TOOLS` list, add its name to the name set and dispatch in `tool_registry.py`.

## File System Access (T1)

### Configuration
Sources are defined in `args/settings.yaml` → `knowledge.sources`:

```yaml
knowledge:
  sources:
    - path: ~/Desktop/AITourPilot Project/BUSINESS_CONTENT/wiki
      glob: "**/*.html"
      extractor: html_wiki
      access: read
      label: "Business Wiki"
    - path: ~/Desktop/AITourPilot Project/Marketing Automation
      glob: "**/*.{txt,md,pdf,docx}"
      extractor: auto
      access: read
      label: "Marketing Materials"
      exclude_patterns: ["*.png", "*.jpg", "*.gif", "*.svg", ".git/**", "*.csv", "*.xlsx"]
    - path: ./docs_dev
      glob: "**/*.md"
      extractor: md
      access: readwrite
      label: "Development Docs"
  output_dir: knowledge/processed
  max_file_size_mb: 10
```

### Security
- Path traversal protection: all resolved paths verified to sit within the configured source root before opening
- Absolute paths (e.g. `/etc/passwd`) rejected with 403
- Files exceeding `max_file_size_mb` return 413
- API bound to `127.0.0.1` only — not exposed to the internet
- `access: read` sources are read-only; `readwrite` sources allow future write endpoints

### Knowledge ingest
134 files processed to `knowledge/processed/`. Extractors handle html (BeautifulSoup), md (plain read), auto (pdf via pdfminer, docx via python-docx). Re-run ingest after adding new sources.

## Browser Access (T2)

- `browse_url` — Jina Reader (`r.jina.ai/<url>`). Returns rendered text. Free, no key.
- `web_search` — Tavily API. Returns top N results with title, URL, snippet. Needs `TAVILY_API_KEY`.
- Both are implemented in `tools/api/browse_tools.py`.
- Errors (network failure, Tavily not configured) return a plain-text error string — the loop continues.

## Calendar Access (T3)

### Setup (one-time OAuth)
1. Create a Google Cloud project, enable Google Calendar API, create OAuth 2.0 credentials (Desktop app type).
2. Add to `.env`:
   ```
   GOOGLE_CALENDAR_CLIENT_ID=...
   GOOGLE_CALENDAR_CLIENT_SECRET=...
   ```
3. Run the OAuth flow:
   ```bash
   python -c "from tools.calendar.google_calendar import authenticate; authenticate()"
   ```
4. Token stored at `~/.touribot/google_token.json`. Refreshed automatically.

### Behavior when not configured
All calendar endpoints return HTTP 503 with a human-readable message. The `check_calendar` and `schedule_event` chat tools return a plain-text error — Touri will tell the user to set up OAuth.

### Calendar config in settings.yaml
```yaml
calendar:
  enabled: true
  google:
    token_file: "~/.touribot/google_token.json"
    scopes:
      - "https://www.googleapis.com/auth/calendar"
```

## Email Access (T4)

### Components
- `tools/email/zoho_reader.py` — IMAP reader (read-only access to Zoho inbox)
- `tools/email/safety.py` — kill switch, rate limits, duplicate detection, queue, audit log

### Setup
Add to `.env`:
```
ZOHO_IMAP_USER=hermann@aitourpilot.com
ZOHO_IMAP_PASSWORD=<app-specific-password>
```
Generate an app-specific password in Zoho Mail → Security → App Passwords.

### Safety guardrails
| Guardrail | Details |
|-----------|---------|
| Kill switch | `settings.yaml → email.automated_send_enabled`. Read at send time, never cached. Defaults to `false` |
| .com hard rule | `hermann@aitourpilot.com` never auto-sends — hardcoded in `safety.py`, not overridable by config |
| Rate limits | 3/day .com (hardcoded floor); 20/day .co (configurable, floor hardcoded) |
| Recipient dedup | Block same recipient within 7 days |
| Content dedup | Block same content hash within 30 days |
| Approval queue | All sends must go through `email_queue` → PENDING_APPROVAL → APPROVED before sending |
| Audit log | Every status change logged to `email_audit_log` table in `leads.db` |

### Queue status flow
```
PENDING_APPROVAL → APPROVED → SENDING → SENT
                → CANCELLED (any pre-SENT state)
                → FAILED
```

### Email config in settings.yaml
```yaml
email:
  automated_send_enabled: false   # THE KILL SWITCH — keep false until Phase E4
  daily_limit_com: 3
  daily_limit_co: 20
  safety:
    recipient_dedup_days: 7
    content_dedup_days: 30
    require_approval: true
```

## Contacts Page (/contacts)

### Views
- **People view**: lists individual contacts. Card layout (default) or table layout. Each card shows name, role, museum, email, last interaction date, source badge.
- **Museums view**: lists museums. Museum cards show museum name, location, stage, contact list.

### Filters and search
- Full-text search across name, role, museum
- Source filter (CRM contacts, imported, etc.)
- Engagement filter (active, inactive, etc.)

### Contact detail sheet
Slide-in sheet on card/row click shows:
- Contact metadata (name, role, email, phone, LinkedIn)
- Interaction history
- Linked memories
- Follow-up tasks
- Cross-links to Pipeline, Chat, Calendar, Memory pages

### Data model
Data is read from `data/leads.db` via better-sqlite3 at request time (no FastAPI involvement). Tables: `museums`, `contacts`, `interactions`.

## Calendar Page (/calendar)

### Views
| View | File | Description |
|------|------|-------------|
| Week | `week-view.tsx` | 7-day columns, hour-based event placement |
| Month | `month-view.tsx` | Traditional month grid with event chips |
| Year | `year-view.tsx` | 12-month overview; click day to jump to week view |

Cross-view navigation: click a day in Year → opens Week view at that week. Click a day in Month → opens Week view at that week.

Controls: tab switcher (Week/Month/Year), back/forward arrows, Today button, refresh.

Color coding: amber = follow-up, cyan = demo, red = overdue.

## Chat: Concurrent Sessions

- Each session tracks its own streaming state via `streamingSessions: Set<string>` in React state.
- Users can switch between sessions while one is streaming — the background stream completes silently.
- On switching back to a completed session, messages are reloaded automatically.
- The `sending` prop passed to `ChatInput` is `streamingSessions.has(sessionId)` — per-session, not global.

## Chat: File Drag/Drop

- `ChatInput` is a `forwardRef` component exposing an `addFiles(files)` imperative handle.
- A global drag overlay (frosted glass UX) captures drag events on the chat page and calls `addFiles`.
- File handling:
  - Images → converted to base64, sent as Anthropic vision blocks (`image_url` content)
  - Documents (pdf, docx, txt, csv, xlsx) → text extracted client-side, sent as text blocks
- Limits: 10 MB per file, 5 files max per message.

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
- **Required .env keys**:
  - `ANTHROPIC_API_KEY` — always required
  - `TAVILY_API_KEY` — for web_search tool and deep research
  - `GOOGLE_CALENDAR_CLIENT_ID` + `GOOGLE_CALENDAR_CLIENT_SECRET` — for calendar tools (OAuth flow needed after setting)
  - `ZOHO_IMAP_USER` + `ZOHO_IMAP_PASSWORD` — for check_email tool (app-specific password from Zoho)
