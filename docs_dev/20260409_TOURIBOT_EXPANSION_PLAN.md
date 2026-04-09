# TouriBot Expansion Plan — File System, Browser, Calendar, Email

**Date:** 2026-04-09
**Project:** AITourPilot-Touribot
**Author:** Expansion Planning Agent
**Status:** Ready for review
**Prerequisite:** Phases 1-5 complete (memory, knowledge, outreach, pipeline, CRM)

---

## 1. Executive Summary

TouriBot is alive and effective: it drafts personalized museum outreach, tracks a CRM pipeline of 30+ leads, maintains cross-session memory, and runs deep research. But today it operates in a closed loop. Hermann must manually copy-paste emails, manually check his calendar, manually look up business documents, and manually browse museum websites to feed Touri context.

This plan opens TouriBot to the outside world through four capability expansions:

1. **File System Access** — Touri reads AITourPilot business content (wiki, marketing materials, sales decks) directly from disk, eliminating the manual knowledge-feeding bottleneck. The existing ingest pipeline becomes config-driven and gains PDF/DOCX/TXT extractors.

2. **Browser Access** — Touri browses museum websites and searches the web during chat, using existing Jina Reader and Tavily infrastructure that is currently wired only into the deep research pipeline.

3. **Calendar Access** — Touri reads Google Calendar to know Hermann's availability, creates demo events, and sets follow-up reminders. Builds on HenryBot's proven Google Calendar provider pattern.

4. **Email Access** — The most sensitive expansion. Touri reads inbound email from both accounts (Zoho IMAP for .com, Instantly webhook for .co), creates drafts in Zoho, and eventually auto-sends cold outreach via Instantly with a defense-in-depth safety system. Every email passes through a queue-based approval workflow with rate limiting, duplicate detection, and a system-level kill switch.

Together, these four capabilities transform TouriBot from a drafting assistant into a genuine outreach co-pilot that can see Hermann's full business context, research targets in real time, schedule meetings, and manage email workflows — all without leaving the chat interface.

**Estimated total effort:** 12-16 working days across all four tasks.

---

## 2. Task 1: File System Access

### Goal

Touri reads AITourPilot business documents (wiki, marketing materials, sales decks) directly from disk via a config-driven folder registry, eliminating manual copy-paste into the knowledge base.

### Current State

- `tools/knowledge/ingest.py` processes 5 hardcoded wiki HTML sources into `knowledge/processed/`
- Extraction is limited to HTML files with embedded `window.__MD_EN` markdown
- No support for .txt, .md, .pdf, .docx formats
- No ability to browse or read files on demand from the dashboard/chat
- Three target folders identified on disk:
  - `~/Desktop/AITourPilot Project/BUSINESS_CONTENT/` — 86 meaningful files, mostly HTML with embedded markdown
  - `~/Documents/ClaudeProjects/AITourPilot-Touribot/docs_dev/` — development documents
  - `~/Desktop/AITourPilot Project/Marketing Automation/` — 203 files (40 txt, 10 md, 10 pdf, 2 docx, 101 images)

### Phase F1: Config-Driven Ingest Pipeline (1-2 days)

**Goal:** Replace hardcoded SOURCES list with a settings.yaml-driven folder registry. Add extractors for .txt, .md, .pdf, .docx.

**Files to modify:**
- `tools/knowledge/ingest.py` — Refactor to read sources from settings.yaml; add format extractors
- `args/settings.yaml` — Add `knowledge.sources` section

**Files to create:**
- `tools/knowledge/extractors.py` (~150 lines) — Format-specific extractors: `extract_html()`, `extract_txt()`, `extract_md()`, `extract_pdf()`, `extract_docx()`

**Design:**

```yaml
# args/settings.yaml addition
knowledge:
  sources:
    - path: ~/Desktop/AITourPilot Project/BUSINESS_CONTENT/wiki
      glob: "**/*.html"
      extractor: html_wiki    # Uses existing window.__MD_EN extraction
      access: read
      label: "Business Wiki"
    - path: ~/Desktop/AITourPilot Project/Marketing Automation
      glob: "**/*.{txt,md,pdf,docx}"
      extractor: auto          # Detect by extension
      access: read
      label: "Marketing Materials"
      exclude_patterns:
        - "*.png"
        - "*.jpg"
        - "*.gif"
        - ".git/**"
    - path: ./docs_dev
      glob: "**/*.md"
      extractor: md
      access: readwrite
      label: "Development Docs"
  output_dir: knowledge/processed
  max_file_size_mb: 10
```

**Extraction logic:**

| Format | Extractor | Library | Notes |
|--------|-----------|---------|-------|
| .html | `extract_html()` | Existing `_extract_markdown_from_html()` | Wiki pages with `window.__MD_EN` |
| .txt | `extract_txt()` | Built-in | Direct read, add title header |
| .md | `extract_md()` | Built-in | Direct read, preserve frontmatter |
| .pdf | `extract_pdf()` | `pdfplumber` | Text extraction with page markers |
| .docx | `extract_docx()` | `python-docx` | Paragraph + table extraction |

**Verification:**
1. `python run.py ingest --list` shows all three folder sources with file counts
2. `python run.py ingest` processes all supported files, skips images
3. `knowledge/processed/` contains extracted markdown from all three sources
4. Re-running `ingest` is idempotent (same output, no duplicates)
5. Adding a new folder requires only a settings.yaml edit, no code change

### Phase F2: File Access API Layer (1-2 days)

**Goal:** Dashboard and chat can browse and read files from allowed folders via API endpoints.

**Files to create:**
- `tools/api/file_handler.py` (~200 lines) — FastAPI router with file list/read endpoints

**Files to modify:**
- `tools/api/server.py` — Mount file_handler router
- `args/settings.yaml` — Uses same `knowledge.sources` for folder allowlist

