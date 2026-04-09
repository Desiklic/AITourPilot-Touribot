# TouriBot Dashboard — Autonomous Build Plan

**Date:** 2026-04-07
**Project:** /Users/hermannkudlich/Documents/ClaudeProjects/AITourPilot-Touribot
**Depends on:** ARCHITECTURE.md, Phase 1-5 CLI backend complete
**FelixBot source:** ~/FelixBot/dashboard/ (Next.js 16, React 19, shadcn/ui, Tailwind v4)
**HenryBot source:** ~/HenryBot/henry-dashboard/

---

## Execution Protocol

**THIS PLAN IS DESIGNED FOR FULLY AUTONOMOUS EXECUTION.** The executing agent should complete ALL 7 phases in a single session without human intervention, stopping only if a blocking issue requires human input (e.g., missing API keys, permissions errors).

**Each phase follows a strict 3-step cycle:**

1. **RESEARCH** — Understand what needs to be done by examining source code, dependencies, and patterns
2. **IMPLEMENT** — Build the code with a multi-agent team (implementers + architect overseer + QA)
3. **VALIDATE** — Verify everything works with a separate validation team. Fix any issues found. Only proceed to the next phase when validation PASSES.

**If validation FAILS:** Fix the issues, re-validate. Loop until PASS. Never skip to the next phase with known failures.

**Commit after each validated phase.** Use descriptive commit messages.

---

## Context for the Executing Agent

TouriBot is a museum outreach assistant with a working CLI backend. This plan adds a web dashboard — a visual campaign command center.

### What Exists (Backend — DO NOT MODIFY)

| Data | Location | Access |
|------|----------|--------|
| 55 museums, 76 contacts, 14 interactions | `data/leads.db` | `tools/leads/lead_db.py` |
| 11 memories, 11 embeddings | `data/memory.db` | `tools/memory/memory_db.py` |
| Email drafts | `output/emails/*.md` | Filesystem |
| Chat session | `tools/chat/session.py` | Anthropic SDK (no HTTP server) |

### What We're Building (Dashboard)

| View | Priority | Source |
|------|----------|--------|
| Pipeline CRM (kanban + table, 11 stages) | P0 | New — reads `leads.db` |
| Chat (threaded, streaming) | P0 | FelixBot copy + FastAPI backend |
| Statistics (funnel, email stats, timeline) | P1 | New — reads `leads.db` |
| Calendar (follow-ups, demos) | P1 | FullCalendar + `leads.db` |
| Task Board (follow-ups, actions) | P1 | FelixBot kanban copy |
| Memory browser | P2 | FelixBot copy |
| Settings (theme, models) | P2 | FelixBot copy |

### Tech Stack

Next.js 16 (App Router), React 19, shadcn/ui, Tailwind CSS v4, Recharts v3, @hello-pangea/dnd v18, FullCalendar v6, next-themes v0.4, better-sqlite3 v12, TanStack Query v5. Chat backend: FastAPI + sse-starlette.

### Directory Structure

```
touri-dashboard/
├── package.json
├── next.config.ts
├── tailwind.config.ts
├── tsconfig.json
├── .env.local                       <-- TOURIBOT_HOME path
├── src/
│   ├── app/
│   │   ├── layout.tsx               <-- ThemeProvider + sidebar shell
│   │   ├── page.tsx                 <-- Redirect to /pipeline
│   │   ├── pipeline/page.tsx        <-- CRM pipeline (kanban + table)
│   │   ├── pipeline/[id]/page.tsx   <-- Museum detail
│   │   ├── chat/page.tsx            <-- Threaded chat
│   │   ├── stats/page.tsx           <-- Campaign statistics
│   │   ├── calendar/page.tsx        <-- Follow-ups calendar
│   │   ├── tasks/page.tsx           <-- Task board
│   │   ├── memory/page.tsx          <-- Memory browser
│   │   ├── settings/page.tsx        <-- Theme, models
│   │   └── api/                     <-- API routes (leads, stats, chat, memory, etc.)
│   ├── components/
│   │   ├── ui/                      <-- FROM FELIXBOT: shadcn primitives
│   │   ├── layout/                  <-- FROM FELIXBOT: sidebar, shell
│   │   ├── chat/                    <-- FROM FELIXBOT: chat components
│   │   ├── pipeline/                <-- NEW: CRM components
│   │   ├── stats/                   <-- NEW: statistics components
│   │   ├── board/                   <-- FROM FELIXBOT: kanban
│   │   ├── calendar/                <-- NEW: FullCalendar wrapper
│   │   └── settings/                <-- FROM FELIXBOT: appearance
│   └── lib/
│       ├── db/                      <-- SQLite access (better-sqlite3)
│       ├── types.ts                 <-- TypeScript types matching SQLite schema
│       ├── constants.ts             <-- Stage names, colors, icons
│       └── subprocess.ts            <-- FROM FELIXBOT: Python subprocess spawner

tools/api/                           <-- NEW: Python FastAPI chat backend
├── __init__.py
├── server.py                        <-- FastAPI app (port 8765)
└── chat_handler.py                  <-- Wraps session.py for streaming
```