**Endpoints:**

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/files/list` | List files in an allowed folder. Query: `source_label`, `glob` |
| GET | `/api/files/read` | Read a single file. Query: `path` (must be within allowlist) |

**Security:**
- Path traversal protection: resolve real path, verify it falls within an allowed source path
- Read-only for BUSINESS_CONTENT and Marketing Automation; read-write for docs_dev only
- File size cap from `knowledge.max_file_size_mb` setting
- No execution, no writes to read-only sources

**Verification:**
1. `GET /api/files/list?source_label=Business+Wiki` returns file list
2. `GET /api/files/read?path=...` returns file content for allowed paths
3. `GET /api/files/read?path=/etc/passwd` returns 403 Forbidden
4. `GET /api/files/read?path=../../.env` returns 403 Forbidden

### Phase F3: Chat Integration (0.5 days)

**Goal:** Touri automatically loads relevant marketing content when task type requires it.

**Files to modify:**
- `tools/chat/session.py` — Add `"marketing"` task type to `_detect_task_type()`; load marketing content in `_build_tier3_context()` when detected

**Detection keywords:** marketing, campaign, linkedin, newsletter, automation, content, social, advertising, brand

**Verification:**
1. Chat: "What marketing campaigns have we run?" loads marketing folder content
2. Chat: "Draft an email for Joanneum" does NOT load marketing content (stays focused on outreach)

### Safety Considerations

- Source folders are read from disk at ingest/query time; Touri never modifies originals (except docs_dev)
- Images excluded from text ingest (waste of tokens, no value for text-based context)
- `.git` directories excluded via `exclude_patterns`
- PDF extraction limited to text; scanned image-PDFs will produce empty output (acceptable)
- File access API is local-only (127.0.0.1); no exposure to internet

### Estimated Effort

| Phase | Days | Depends On |
|-------|------|------------|
| F1: Config-driven ingest | 1-2 | Nothing |
| F2: File access API | 1-2 | F1 (uses same config) |
| F3: Chat integration | 0.5 | F1 |
| **Total** | **2.5-4.5** | |

---

## 3. Task 2: Browser Access

### Goal

Touri browses museum websites and searches the web during dashboard chat, using existing Jina Reader and Tavily infrastructure already built for the deep research pipeline.

### Current State

- `tools/research/jina_reader.py` — Jina Reader client, fetches clean markdown from any URL (free tier 20 RPM)
- `tools/research/search_client.py` — Tavily/Serper web search ($0.005/query)
- Both are ONLY wired into the deep research orchestrator (`tools/research/orchestrator.py`)
- The dashboard chat handler (`tools/api/chat_handler.py`) does NOT have access to browse or search tools
- Playwright is already installed (available as fallback for Jina failures)

### Phase B1: Tool Definitions and Handlers (1 day)

**Goal:** Define `browse_url` and `web_search` as Anthropic tool-use definitions with handler functions.

**Files to create:**
- `tools/api/browse_tools.py` (~180 lines) — Tool specs + handler dispatch

**Tool specifications:**

```python
BROWSE_TOOLS = [
    {
        "name": "browse_url",
        "description": "Fetch and read the content of a web page. Returns clean markdown text. Use this when you need to look up specific information from a museum website, news article, or any public URL.",
        "input_schema": {
            "type": "object",
            "properties": {
                "url": {
                    "type": "string",
                    "description": "The full URL to fetch (must start with http:// or https://)"
                }
            },
            "required": ["url"]
        }
    },
    {
        "name": "web_search",
        "description": "Search the web for information. Returns a list of results with titles, URLs, and snippets. Use this to find museum contact info, recent news, exhibition schedules, or technology adoption details.",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "The search query"
                },
                "max_results": {
                    "type": "integer",
                    "description": "Number of results (default 5, max 10)",
                    "default": 5
                }
            },
            "required": ["query"]
        }
    }
]
```

**Handler logic:**

```python
def handle_tool_call(tool_name: str, tool_input: dict) -> str:
    if tool_name == "browse_url":
        url = tool_input["url"]
        text = jina_reader.fetch_page(url, max_chars=20000)
        if not text or len(text) < 500:
            text = _playwright_fallback(url)  # Fallback for JS-heavy sites
        return text or "Failed to fetch page content."
    elif tool_name == "web_search":
        results, cost = search_client.search(
            tool_input["query"],
            max_results=tool_input.get("max_results", 5)
        )
        return _format_search_results(results)
```

**Verification:**
1. Unit test: `handle_tool_call("browse_url", {"url": "https://www.ssgreatbritain.org"})` returns markdown content
2. Unit test: `handle_tool_call("web_search", {"query": "SS Great Britain museum technology"})` returns formatted results

### Phase B2: Chat Handler Integration (1-2 days)

**Goal:** Wire browse tools into the streaming chat handler so Claude can use them mid-conversation.

**Files to modify:**
- `tools/api/chat_handler.py` — Add tool-use support to the streaming endpoint

**Integration pattern:**

The current `stream_chat()` endpoint uses `client.messages.stream()` which streams `text_delta` events. With tool use, Claude may emit `tool_use` blocks instead of (or alongside) text. The handler must:

1. Pass `tools=BROWSE_TOOLS` to `client.messages.stream()`
2. Detect `tool_use` content blocks in the response
3. When tool use detected:
   - Emit an SSE `status` event to the frontend: "Browsing {url}..." or "Searching for {query}..."
   - Execute the tool handler synchronously
   - Build a tool result message and continue the conversation
   - Resume streaming the next assistant response
4. Accumulate the final full response text across all turns

**SSE event additions:**

| Event | Payload | When |
|-------|---------|------|
| `tool_start` | `{"tool": "browse_url", "input": {"url": "..."}}` | Claude requests a tool |
| `tool_result` | `{"tool": "browse_url", "chars": 12500}` | Tool execution complete |

**Streaming loop pseudocode:**

```python
messages = list(history) + [{"role": "user", "content": augmented_input}]
full_response = ""

while True:
    response = client.messages.create(
        model=model, max_tokens=max_tokens, temperature=temperature,
        system=system_prompt, messages=messages,
        tools=BROWSE_TOOLS,
    )
    
    # Process response content blocks
    for block in response.content:
        if block.type == "text":
            full_response += block.text
            yield _sse("text_delta", text=block.text)
        elif block.type == "tool_use":
            yield _sse("tool_start", tool=block.name, input=block.input)
            result = handle_tool_call(block.name, block.input)
            yield _sse("tool_result", tool=block.name, chars=len(result))
            # Add assistant message + tool result to messages
            messages.append({"role": "assistant", "content": response.content})
            messages.append({"role": "user", "content": [
                {"type": "tool_result", "tool_use_id": block.id, "content": result}
            ]})
    
    if response.stop_reason == "end_turn":
        break
```

**Note:** Streaming with tool use requires switching from `client.messages.stream()` to `client.messages.create()` for the tool-use turns, then back to streaming for the final text response. This is a known Anthropic SDK pattern.

**Verification:**
1. Dashboard chat: "Look up the SS Great Britain website and tell me about their current audio guide setup" triggers `browse_url` tool call
2. Dashboard chat: "Search for museums in Austria that use audio guides" triggers `web_search`
3. Frontend shows "Browsing..." / "Searching..." status during tool execution
4. Tool results are NOT shown verbatim to the user (Claude synthesizes them)
5. Conversation history is saved cleanly (no tool artifacts in stored messages)

### Phase B3: CLI Chat Integration (0.5 days)

**Goal:** Same browse tools available in CLI chat (`python run.py chat`).

**Files to modify:**
- `tools/chat/session.py` — Add tool-use support to `run_chat()` loop, same pattern as chat_handler

**Verification:**
1. CLI chat with browse tools works end-to-end
2. Status messages appear in terminal during tool execution

### Scope Exclusions

- **Not in scope:** Auth-gated pages (museum intranets, LinkedIn profiles, paywalled articles)
- **Not in scope:** Screenshots or visual page analysis
- **Not in scope:** Form submission or page interaction
- **Not in scope:** Caching of browsed pages (each fetch is fresh)

### Safety Considerations

- Jina Reader free tier at 20 RPM is sufficient for ad-hoc chat browsing
- Tavily at $0.005/query adds negligible cost (typical session uses 0-3 searches)
- Playwright fallback only activates when Jina returns <500 chars (rate-limited to avoid resource drain)
- Tool results are truncated to 20,000 chars to prevent context blowup
- Cost tracking: search costs added to existing `cost_caps` tracking

### Estimated Effort

| Phase | Days | Depends On |
|-------|------|------------|
| B1: Tool definitions + handlers | 1 | Nothing |
| B2: Chat handler integration | 1-2 | B1 |
| B3: CLI chat integration | 0.5 | B1 |
| **Total** | **2.5-3.5** | |

---

## 4. Task 3: Calendar Access

### Goal

Touri reads Hermann's Google Calendar to know his availability, creates demo events for museum leads, and sets follow-up reminders — all from chat.

### Current State

- **HenryBot has a complete Google Calendar provider** at `~/HenryBot/tools/integrations/calendar/google_provider.py` that implements OAuth2, event CRUD, and free/busy queries
- HenryBot also has an Apple Calendar provider via a Swift binary, but Google Calendar is the better path because writes to Google auto-sync to Apple Calendar
- TouriBot has no calendar integration today
- The dashboard has a Calendar page placeholder that could display real events

### Setup Prerequisites (~20 minutes, one-time)

1. **Google Cloud Console:** Create project (or reuse existing) → Enable Calendar API → Create OAuth2 Desktop app credentials
2. **Download:** `client_secret.json` → store as referenced in `.env`
3. **First run:** Browser-based OAuth consent flow → tokens cached to `~/.touribot/google_token.json`
4. **Environment variables:**
   - `GOOGLE_CALENDAR_CLIENT_ID` — OAuth client ID
   - `GOOGLE_CALENDAR_CLIENT_SECRET` — OAuth client secret
   - `GOOGLE_CALENDAR_TOKEN_FILE` — Path to token cache (default: `~/.touribot/google_token.json`)

### Phase C1: Calendar Provider (1-2 days)

**Goal:** Copy and adapt HenryBot's Google Calendar provider for TouriBot.

**Files to create:**
- `tools/calendar/__init__.py`
- `tools/calendar/google_calendar.py` (~250 lines) — Adapted from HenryBot's `google_provider.py`

**Adaptation from HenryBot:**
- Remove dependency on `provider_base.py` (TouriBot doesn't need the multi-provider abstraction)
- Remove sync tokens and incremental sync (TouriBot doesn't need continuous sync)
- Change token path default from `~/.henrybot/` to `~/.touribot/`
- Keep: OAuth2 flow, `list_events()`, `create_event()`, `get_free_busy()`, `delete_event()`
- Add: `get_upcoming_demos()` — filter events by "Demo" or "AITourPilot" in title/description

**Core functions:**

```python
def authenticate() -> bool:
    """Run OAuth2 flow if no valid token exists. Returns True on success."""

def get_upcoming_events(days: int = 7) -> list[dict]:
    """List events in the next N days. Returns [{summary, start, end, location, description}]."""

def get_free_busy(date: str, duration_minutes: int = 60) -> list[dict]:
    """Find free slots on a given date. Returns [{start, end}] of available windows."""

def create_demo_event(museum_name: str, contact_name: str, 
                      start: str, duration_minutes: int = 45,
                      notes: str = "") -> dict:
    """Create a demo event. Returns the created event dict."""

def create_followup_reminder(museum_name: str, date: str, action: str) -> dict:
    """Create a follow-up reminder event. Returns the created event dict."""

def delete_event(event_id: str) -> bool:
    """Delete an event by ID."""