### Reuse Rules

- **FROM FELIXBOT (verbatim)** — copy with zero changes
- **FROM FELIXBOT (adapted)** — copy then modify as specified
- **NEW** — build from scratch following FelixBot's shadcn/ui patterns

### Files NOT to Touch

- `tools/memory/*.py` — never modify the memory system
- `tools/chat/session.py` — the dashboard handler wraps it, doesn't modify it
- `tools/leads/lead_db.py` — read by the dashboard, not modified
- `tools/outreach/*.py` — invoked via FastAPI, not modified
- `soul.md`, `memory/USER.md` — identity files, never auto-modified
- `run.py` — CLI continues to work independently

### Risk Areas

**#1: SQLite concurrent access.** JS (better-sqlite3) and Python (sqlite3) both access leads.db and memory.db. Mitigation: enable WAL mode on both DBs. JS routes are read-only except PATCH /api/leads/[id].

**#2: Chat streaming reliability.** SSE through Next.js → FastAPI → Anthropic. Mitigation: copy FelixBot's proven SSE event format. Add error/reconnection handling.

### Rollback

The entire dashboard is in `touri-dashboard/`. Delete it to rollback. CLI backend is unaffected.

---

## PHASE D1: Foundation + Layout (~4 hours)

**Goal:** Dashboard shell with navigation, theme toggle, and placeholder pages that loads at localhost:3000.

### Step 1 — RESEARCH

Create an agent team of 2 teammates:

1. **Deep Investigator** — Read the FelixBot dashboard codebase at ~/FelixBot/dashboard/:
   - Read `package.json` completely — list all dependencies and their versions
   - Read `src/app/layout.tsx` — how is ThemeProvider + sidebar shell structured?
   - Read `src/components/layout/sidebar.tsx` and `layout-shell.tsx` — navigation structure, icon system, collapsible behavior
   - Read `src/components/settings/appearance-section.tsx` — theme toggle implementation
   - Read `tailwind.config.ts` and `next.config.ts` — configuration
   - List ALL files in `src/components/ui/` — these are shadcn primitives to copy
   - Document: which files to copy verbatim, which need adaptation, what to change in each

2. **Architect Analyst** — Read the TouriBot ARCHITECTURE.md and the build plan context above:
   - Define the TypeScript types needed (Museum, Contact, Interaction, PipelineStats) matching the SQLite schema in ARCHITECTURE.md Section C1
   - Define the stage constants (names, colors, icons for stages 0-10)
   - Plan the navigation items: Pipeline, Chat, Stats, Calendar, Tasks, Memory, Settings
   - Identify any FelixBot dependencies that TouriBot doesn't need (e.g., js-yaml, CalendarWrapper)
   - Ensure .env.local points to the correct TOURIBOT_HOME path

DELIVERABLE: Consolidated list of files to copy, files to create, and exact modifications needed.

### Step 2 — IMPLEMENT

Create an agent team:

1. **Implementer A** — Owns: project initialization + copied components
   - Create `touri-dashboard/` directory
   - Create `package.json` from FelixBot template (remove unneeded deps, add any missing ones)
   - Copy `next.config.ts`, `tailwind.config.ts`, `tsconfig.json` from FelixBot, adapt as needed
   - Copy ALL `src/components/ui/` from FelixBot verbatim
   - Copy and adapt `layout-shell.tsx`, `sidebar.tsx` — rename FelixBot→TouriBot, update nav items
   - Copy `theme-provider.tsx`, `appearance-section.tsx`
   - Create `.env.local` with TOURIBOT_HOME path
   - Create `.gitignore` (node_modules, .next, .env.local)
   - Run `npm install`