```

**Verification:**
1. `python -c "from tools.calendar.google_calendar import authenticate; authenticate()"` opens browser, completes OAuth
2. `get_upcoming_events(7)` returns this week's events
3. `create_demo_event("SS Great Britain", "Georgie Power", "2026-04-15T10:00:00")` creates event visible in Google + Apple Calendar
4. `get_free_busy("2026-04-15")` returns available time slots

### Phase C2: Chat Tool Integration (1 day)

**Goal:** Expose calendar functions as Anthropic tool-use definitions in chat.

**Files to create:**
- `tools/api/calendar_tools.py` (~120 lines) — Tool specs + handlers (same pattern as browse_tools.py)

**Files to modify:**
- `tools/api/chat_handler.py` — Add calendar tools to the tools list
- `tools/chat/session.py` — Add calendar tools to CLI chat

**Tool definitions:**

| Tool Name | Description | Parameters |
|-----------|-------------|------------|
| `get_calendar` | Get upcoming events for the next N days | `days` (int, default 7) |
| `check_availability` | Find free time slots on a specific date | `date` (ISO date), `duration_minutes` (default 60) |
| `schedule_demo` | Create a demo meeting event | `museum_name`, `contact_name`, `start` (ISO datetime), `duration_minutes`, `notes` |
| `set_followup` | Create a follow-up reminder | `museum_name`, `date` (ISO date), `action` (what to do) |

**Verification:**
1. Chat: "Am I free next Tuesday afternoon?" triggers `check_availability`
2. Chat: "Schedule a demo with Georgie Power at SS Great Britain for Tuesday at 2pm" triggers `schedule_demo`
3. Chat: "Remind me to follow up with Joanneum in 5 days" triggers `set_followup`
4. Events appear in Google Calendar within seconds

### Phase C3: Dashboard Calendar Page (1 day, optional)

**Goal:** Dashboard calendar page shows real Google Calendar events instead of placeholder data.

**Files to modify:**
- `tools/api/chat_handler.py` or new `tools/api/calendar_handler.py` — Add REST endpoints

**Endpoints:**

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/calendar/events` | List events for a date range |
| POST | `/api/calendar/events` | Create an event |
| DELETE | `/api/calendar/events/{id}` | Delete an event |

**Verification:**
1. Dashboard calendar page loads real events
2. Creating an event from dashboard appears in Google Calendar

### Safety Considerations

- OAuth2 tokens stored locally at `~/.touribot/google_token.json`, never committed
- Calendar scope is full read/write (`https://www.googleapis.com/auth/calendar`) — needed for event creation
- No auto-scheduling: Touri proposes times, Hermann confirms before creation
- Event creation always requires explicit user instruction (never triggered by memory extraction or background process)
- Token refresh handled automatically by google-auth library

### Estimated Effort

| Phase | Days | Depends On |
|-------|------|------------|
| C1: Calendar provider | 1-2 | Setup prerequisites |
| C2: Chat tool integration | 1 | C1 + B2 (tool-use pattern from browser) |
| C3: Dashboard calendar page | 1 | C1 (optional, can be deferred) |
| **Total** | **2-4** | |

---

## 5. Task 4: Email Access

### Goal

Touri reads inbound email from both accounts, creates drafts in Zoho, and (with guardrails) sends cold outreach via Instantly — the most sensitive capability expansion requiring defense-in-depth safety.

### Current State

- **hermann@aitourpilot.com** (Zoho Mail) — Primary business email. Manual send only. 3 emails/day self-imposed limit for .com domain reputation.
- **hermann@kudlich.co** (Instantly) — Cold outreach domain. Instantly manages sequences, warmup, deliverability. 20/day planned volume.
- TouriBot currently saves drafts to `output/emails/` as markdown files. Hermann copy-pastes them into Zoho.
- No read access to either inbox. Hermann manually reports responses.

### Critical Safety Context: The OpenClaw Incident

Research into AI email automation failures revealed a critical pattern: **safety instructions stored in conversational context (system prompts, memory) are LOST during context compaction.** When an LLM agent's context window fills up and older messages are dropped, behavioral constraints disappear. This is not theoretical — it has caused real-world unauthorized email sends.

**Implication for TouriBot:** All safety controls (rate limits, kill switches, approval requirements) must be enforced at the **system level** (config files read at execution time, database checks, code-level guards) — NEVER as conversational instructions that could be compacted away.

### Phase E1: Read .com via IMAP (1-2 days)

**Goal:** Touri reads inbound email from hermann@aitourpilot.com via Zoho IMAP.

**Files to create:**
- `tools/email/__init__.py`
- `tools/email/zoho_reader.py` (~200 lines) — IMAP client for Zoho Mail

**Environment variables:**
- `ZOHO_IMAP_HOST` — `imappro.zoho.com`
- `ZOHO_IMAP_USER` — `hermann@aitourpilot.com`
- `ZOHO_IMAP_PASSWORD` — App-specific password (not account password)

**Core functions:**

```python
def get_recent_emails(days: int = 7, folder: str = "INBOX") -> list[dict]:
    """Fetch recent emails. Returns [{from, to, subject, date, body_preview, message_id}]."""

def get_email(message_id: str) -> dict:
    """Fetch a single email with full body."""

def search_emails(query: str, days: int = 30) -> list[dict]:
    """Search emails by subject/from/body text."""
```

**IMAP implementation notes:**
- Use Python's built-in `imaplib` + `email` modules (no extra dependency)
- Connect with SSL on port 993
- Search with IMAP SINCE/SUBJECT/FROM criteria
- Parse MIME messages to extract text/plain or text/html body
- HTML body converted to text via `html2text` (already installed)
- Connection opened per request, not persistent (simple, safe)

**Verification:**
1. `get_recent_emails(7)` returns this week's emails from Zoho
2. `search_emails("SS Great Britain")` finds relevant correspondence
3. No email is ever modified, moved, or deleted via IMAP

### Phase E2: Read .co via Instantly Webhook (2-3 days)