2. **Implementer B** — Owns: types, constants, placeholder pages, layout
   - Create `src/lib/types.ts` — TypeScript types matching SQLite schema
   - Create `src/lib/constants.ts` — stage names, colors (gold→green gradient), icons
   - Create `src/app/layout.tsx` — ThemeProvider + sidebar shell
   - Create `src/app/page.tsx` — redirect to /pipeline
   - Create 7 placeholder pages (pipeline, chat, stats, calendar, tasks, memory, settings) — each showing a header and "Coming soon" message
   - Create `src/app/settings/page.tsx` — copy FelixBot's appearance section as the first working settings page

3. **Architect Overseer** — Does NOT write code. Reviews:
   - No FelixBot references remaining (grep for "felix", "Felix", "FELIX")
   - package.json has no unnecessary dependencies
   - TypeScript types exactly match the ARCHITECTURE.md C1 schema
   - Navigation items are correct (7 items)
   - Theme toggle works in both dark and light mode
   - .env.local has correct path

DELIVERABLE: Working dashboard shell. `npm run dev` loads at localhost:3000.

### Step 3 — VALIDATE

Create an agent team of 2:

1. **Architect Validator** — Full review:
   - Read every created/copied file end-to-end
   - Verify no FelixBot references remain (grep entire touri-dashboard/ for "felix")
   - Verify TypeScript types match ARCHITECTURE.md C1 schema field-for-field
   - Verify all 7 navigation items are present and route correctly
   - Verify layout.tsx properly wraps with ThemeProvider
   - Check: does `npm run build` succeed without errors?

2. **Regression Checker**:
   - Verify NO files outside touri-dashboard/ were modified
   - Verify `python run.py status` still works (CLI backend unaffected)
   - Verify `python run.py pipeline` still works
   - Check that data/leads.db and data/memory.db are not modified

If ANY check fails → fix and re-validate. Only proceed to Phase D2 when all checks PASS.

**Commit:** `git add touri-dashboard/ && git commit -m "Phase D1: Dashboard foundation + layout"`

---

## PHASE D2: Pipeline CRM View (~8 hours)

**Goal:** Museums displayed as a kanban board with 11 stages, switchable to table view, with a museum detail panel showing full interaction history.

### Step 1 — RESEARCH

Create an agent team of 2:

1. **Deep Investigator** — Read FelixBot's kanban board implementation:
   - Read ALL files in ~/FelixBot/dashboard/src/components/board/ (6 files, ~1464 lines)
   - Read ~/FelixBot/dashboard/src/lib/db/tasks-db.ts — how does it access SQLite?
   - Read ~/FelixBot/dashboard/src/app/api/tasks/route.ts — API pattern
   - Document: the DnD pattern (@hello-pangea/dnd), sort order algorithm, task card structure
   - Read the TouriBot `data/leads.db` schema (open with sqlite3, run .schema) — confirm all fields

2. **Architect Analyst** — Design the pipeline components:
   - How to map the 11 pipeline stages (0-10) to kanban columns
   - Table view design: which columns, sort order, filters
   - Museum detail panel: what data to show (contacts, interactions, research, notes)
   - API route design: GET /api/leads, GET /api/leads/[id], PATCH /api/leads/[id]
   - better-sqlite3 wrapper design for leads.db (WAL mode, connection pooling)

DELIVERABLE: Component specifications and API contracts.

### Step 2 — IMPLEMENT

Create an agent team:

1. **Implementer A** — Owns: database layer + API routes
   - Create `src/lib/db/leads-db.ts` — better-sqlite3 wrapper for leads.db with WAL mode
   - Create `src/app/api/leads/route.ts` — GET (list with ?stage= filter), POST (create)
   - Create `src/app/api/leads/[id]/route.ts` — GET (detail + contacts + interactions), PATCH (update stage/score/notes)
   - Create `src/app/api/leads/[id]/history/route.ts` — GET (full interaction timeline)