**Goal:** Touri receives and stores inbound replies to cold outreach sent via Instantly.

**Files to create:**
- `tools/email/instantly_reader.py` (~150 lines) — Instantly API client + webhook handler

**Environment variables:**
- `INSTANTLY_API_KEY` — API key from Instantly dashboard
- `INSTANTLY_WEBHOOK_SECRET` — Webhook verification secret

**Design options (two approaches):**

**Option A: Instantly API polling (simpler, recommended for Phase E2)**
- Poll `GET /api/v1/email/list` every N minutes via a background task
- Store new replies in `data/leads.db` interactions table
- Pro: No webhook infrastructure needed. Con: Not real-time (polling delay).

**Option B: Instantly webhook (real-time, requires Phase E2b)**
- Register webhook URL at Instantly dashboard
- Requires the FastAPI server to be reachable (localhost + ngrok or deployed)
- Pro: Real-time. Con: Infrastructure dependency.

**Recommendation:** Start with Option A (polling). Add webhook in a later phase if real-time matters.

**Core functions:**

```python
def get_instantly_replies(campaign_id: str = None, since_days: int = 7) -> list[dict]:
    """Fetch replies from Instantly API. Returns [{from, subject, body, replied_at, campaign}]."""

def sync_replies_to_leads_db() -> int:
    """Sync new Instantly replies into interactions table. Returns count of new replies."""
```

**Verification:**
1. `get_instantly_replies()` returns recent cold outreach replies
2. `sync_replies_to_leads_db()` creates interaction records linked to the correct museum
3. Dashboard chat: "Any new replies?" shows Instantly replies

### Phase E3: Draft in Zoho via OAuth2 (1-2 days)

**Goal:** Touri creates email drafts directly in Hermann's Zoho Mail drafts folder via Zoho Mail API.

**Files to create:**
- `tools/email/zoho_writer.py` (~200 lines) — Zoho Mail API client for draft creation

**Environment variables:**
- `ZOHO_CLIENT_ID` — OAuth2 client ID from Zoho API Console
- `ZOHO_CLIENT_SECRET` — OAuth2 client secret
- `ZOHO_REFRESH_TOKEN` — Long-lived refresh token (generated once via consent flow)

**Critical safety decision:** The Zoho OAuth2 scope must be `ZohoMail.messages.CREATE` (drafts only). **NEVER request `ZohoMail.messages.ALL` or send scope.** This is a hard architectural constraint — not a conversational instruction.

**Core functions:**

```python
def create_draft(to: str, subject: str, body_html: str, 
                 cc: str = "", bcc: str = "") -> dict:
    """Create a draft in Zoho Mail. Returns {draft_id, message_id}."""
    # Draft appears in Hermann's Zoho drafts folder
    # Hermann reviews and clicks Send manually
```

**Integration with outreach pipeline:**
- When Touri drafts an email via `tools/outreach/drafter.py`, offer to also create a Zoho draft
- Draft is always saved to `output/emails/` AND created in Zoho
- The interaction is logged in leads.db with `is_draft=1`

**Verification:**
1. `create_draft("georgie@ssgreatbritain.org", "Following up...", "<p>Hi Georgie...</p>")` creates a draft visible in Zoho web UI
2. Draft appears in the Zoho Drafts folder, ready for Hermann to review and send
3. Hermann can edit the draft in Zoho before sending

### Phase E4: Automated Send via Instantly (3-5 days)

**Goal:** Touri sends cold outreach emails via Instantly API with full safety guardrails.

**This is the highest-risk phase.** It should only be enabled after Phases E1-E3 are stable and Hermann is comfortable with the approval workflow.

**Files to create:**
- `tools/email/email_queue.py` (~300 lines) — Queue-based approval workflow
- `tools/email/send_instantly.py` (~200 lines) — Instantly API send with all guardrails

**Schema additions to `data/leads.db`:**

```sql
CREATE TABLE IF NOT EXISTS email_queue (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    museum_id       INTEGER NOT NULL REFERENCES museums(id),
    contact_id      INTEGER REFERENCES contacts(id),
    account         TEXT NOT NULL,          -- 'com' or 'co'
    to_email        TEXT NOT NULL,
    subject         TEXT NOT NULL,
    body_html       TEXT NOT NULL,
    body_text       TEXT,
    sequence_step   INTEGER,
    status          TEXT DEFAULT 'pending', -- pending, approved, sent, rejected, failed
    approved_by     TEXT,                   -- 'hermann' or 'auto' (only for .co after safety checks)
    approved_at     TEXT,
    sent_at         TEXT,
    error_message   TEXT,
    content_hash    TEXT,                   -- SHA256 of normalized body for dedup
    created_at      TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS email_audit_log (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    queue_id        INTEGER REFERENCES email_queue(id),
    action          TEXT NOT NULL,          -- queued, approved, rejected, sent, failed, blocked_rate, blocked_dedup, blocked_killswitch
    actor           TEXT NOT NULL,          -- 'system', 'hermann', 'touri'
    details         TEXT,                   -- JSON with context
    created_at      TEXT DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_queue_status ON email_queue(status);
CREATE INDEX IF NOT EXISTS idx_queue_to_email ON email_queue(to_email);
CREATE INDEX IF NOT EXISTS idx_audit_queue ON email_audit_log(queue_id);
```

**Defense-in-depth safety system:**

| Layer | Control | Implementation | Bypass? |
|-------|---------|----------------|---------|
| 1. Kill switch | Global email send disable | `settings.yaml: email.send_enabled: false` — checked at execution time, NOT stored in LLM context | Only by editing config file |
| 2. Account isolation | .com never auto-sends | Code: `if account == 'com': raise` in `send_instantly.py` | Code change required |
| 3. Rate limiting | 3/day .com (hardcoded), 20/day .co (configurable) | `email_queue` table count query with date filter | Config change for .co |
| 4. Approval queue | All emails queued first | `email_queue` status must be `approved` before send | Code change required |
| 5. Recipient dedup | Same recipient within 7 days blocked | `email_queue` query: same `to_email` within window | Config change for window |
| 6. Content fingerprint | Same content within 30 days blocked | SHA256 hash of normalized body text | Config change for window |
| 7. Instantly platform dedup | Instantly's own dedup | Instantly API rejects duplicates natively | Platform-level |
| 8. Audit log | Every action logged | `email_audit_log` table, immutable append-only | Cannot bypass |
| 9. GDPR compliance | Legitimate interest + opt-out | Unsubscribe link in every cold email; LIA document on file | Legal requirement |