2. **Implementer B** — Owns: pipeline page + components
   - Create `src/components/pipeline/stage-badge.tsx` — colored pill
   - Create `src/components/pipeline/museum-card.tsx` — card for kanban (name, contact, country, stale indicator)
   - Create `src/components/pipeline/pipeline-kanban.tsx` — 11 columns with horizontal scroll, DnD between stages
   - Create `src/components/pipeline/pipeline-table.tsx` — DataTable with TanStack Table (sortable, filterable)
   - Create `src/components/pipeline/museum-detail.tsx` — slide-out panel with full detail
   - Create `src/app/pipeline/page.tsx` — toggle between kanban and table, data fetching with TanStack Query
   - Create `src/app/pipeline/[id]/page.tsx` — full museum detail page

3. **Architect Overseer** — Reviews:
   - API routes return correct data matching TypeScript types
   - better-sqlite3 opens leads.db in WAL mode
   - No writes from kanban DnD bypass the PATCH API route
   - Museum detail shows ALL interaction types (email_sent, meeting_noshow, prep, etc.)
   - Empty states handled (what if a stage has 0 museums?)
   - Dark/light theme works on all pipeline components

DELIVERABLE: Working pipeline page with kanban + table + detail panel.

### Step 3 — VALIDATE

Create an agent team of 2:

1. **Architect Validator**:
   - Open /pipeline — verify all 55 museums display
   - Verify kanban shows correct count per stage (52 at Stage 0, 1 at Stage 2, 1 at Stage 3, 1 at Stage 6)
   - Click BTU Cottbus — verify 5 interactions show (booking, research, prep, no-show, follow-up)
   - Toggle to table view — verify sorting and filtering work
   - Verify PATCH /api/leads/[id] correctly updates stage in leads.db
   - Test with `npm run build` — no TypeScript errors

2. **Regression Checker**:
   - Verify `python run.py pipeline` still shows the same data
   - Verify Phase D1 pages still work (settings, theme toggle)
   - Verify no Python files were modified

If ANY check fails → fix and re-validate.

**Commit:** `git commit -m "Phase D2: Pipeline CRM view with kanban + table"`

---

## PHASE D3: Chat Interface (~6 hours)

**Goal:** Chat with Touri in the browser with streaming responses and conversation history.

### Step 1 — RESEARCH

Create an agent team of 3:

1. **Deep Investigator** — Read FelixBot's chat implementation:
   - Read ALL files in ~/FelixBot/dashboard/src/components/chat/ (6 files, ~1287 lines)
   - Read ~/FelixBot/dashboard/src/app/chat/page.tsx (538 lines) — full page structure
   - Read ~/FelixBot/dashboard/src/app/api/chat/stream/route.ts — SSE streaming pattern
   - Read ~/FelixBot/dashboard/src/lib/subprocess.ts — Python subprocess spawning
   - Read ~/FelixBot/dashboard/src/lib/db/conversations-db.ts — conversation storage

2. **Architect Analyst** — Design the chat backend:
   - Read TouriBot's `tools/chat/session.py` (442 lines) — understand the chat loop internals
   - Design `tools/api/server.py` (FastAPI) — what endpoints, how to stream
   - Design `tools/api/chat_handler.py` — how to wrap session.py for HTTP streaming
   - Define the SSE event format (match FelixBot: meta, text_delta, done, error)
   - Plan conversation storage schema for the dashboard

3. **External Researcher** — Research FastAPI SSE streaming:
   - How to use sse-starlette with FastAPI for streaming AI responses
   - How to connect Next.js frontend to a FastAPI SSE endpoint
   - CORS configuration for local development (Next.js on 3000, FastAPI on 8765)

DELIVERABLE: Chat backend design + component adaptation plan.

### Step 2 — IMPLEMENT

Create an agent team:

1. **Implementer A** — Owns: Python FastAPI backend (tools/api/)
   - Create `tools/api/__init__.py`
   - Create `tools/api/server.py` — FastAPI app with CORS, SSE chat endpoint
   - Create `tools/api/chat_handler.py` — wraps session.py: loads context, calls Anthropic, streams tokens as SSE

2. **Implementer B** — Owns: Frontend chat components + API routes
   - Copy chat components from FelixBot: chat-thread.tsx, chat-input.tsx, chat-sidebar.tsx, message-bubble.tsx, markdown-content.tsx
   - Adapt chat-sidebar.tsx — rename FelixBot references
   - Create `src/app/chat/page.tsx` — connect to FastAPI SSE endpoint
   - Create `src/lib/db/conversations-db.ts` — conversation storage
   - Create `src/app/api/chat/route.ts` — GET session list
   - Create `src/app/api/chat/stream/route.ts` — POST proxy to FastAPI SSE