**CLI approval workflow:**

```bash
# View pending emails
python run.py email-queue

# Approve a specific email
python run.py email-approve 42

# Reject a specific email
python run.py email-reject 42 --reason "wrong tone"

# Approve all pending .co emails (batch)
python run.py email-approve-all --account co

# Emergency: disable all sending
python run.py email-killswitch on
python run.py email-killswitch off
```

**Kill switch implementation:**

```python
def _check_killswitch() -> bool:
    """Read kill switch from settings.yaml at execution time. NOT from memory/context."""
    settings = yaml.safe_load(open(SETTINGS_PATH))
    return settings.get("email", {}).get("send_enabled", False)

def send_email(queue_id: int) -> dict:
    if not _check_killswitch():
        _audit_log(queue_id, "blocked_killswitch", "system", "Kill switch is OFF")
        raise EmailBlockedError("Email sending is disabled via kill switch")
    # ... proceed with safety checks ...
```

**Verification:**
1. Touri queues an email: appears in `email_queue` with status `pending`
2. `python run.py email-queue` shows pending emails with preview
3. `python run.py email-approve 42` changes status to `approved`, triggers send
4. Sending respects rate limits: 4th .com email in a day is blocked
5. Duplicate to same recipient within 7 days is blocked
6. Kill switch OFF → all sends blocked with audit log entry
7. `email_audit_log` shows complete history of every action
8. .com account NEVER auto-sends (code-level block, not config)

### Safety Considerations (consolidated)

- **Principle of least privilege:** Zoho OAuth2 scope = CREATE only (no send). .com sends are always manual.
- **Defense in depth:** 9 independent safety layers. No single point of failure.
- **System-level controls:** Kill switch, rate limits, and approval requirements are enforced in code/config, never in LLM conversational context (the OpenClaw lesson).
- **Audit trail:** Every email action is logged with actor, timestamp, and context. Immutable append-only.
- **Gradual rollout:** E1 (read) → E2 (read more) → E3 (draft) → E4 (send with guardrails). Each phase independently useful.
- **GDPR:** Legitimate interest basis for B2B cold outreach. Every cold email includes unsubscribe link. Legitimate Interest Assessment (LIA) document needed before E4 goes live.

### Estimated Effort

| Phase | Days | Depends On |
|-------|------|------------|
| E1: Read .com (IMAP) | 1-2 | Nothing |
| E2: Read .co (Instantly API) | 2-3 | E1 (shared patterns) |
| E3: Draft in Zoho (OAuth2) | 1-2 | E1 (Zoho familiarity) |
| E4: Send via Instantly | 3-5 | E1, E2, E3 all stable |
| **Total** | **7-12** | |

---

## 6. Implementation Priority and Dependencies

### Dependency Graph

```
F1 (File Ingest) ──→ F2 (File API) ──→ F3 (Chat Integration)
                                    ↗
B1 (Browse Tools) ──→ B2 (Chat Handler Tool-Use) ──→ B3 (CLI Tools)
                              ↓
                     C1 (Calendar Provider) ──→ C2 (Calendar Chat Tools) ──→ C3 (Dashboard Calendar)
                     
E1 (Read .com) ──→ E3 (Draft .com) ──→ E4 (Send .co)
       ↓
E2 (Read .co) ──────────────────────↗
```

### Recommended Execution Order

**Week 1: Foundation + Quick Wins**

| Day | Phase | Rationale |
|-----|-------|-----------|
| 1 | F1: Config-driven ingest | Unblocks all file access; low risk |
| 2 | B1: Browse tool definitions | Unblocks browser integration; reuses existing code |
| 2 | E1: Read .com via IMAP | Can start in parallel; independent |
| 3 | B2: Chat handler tool-use | Critical enabler for calendar and all future tools |
| 4 | F2: File access API | Builds on F1; straightforward |
| 4 | F3: Chat integration | Quick, builds on F1 |

**Week 2: Calendar + Email Read**

| Day | Phase | Rationale |
|-----|-------|-----------|
| 5 | C1: Calendar provider | Copy from HenryBot; needs Google setup |
| 6 | C2: Calendar chat tools | Reuses B2 tool-use pattern |
| 6 | E2: Read .co via Instantly | Parallel with calendar work |
| 7 | B3: CLI chat tools | Quick; applies B2 pattern to CLI |
| 7 | E3: Draft in Zoho | Builds on E1 Zoho familiarity |

**Week 3: Email Send (when ready)**

| Day | Phase | Rationale |
|-----|-------|-----------|
| 8-10 | E4: Send via Instantly | Full safety system build |
| 10 | C3: Dashboard calendar | Optional; deferred if time-constrained |

### Parallelization Opportunities

These phase pairs can be built simultaneously by separate agents:

- F1 + E1 (file ingest + IMAP reader — completely independent codepaths)
- F2 + B1 (file API + browse tools — both add to `tools/api/`, but different files)
- C1 + E2 (calendar provider + Instantly reader — independent external APIs)
- B3 + F3 (CLI browse + file chat integration — both modify `session.py`, coordinate needed)

### Critical Path

The critical path runs through **B2 (Chat handler tool-use)** — this is the enabler for calendar tools, browse tools, and eventually email tools in chat. Everything before it is preparation; everything after it depends on the tool-use pattern being solid.

```
B1 → B2 → C2 → E4
```

---