3. **Architect Overseer** — Reviews:
   - FastAPI server starts without errors, streams tokens correctly
   - No modification to tools/chat/session.py (handler imports its internals)
   - FelixBot chat component copies have no FelixBot references
   - SSE event format matches between Python backend and frontend consumer
   - Conversation history persists across page reloads
   - Memory search context is injected into chat responses (Touri knows about BTU Cottbus)

DELIVERABLE: Working chat interface with streaming.

### Step 3 — VALIDATE

Create an agent team of 2:

1. **Architect Validator**:
   - Start FastAPI server (`python -m tools.api.server`)
   - Open /chat — type "What do you know about BTU Cottbus?" — verify streaming response with correct context
   - Start new session, return to previous — verify history preserved
   - Verify memory search is active (response mentions Dr. Owesle, no-show, etc.)
   - Test `npm run build` — no errors
   - Verify tools/chat/session.py was NOT modified

2. **Regression Checker**:
   - Verify /pipeline still works
   - Verify `python run.py chat` CLI still works independently
   - Verify `python run.py recall "BTU"` still works

If ANY check fails → fix and re-validate.

**Commit:** `git commit -m "Phase D3: Chat interface with streaming"`

---

## PHASE D4: Statistics Dashboard (~5 hours)

**Goal:** Campaign metrics at a glance — pipeline funnel, email stats, activity timeline.

### Step 1 — RESEARCH

Create an agent team of 2:

1. **Deep Investigator** — Read FelixBot's costs page for chart patterns:
   - Read ~/FelixBot/dashboard/src/app/costs/page.tsx — Recharts implementation
   - Read ~/FelixBot/dashboard/src/lib/db/costs-db.ts — aggregation patterns
   - Document: which Recharts components are used, how data is formatted for charts

2. **Architect Analyst** — Design the statistics components:
   - Define API response shape for GET /api/stats
   - Design pipeline funnel visualization (horizontal bar chart by stage)
   - Design email stats cards (sent, replied, pending, conversion rate)
   - Design activity timeline (last 14 days of interactions)
   - Design campaign progress metrics (days active, contacts reached, velocity)

DELIVERABLE: Component specifications with mock data shapes.

### Step 2 — IMPLEMENT

Create an agent team:

1. **Implementer A** — Owns: API route + data layer
   - Create `src/app/api/stats/route.ts` — aggregates from leads.db

2. **Implementer B** — Owns: stats page + components
   - Create `src/components/stats/pipeline-funnel.tsx` — Recharts horizontal BarChart
   - Create `src/components/stats/email-stats.tsx` — card grid with key metrics
   - Create `src/components/stats/activity-timeline.tsx` — vertical timeline
   - Create `src/components/stats/campaign-progress.tsx` — overall metrics
   - Create `src/app/stats/page.tsx` — wire all components

3. **Architect Overseer** — Reviews:
   - Charts render correctly with real data (not just mock data)
   - Numbers match what `python run.py status` shows
   - Empty states handled (what if 0 emails sent?)
   - Dark/light theme works on all chart components
   - Recharts responsive container used for all charts

DELIVERABLE: Working statistics page.

### Step 3 — VALIDATE

Create an agent team of 2:

1. **Architect Validator**:
   - Open /stats — verify pipeline funnel shows correct stage counts
   - Verify email stats match interaction counts from leads.db
   - Verify activity timeline shows BTU Cottbus events
   - Test `npm run build` — no errors

2. **Regression Checker**:
   - Verify /pipeline and /chat still work
   - Verify no Python files modified

If ANY check fails → fix and re-validate.

**Commit:** `git commit -m "Phase D4: Statistics dashboard"`

---

## PHASE D5: Calendar + Task Board (~5 hours)

**Goal:** Visual timeline of upcoming actions and a task board for follow-ups.

### Step 1 — RESEARCH

Create an agent team of 2:

1. **Deep Investigator** — Read FelixBot's calendar and kanban:
   - Read ~/FelixBot/dashboard/src/app/calendar/page.tsx — calendar structure
   - Read ~/FelixBot/dashboard/src/components/board/ — kanban board for task reuse
   - Research FullCalendar v6 React integration (web search for docs/examples)