## 7. Settings.yaml Changes Summary

All configuration additions across all four tasks, consolidated.

```yaml
# ── File System Access (Task 1) ──────────────────────────────────

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
      exclude_patterns:
        - "*.png"
        - "*.jpg"
        - "*.jpeg"
        - "*.gif"
        - "*.svg"
        - ".git/**"
    - path: ./docs_dev
      glob: "**/*.md"
      extractor: md
      access: readwrite
      label: "Development Docs"
  output_dir: knowledge/processed
  max_file_size_mb: 10

# ── Browser Access (Task 2) ───────────────────────────────────────

browse:
  jina:
    enabled: true
    max_chars: 20000         # Truncate fetched pages
    timeout_seconds: 30
  playwright_fallback:
    enabled: true            # Use when Jina returns <500 chars
    min_jina_chars: 500      # Threshold to trigger fallback
  search:
    provider: tavily          # tavily | serper (reuses deep_research config)
    max_results_default: 5
  tools_enabled: true         # Master toggle for browse tools in chat

# ── Calendar Access (Task 3) ──────────────────────────────────────

calendar:
  provider: google
  timezone: Europe/Vienna     # Hermann's timezone
  demo_duration_minutes: 45   # Default demo meeting length
  followup_reminder_time: "09:00"  # Default time for follow-up reminders
  enabled: true               # Master toggle for calendar tools in chat

# ── Email Access (Task 4) ─────────────────────────────────────────

email:
  send_enabled: false         # KILL SWITCH — checked at execution time
  accounts:
    com:
      provider: zoho_imap
      address: hermann@aitourpilot.com
      imap_host: imappro.zoho.com
      imap_port: 993
      rate_limit_per_day: 3   # HARDCODED in code; config is documentation only
      auto_send: false        # NEVER true for .com — enforced in code
      draft_enabled: true     # Can create drafts via Zoho API
    co:
      provider: instantly
      address: hermann@kudlich.co
      rate_limit_per_day: 20  # Configurable
      auto_send: false        # Set to true when E4 is stable and approved
  safety:
    recipient_dedup_days: 7   # Block same recipient within N days
    content_dedup_days: 30    # Block same content hash within N days
    require_approval: true    # All emails must be approved before sending
    auto_approve_co: false    # When true, .co emails auto-approve after safety checks
  audit:
    log_enabled: true         # Always true in production
    retention_days: 365       # Keep audit logs for 1 year
```

---

## 8. New Python Dependencies

Consolidated pip install list for all four tasks.

```
# Task 1: File System Access
pdfplumber>=0.10              # PDF text extraction for sales decks
python-docx>=1.1              # DOCX extraction for marketing documents

# Task 2: Browser Access
playwright>=1.40              # Already installed — fallback for Jina failures
# (jina_reader.py and search_client.py use only stdlib urllib — no extra deps)

# Task 3: Calendar Access
google-api-python-client>=2.0 # Google Calendar API v3
google-auth-oauthlib>=1.2     # OAuth2 browser consent flow
google-auth-httplib2>=0.2     # Auth transport
python-dateutil>=2.9          # Date parsing for calendar operations

# Task 4: Email Access
# imaplib + email are stdlib — no extra deps for E1
# html2text already installed — used for MIME parsing
# E3 (Zoho API) uses stdlib urllib — no extra deps
# E4 (Instantly API) uses stdlib urllib — no extra deps
```

**Total new dependencies: 5 packages** (pdfplumber, python-docx, google-api-python-client, google-auth-oauthlib, google-auth-httplib2). python-dateutil may already be installed as a transitive dependency.

**Updated requirements.txt:**

```
# Existing
anthropic>=0.40.0
PyYAML>=6.0
rich>=13.0
prompt_toolkit>=3.0
sentence-transformers>=5.0
sqlite-vec>=0.1.6
python-dotenv>=1.0
beautifulsoup4>=4.12
html2text>=2024.2

# Task 1: File System Access
pdfplumber>=0.10
python-docx>=1.1

# Task 3: Calendar Access
google-api-python-client>=2.0
google-auth-oauthlib>=1.2
google-auth-httplib2>=0.2
python-dateutil>=2.9
```

---

## 9. Credential Requirements

All API keys and tokens needed across all four tasks.

| Credential | Task | Source | Storage | Notes |
|-----------|------|--------|---------|-------|
| `JINA_API_KEY` | T2 | jina.ai dashboard | `.env` | Optional — free tier works without key at 20 RPM |
| `TAVILY_API_KEY` | T2 | tavily.com dashboard | `.env` | Already configured for deep research |
| `GOOGLE_CALENDAR_CLIENT_ID` | T3 | Google Cloud Console | `.env` | OAuth2 Desktop app |
| `GOOGLE_CALENDAR_CLIENT_SECRET` | T3 | Google Cloud Console | `.env` | OAuth2 Desktop app |
| `GOOGLE_CALENDAR_TOKEN_FILE` | T3 | Auto-generated | `~/.touribot/google_token.json` | Created on first OAuth flow |
| `ZOHO_IMAP_USER` | T4-E1 | Known | `.env` | hermann@aitourpilot.com |
| `ZOHO_IMAP_PASSWORD` | T4-E1 | Zoho Mail settings | `.env` | App-specific password, NOT account password |
| `ZOHO_CLIENT_ID` | T4-E3 | Zoho API Console | `.env` | OAuth2 for Mail API |
| `ZOHO_CLIENT_SECRET` | T4-E3 | Zoho API Console | `.env` | OAuth2 for Mail API |
| `ZOHO_REFRESH_TOKEN` | T4-E3 | OAuth2 consent flow | `.env` | Long-lived token |
| `INSTANTLY_API_KEY` | T4-E2/E4 | Instantly dashboard | `.env` | API key for read + send |
| `INSTANTLY_WEBHOOK_SECRET` | T4-E2b | Instantly dashboard | `.env` | Only if webhook approach chosen |

**Setup order by task:**
1. **T2 (Browser):** Already have TAVILY_API_KEY; JINA_API_KEY is optional
2. **T3 (Calendar):** ~20 min Google Cloud Console setup → OAuth browser flow
3. **T4-E1 (Read .com):** ~5 min Zoho app-specific password creation
4. **T4-E2 (Read .co):** ~5 min Instantly API key from dashboard
5. **T4-E3 (Draft .com):** ~30 min Zoho API Console setup → OAuth consent flow
6. **T1 (Files):** No credentials needed

---

## 10. Risk Register

| # | Risk | Impact | Likelihood | Mitigation |
|---|------|--------|------------|------------|
| R1 | **Zoho IMAP rate limiting or blocking** — Zoho may throttle frequent IMAP connections | Email read fails intermittently | Medium | Implement connection pooling with backoff; cache recent emails locally; poll no more than every 5 minutes |
| R2 | **Google OAuth token expiry during demo** — Refresh token expires (rare, 6-month default) | Calendar tools fail mid-conversation | Low | Token refresh is automatic; add graceful error handling that prompts re-auth |
| R3 | **Accidentally sending an email from .com** — Code bug bypasses safety layers | Reputation damage to .com domain | Low (9 safety layers) | .com auto-send is blocked at code level, not config; Zoho OAuth scope excludes send; code review required for any change to this |
| R4 | **Jina Reader returning garbage for JS-heavy museum sites** — Some museum sites are SPAs that Jina cannot render | Browse tool returns useless content | Medium | Playwright fallback already planned; threshold-based (Jina <500 chars triggers fallback) |
| R5 | **Context window overflow with tool results** — Browse/search results + email bodies + calendar data could blow token budget | API errors or truncated responses | Medium | All tool results are truncated to max_chars; total context budget enforced in `_assemble_context()` |
| R6 | **GDPR complaint from cold outreach recipient** — EU recipient invokes data rights | Legal exposure | Medium | Include unsubscribe link in every email; prepare LIA document; honor opt-out within 48 hours; document lawful basis |
| R7 | **Instantly deliverability drop after automation** — Aggressive sending damages .co domain reputation | Cold outreach ends up in spam | Medium | Start with 5/day, ramp to 20/day over 2 weeks; use Instantly's warmup; monitor open/reply rates |
| R8 | **Tool-use loop — Claude calls tools endlessly** — LLM decides to keep browsing/searching in a loop | High API costs, timeout | Low | Max 5 tool calls per conversation turn (hardcoded limit in chat handler); cost tracking alerts |
| R9 | **Settings.yaml config drift** — Multiple expansion phases modifying same config file creates merge conflicts | Broken config | Medium | Each phase adds its own top-level key (knowledge, browse, calendar, email); no overlap |
| R10 | **PDF extraction quality** — Marketing PDFs may be image-based scans, not text | Empty extraction for some sales decks | Low | Accept empty output for image PDFs; flag them in ingest output; Hermann can convert to text manually |
| R11 | **Playwright resource consumption** — Headless browser instances consume memory | Server instability | Low | Single browser instance reused; explicit cleanup after each page; timeout at 30 seconds |
| R12 | **Instantly API changes or deprecation** — Third-party API is outside our control | Cold outreach automation breaks | Low | Instantly is the market leader; API is stable; abstract behind interface for easy swap |

### Risk Severity Matrix

```
              Low Impact    Medium Impact    High Impact
High Likely   —             R7               —
Med Likely    R10           R1, R5, R6, R9   —
Low Likely    R11, R12      R2, R4, R8       R3
```

**Top 3 risks requiring active monitoring:**
1. **R3 (Accidental .com send)** — Highest consequence. Mitigated by 9 safety layers. Verify with every E4 code change.
2. **R7 (Deliverability drop)** — Directly impacts outreach success. Monitor Instantly dashboard daily during ramp-up.
3. **R5 (Context overflow)** — Most likely to cause runtime errors. Budget enforcement already exists; extend to tool results.

---

## Appendix A: Files Created/Modified by Phase

| Phase | New Files | Modified Files |
|-------|-----------|----------------|
| F1 | `tools/knowledge/extractors.py` | `tools/knowledge/ingest.py`, `args/settings.yaml` |
| F2 | `tools/api/file_handler.py` | `tools/api/server.py` |
| F3 | — | `tools/chat/session.py` |
| B1 | `tools/api/browse_tools.py` | — |
| B2 | — | `tools/api/chat_handler.py` |
| B3 | — | `tools/chat/session.py` |
| C1 | `tools/calendar/__init__.py`, `tools/calendar/google_calendar.py` | — |
| C2 | `tools/api/calendar_tools.py` | `tools/api/chat_handler.py`, `tools/chat/session.py` |
| C3 | `tools/api/calendar_handler.py` | `tools/api/server.py` |
| E1 | `tools/email/__init__.py`, `tools/email/zoho_reader.py` | — |
| E2 | `tools/email/instantly_reader.py` | — |
| E3 | `tools/email/zoho_writer.py` | `tools/outreach/drafter.py` |
| E4 | `tools/email/email_queue.py`, `tools/email/send_instantly.py` | `tools/leads/lead_db.py` (schema), `run.py`, `args/settings.yaml` |

**Total new files:** 13
**Total modified files:** 9 unique files (some modified in multiple phases)

---

## Appendix B: Schema Additions Summary

**`data/leads.db` additions (Phase E4):**
- `email_queue` table — approval workflow for outgoing emails
- `email_audit_log` table — immutable audit trail

**`data/conversations.db` additions:** None

**`data/memory.db` additions:** None

---

*This plan is the complete blueprint for TouriBot's next major evolution. Each phase is independently verifiable and independently valuable. The four capability areas can be built in parallel where dependencies allow. The critical path runs through the chat handler tool-use pattern (Phase B2), which enables all subsequent tool integrations.*

*Created: 2026-04-09*