2. **Architect Analyst** — Design calendar and task board:
   - API: GET /api/calendar (follow-ups as events), GET /api/followups (due today/week/overdue)
   - Calendar event types: follow-up (orange), demo (blue), overdue (red), completed (green)
   - Task board columns: Overdue, Due Today, This Week, Next Week

DELIVERABLE: Component specifications.

### Step 2 — IMPLEMENT

Create an agent team:

1. **Implementer A** — Owns: API routes + calendar
   - Create `src/app/api/calendar/route.ts`
   - Create `src/app/api/followups/route.ts`
   - Create `src/components/calendar/campaign-calendar.tsx` — FullCalendar wrapper
   - Create `src/app/calendar/page.tsx`

2. **Implementer B** — Owns: task board
   - Copy and adapt FelixBot kanban board — columns: Overdue, Due Today, This Week, Next Week
   - Create `src/app/tasks/page.tsx`

3. **Architect Overseer** — Reviews:
   - Calendar events color-coded correctly
   - BTU Cottbus follow-up (April 14) appears on calendar
   - Task board shows correct column for each follow-up based on today's date
   - FullCalendar responsive and theme-aware

DELIVERABLE: Working calendar and task board.

### Step 3 — VALIDATE

Validate calendar shows BTU Cottbus follow-up, task board shows it in the correct column. All previous pages still work.

**Commit:** `git commit -m "Phase D5: Calendar + task board"`

---

## PHASE D6: Memory + Settings (~3 hours)

**Goal:** Memory browser and settings, largely copied from FelixBot.

### Step 1 — RESEARCH

Read FelixBot's memory page (~/FelixBot/dashboard/src/app/memory/page.tsx) and memory API routes. Document what to copy and what to change (DB path to TouriBot's data/memory.db).

### Step 2 — IMPLEMENT

1. Copy FelixBot memory page — adapt DB path
2. Copy memory API routes — adapt paths
3. Update settings page — add TouriBot-specific settings
4. Create `src/lib/db/memory-db.ts` from FelixBot — change BOT_HOME

### Step 3 — VALIDATE

Open /memory — see 11 memories. Search "BTU" — returns results. Dark/light theme works. All previous pages work.

**Commit:** `git commit -m "Phase D6: Memory browser + settings"`

---

## PHASE D7: Polish + Integration (~4 hours)

**Goal:** Everything works together seamlessly. Cross-page navigation, loading states, responsive design.

### Step 1 — RESEARCH

Review all pages for integration opportunities: pipeline detail → "Draft Email" → chat. Stats → click stage → pipeline filtered. Calendar/tasks → click item → museum detail.

### Step 2 — IMPLEMENT

1. Pipeline detail: "Draft Email" button → navigates to /chat with pre-filled prompt
2. Stats: click stage bar → /pipeline?stage=N
3. Calendar/tasks: click event → museum detail panel
4. Breadcrumb navigation on all pages
5. Loading states (Suspense boundaries) and error boundaries
6. Mobile responsive (sidebar collapse at 768px, horizontal scroll for kanban/table)
7. Create startup script that launches both `npm run dev` and `python -m tools.api.server`

### Step 3 — VALIDATE

**Full end-to-end flow test:**
1. Open /stats → see pipeline funnel
2. Click Stage 0 bar → /pipeline filtered to Stage 0
3. Click a museum → detail panel opens
4. Click "Draft Email" → /chat opens with pre-filled prompt
5. Touri streams a draft email
6. Navigate to /tasks → see follow-ups
7. Navigate to /calendar → see upcoming events
8. Navigate to /memory → search works
9. Toggle dark mode → all pages render correctly
10. Run `npm run build` → zero errors

Verify ALL Python CLI commands still work independently.

**Commit:** `git commit -m "Phase D7: Polish + cross-page integration"`

---

## Final Verification

After all 7 phases are complete:

1. `npm run build` in touri-dashboard/ — zero errors
2. Full flow test (10 steps above)
3. `python run.py status` — CLI works independently
4. `python run.py pipeline` — same data as dashboard
5. `python run.py recall "BTU"` — memory unaffected
6. No Python backend files modified (except new tools/api/)
7. All commits clean and descriptive

---

*Total estimated effort: ~35 hours across 7 phases. Each phase is independently testable and committable.*
