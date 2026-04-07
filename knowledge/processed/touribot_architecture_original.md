# TouriBot Marketing Platform Architecture (Original Vision)

*Source: 20260317-touribot-marketing-platform-architecture.html*
*Priority: P2*

## Vision

TouriBot is a **purpose-built AI operations assistant** for executing the [AITourPilot Precision Partner Acquisition Engine](../strategy/20260314-precision-partner-acquisition-engine.html). It combines the best of three existing systems -- HenryBot's memory and task management, ChatProgElectron's polished chat interface, and the Content Factory's pipeline architecture -- into a single platform focused on one mission: **winning museum partnerships**.

This is not a general-purpose assistant. It is a vertical AI sales agent for cultural institutions, with persistent memory, a visual pipeline, and deep domain knowledge about museums, audioguides, and the competitive landscape.

> **Related documents:** TouriBot operationalizes the [Precision Partner Acquisition Engine](../strategy/20260314-precision-partner-acquisition-engine.html) (strategy: what to send, who to target) and runs on the [Outreach Infrastructure Blueprint](../technical/20260318-outreach-infrastructure-blueprint.html) (infrastructure: .co domain, email authentication, warm-up protocol). All three documents form a layered system: Strategy → Platform → Infrastructure.

### Why Build This (Instead of Using ChatGPT / Claude Web)

| Problem with general-purpose AI chat | TouriBot solves it |
|------|------|
| Context window runs out mid-campaign | Persistent memory (3-tier system from HenryBot) |
| No state tracking across sessions | Museum pipeline tracks every contact's stage |
| No task management | Kanban board with mutual task assignment |
| No cost visibility | Real-time cost monitor per model, per task |
| Can't see what happened yesterday | Calendar + morning briefing with pipeline status |
| Can't research museums autonomously | Agent swarm dispatches research in parallel |
| Generic personality, no domain knowledge | soul.md with deep museum industry context |
| No accountability | Notes system, activity logs, task history |

### What It Inherits

| From HenryBot | From ChatProgElectron | From Content Factory |
|---|---|---|
| 3-tier memory (USER.md / MEMORY.md / memory.db) | React chat UI with threads | Pipeline stage progression (conveyor belt) |
| Multi-agent framework (Agent SDK + Gateway) | Voice input (push-to-talk STT) | BullMQ job queue for async work |
| Kanban task board | Image/file upload & display | Real-time progress tracker (10-stage visual) |
| Cost monitor + spending guards | Auto-resizing composer | Heartbeat / orphan detection |
| Morning briefing system | Markdown rendering + code blocks | SSE for live updates |
| Model selector (per-task routing) | Drag-and-drop | Dashboard with status cards |
| Notes system | Dark/light message bubbles | Stage-level logging |
| Calendar integration | Search/filter threads | Resilience (retry, timeout, zombie detection) |

---

## The Museum Pipeline (Core Innovation)

The central UI concept: **every museum contact moves through a visual pipeline**, similar to how museums move through the Content Factory's 10-stage conveyor belt.

### Pipeline Stages

| Stage | Name | Description | Owner |
|-------|------|-------------|-------|
| 0 | **Identified** | Museum added to target list, basic info captured | Touri |
| 1 | **Researched** | Deep research completed: website, LinkedIn, news, audioguide, insights | Touri |
| 2 | **Personalized** | 5 insights, hypothesis, hook line, conversation starter generated | Touri |
| 3 | **Outreach Sent** | First message sent (email and/or LinkedIn connection) | Touri + Hermann |
| 4 | **In Sequence** | Active in 3-step sequence (Day 0/3/5/8/10 cadence) | Touri |
| 5 | **Responded** | Reply received, scored (1-5), response drafted | Touri + Hermann |
| 6 | **Demo Scheduled** | Meeting booked via Google Calendar | Hermann |
| 7 | **Demo Completed** | Demo done, follow-up actions defined | Hermann |
| 8 | **Proposal Sent** | Museum-specific pilot proposal delivered | Hermann + Touri |
| 9 | **Negotiating** | Active deal discussion | Hermann |
| 10 | **Won / Lost / Nurture** | Final outcome recorded with learnings | Both |

### Pipeline Visualization

Inspired by the Content Factory's pipeline-progress-tracker component:

- **Board view:** Kanban columns for each stage, museum cards that move left to right
- **List view:** Sortable table with all museums showing current stage, score, last action, next action, days in stage
- **Detail view:** Single museum page with full history, all messages sent/received, research insights, personalization package, timeline of interactions
- **Dashboard widgets:** Total in pipeline, conversion rates per stage, average days per stage, bottleneck alerts

### Auto-Advancement

Like the Content Factory's `STAGE_PROGRESSION` map, certain stage transitions happen automatically:

- Stage 0 → 1: Auto-triggered when research agent completes
- Stage 1 → 2: Auto-triggered when personalization engine completes
- Stage 3 → 4: Auto-triggered when first email is confirmed sent
- Stage 5: Auto-scored by AI when reply detected

Manual transitions (require Hermann's action):
- Stage 2 → 3: Hermann reviews and approves the personalized outreach
- Stage 5 → 6: Hermann confirms demo booking
- Stage 6 → 7+: Hermann drives from demo onward

> The pipeline ensures **nothing falls through the cracks**. Every museum is always at a defined stage with a clear next action.

---

## Architecture

### Tech Stack

| Layer | Technology | Inherited From | Why |
|-------|-----------|---------------|-----|
| **Frontend** | Next.js (React) | HenryBot Dashboard | Rich dashboard + chat in one app |
| **Chat UI** | React components | ChatProgElectron | Thread management, voice, image upload |
| **Backend** | Python | HenryBot | Agent framework, memory, LLM gateway |
| **Database** | SQLite (local) | HenryBot | Zero-config, shared with Python tools |
| **Job Queue** | BullMQ + Upstash Redis | Content Factory | Async research tasks, email scheduling |
| **LLM Gateway** | Multi-provider (Anthropic, OpenAI, Google) | HenryBot | Best model per task, cost optimization |
| **Chat Interface** | Telegram + Web Dashboard | HenryBot + ChatProgElectron | Mobile (Telegram) + Desktop (Dashboard) |

### Deployment

| Component | Where | Cost |
|-----------|-------|------|
| Dashboard + API | Local (Mac Mini) or Vercel | Free |
| Python backend (agent loop) | Local (launchd) | Free |
| Redis (job queue) | Upstash (pay-as-you-go) | ~$1/month |
| LLM API costs | Anthropic, OpenAI, Google | ~$50-150/campaign |
| **Total infrastructure** | | **~$1-5/month** |

### Module Map

```
AITourPilot-marketing-platform/
├── CLAUDE.md                    # System handbook (GOTCHA framework)
├── soul.md                      # TouriBot personality
├── args/
│   └── settings.yaml            # All configuration (models, costs, regions)
├── tools/
│   ├── api/                     # LLM gateway, agent loop, cost logger
│   ├── pipeline/                # Museum pipeline stages (NEW)
│   │   ├── stages/              # Stage handlers (00-research through 10-outcome)
│   │   ├── orchestrator.py      # Auto-advancement, stage routing
│   │   └── pipeline_db.py       # Pipeline state persistence
│   ├── outreach/                # Email + LinkedIn message generation (NEW)
│   │   ├── personalization.py   # Deep research + insight generation
│   │   ├── sequences.py         # 3-step message templates
│   │   ├── response_scorer.py   # AI-powered reply classification
│   │   └── email_sender.py      # SMTP / Instantly.ai integration
│   ├── memory/                  # 3-tier memory system (from HenryBot)
│   ├── tasks/                   # Kanban task board (from HenryBot)
│   ├── notes/                   # Numbered notes system (from HenryBot)
│   ├── executors/               # Agent SDK, session manager, research
│   ├── router/                  # Model routing (haiku/sonnet/opus)
│   ├── heartbeat/               # Morning briefing, health checks
│   ├── calendar/                # Calendar integration
│   └── integrations/            # Telegram, LinkedIn, email services
├── touri-dashboard/             # Next.js app (from HenryBot dashboard)
│   ├── app/
│   │   ├── dashboard/           # Overview: pipeline stats, activity feed
│   │   ├── pipeline/            # Museum pipeline board + detail views
│   │   ├── chat/                # Chat interface (from ChatProgElectron)
│   │   ├── board/               # Kanban task board
│   │   ├── calendar/            # Activity calendar
│   │   ├── costs/               # Cost monitor
│   │   ├── notes/               # Shared notes
│   │   ├── memory/              # Memory browser
│   │   └── models/              # Model selector + cache stats
│   └── components/
│       ├── pipeline/            # Pipeline tracker, museum cards, stage badges
│       ├── chat/                # Message bubbles, composer, voice, images
│       └── ui/                  # Shared components (shadcn/ui)
├── data/
│   ├── touri.db                 # Main SQLite: pipeline, tasks, notes, memory
│   ├── costs.db                 # Cost tracking (from HenryBot)
│   └── memory.db                # Memory vectors + FTS5 (from HenryBot)
├── output/                      # Generated content (emails, one-pagers, research)
└── hardprompts/                 # Architecture docs, pipeline specs
```

---

## The Chat Experience

### Two Interfaces, One Brain

| Interface | Use Case | Technology |
|-----------|---------|-----------|
| **Telegram** (mobile) | Quick commands, approvals, notifications on the go | python-telegram-bot (from HenryBot) |
| **Web Dashboard** (desktop) | Deep work: reviewing research, editing messages, pipeline management | Next.js + React (ChatProgElectron-inspired chat) |

### Chat Capabilities (Inherited + New)

**From ChatProgElectron:**
- Thread-based conversations with search and rename
- Push-to-talk voice input with OpenAI transcription
- Image and file upload with inline preview
- Markdown rendering with syntax-highlighted code blocks
- Auto-resizing composer with drag-and-drop

**From HenryBot:**
- Persistent memory across sessions (3-tier: USER.md / MEMORY.md / memory.db)
- Context-aware prompt building (memory search + daily logs + conversation history)
- Automatic memory extraction from conversations
- Session compaction when context budget is reached
- Multi-agent spawning for parallel research

**New for TouriBot:**
- Pipeline-aware context: Touri knows which museums are at which stage
- Inline pipeline actions: "Research Museum X" triggers Stage 0→1 progression
- Message draft preview: see the personalized email before approving send
- Quick approval buttons: "Approve and Send" / "Edit First" / "Skip"
- Museum context cards in chat: when discussing a museum, its pipeline card appears inline

---

## Model Selector

TouriBot does not need coding or code research models. It needs models optimized for the marketing pipeline.

### Model Areas

| Area | Default Model | Purpose |
|------|--------------|---------|
| **Brain** | claude-sonnet-4-6 | Main conversation, task routing, decisions |
| **Heartbeat** | claude-haiku-4-5 | Morning briefing, health checks, auto-scoring |
| **Content Writing** | claude-sonnet-4-6 | Email drafts, LinkedIn posts, proposals |
| **Voice** | gpt-4o-mini-transcribe | Push-to-talk transcription |
| **Image Understanding** | claude-sonnet-4-6 | Analyze screenshots, LinkedIn profiles |
| **Research** | gemini-2.5-pro | Museum website analysis, competitor monitoring |
| **Deep Research** | gemini-3.1-pro-preview | Comprehensive museum profiles, market analysis |
| **Fast Research** | gemini-2.5-flash | Quick lookups, URL scraping, fact checking |
| **Response Scoring** | claude-haiku-4-5 | Classify email replies (Score 1-5) |
| **Personalization** | claude-sonnet-4-6 | Generate per-museum insight packages |

### Cost Controls (From HenryBot)

- Per-run cap: $5 (prevents runaway research)
- Per-day cap: $10 (alerts at 80%)
- Hard stop: $25/day (emergency brake)
- Per-task cost attribution via contextvars
- Dashboard cost charts with model breakdown

---

## Morning Briefing (Pipeline-Focused)

Every morning at 8:00 AM, Touri sends a Telegram briefing. Unlike HenryBot's AI news focus, this is **pure pipeline intelligence**.

### Briefing Sections

1. **Pipeline Status**: X museums in pipeline, Y at Stage 3+, Z responses pending
2. **Today's Actions**: Scheduled emails, LinkedIn touches due, follow-ups triggered
3. **Responses Overnight**: New replies received, auto-scored, drafts ready for review
4. **Stale Contacts**: Museums stuck at a stage for >5 days (bottleneck alert)
5. **LinkedIn Activity**: Profile views from target contacts, engagement on recent posts
6. **Budget Status**: Spend vs. plan (tools, ads, AI tokens)
7. **This Week's Calendar**: Scheduled demos, content posting dates, ad start/end

> The briefing ensures Hermann starts every day knowing exactly what needs attention, without having to check multiple tools.

---

## Task Board (Mutual Assignment)

Inherited from HenryBot's kanban system, adapted for the human-AI collaboration model.

### Who Assigns What

| Assigner | Assignee | Example Tasks |
|----------|---------|---------------|
| Hermann → Touri | Research | "Research Museum X -- find their digital strategy" |
| Hermann → Touri | Writing | "Draft a personalized email for Museum Y" |
| Hermann → Touri | Analysis | "Score and classify yesterday's 5 email replies" |
| Touri → Hermann | Action | "Review and approve 3 outreach messages" |
| Touri → Hermann | Action | "LinkedIn: comment on [Contact]'s recent post" |
| Touri → Hermann | Decision | "Museum Z replied with interest -- schedule demo?" |

### Task Lifecycle

Backlog → Todo → In Progress → In Review → Done → Archived

Each task has: priority (urgent/high/medium/low), assignee (hermann/touri), linked museum (pipeline reference), definition of done, cost tracking.

---

## Notes System

Numbered notes for things that must not be forgotten. Shared between Hermann and Touri.

### Use Cases

- **Objection patterns**: "Museum X said they worry about WiFi -- here's what we learned"
- **Pricing decisions**: "Offered Museum Y a 50% pilot discount for case study rights"
- **Contact intel**: "Museum Z's Director mentioned budget approval in Q3"
- **Template iterations**: "Version 3 of the Insight Hook performs better -- here's why"
- **Campaign learnings**: "LinkedIn posts with video get 3x engagement vs. text-only"

Notes are searchable, taggable, and referenced by number in conversations: "See Note #14 for the WiFi objection response."

---

## What TouriBot Does NOT Need (Scope Control)

Explicitly excluded to keep the project lean and deliverable:

| Excluded | Why |
|----------|-----|
| Code editing / generation | Not a development tool |
| Code research | Not a development tool |
| Blog/news RSS watching | Not relevant for museum outreach |
| Obsidian/Notion integration | Overkill for this scope |
| Apple Notes integration | Not needed |
| GitHub issues management | Git is for code storage only |
| Skills engine (plugin system) | Premature abstraction |
| Telegram group chat | Single-user system |
| Multi-user auth | Hermann is the only user |

---

## Build Plan

### Phase 1: Foundation (Week 1-2)

**Goal:** Working chat + memory + pipeline database. No UI yet -- Telegram-first.

| Task | Source | Effort |
|------|--------|--------|
| Fork HenryBot's core: GOTCHA framework, memory, API gateway, cost logger | HenryBot | 2-3h |
| Create soul.md for Touri personality | New | 1h |
| Create settings.yaml (strip coding models, add marketing models) | HenryBot | 30min |
| Build pipeline_db.py: museums table with 11 stages, contacts, messages, scores | New | 2-3h |
| Add pipeline tool to brain tools (create/update/query museums) | New | 1-2h |
| Wire Telegram bot for basic chat + pipeline commands | HenryBot | 1-2h |
| Import 74 warm contacts into pipeline at Stage 0 | New | 1h |
| **Total** | | **~10-14h** |

**Milestone:** Can chat with Touri via Telegram, ask "what's in the pipeline?", and get an answer with memory.

### Phase 2: Outreach Engine (Week 3-4)

**Goal:** Touri can research museums, generate personalization packages, and draft messages.

| Task | Source | Effort |
|------|--------|--------|
| Build personalization.py: museum website scrape + LinkedIn + insights generation | New (uses HenryBot research executor pattern) | 3-4h |
| Build sequences.py: 3-step message templates with personalization merge | New | 2h |
| Build response_scorer.py: AI classification of replies (Score 1-5) | New | 2h |
| Add auto-advancement logic: Stage 0→1, 1→2, 3→4, reply→5 | Content Factory pattern | 2-3h |
| Wire email sending (SMTP or Instantly.ai API) | New | 2-3h |
| Morning briefing adapted for pipeline status | HenryBot heartbeat | 2h |
| **Total** | | **~15-18h** |

**Milestone:** Can say "Research Rijksmuseum" and get a full personalization package. Can review and approve outreach messages via Telegram.

### Phase 3: Dashboard (Week 5-7)

**Goal:** Visual pipeline, chat interface, full monitoring.

| Task | Source | Effort |
|------|--------|--------|
| Fork HenryBot dashboard (Next.js) | HenryBot | 2h |
| Build pipeline board view (kanban columns for 11 stages) | Content Factory tracker + New | 6-8h |
| Build museum detail page (history, messages, research, timeline) | New | 4-5h |
| Integrate ChatProgElectron chat UI into dashboard | ChatProgElectron | 4-5h |
| Add voice input (push-to-talk from ChatProgElectron) | ChatProgElectron | 2h |
| Cost monitor page | HenryBot | 1h (copy) |
| Calendar page with daily activities | HenryBot | 2h |
| Notes page | HenryBot | 1h (copy) |
| Dashboard overview with pipeline stats | New | 3-4h |
| **Total** | | **~25-30h** |

**Milestone:** Full visual dashboard with pipeline tracking, chat, costs, calendar, notes.

### Phase 4: Optimization (Week 8+)

- A/B message testing (track which templates get higher reply rates)
- LinkedIn post scheduler integration
- Response time analytics (how fast do museums reply?)
- Pipeline conversion funnel visualization
- Export capabilities (pipeline report PDF, contact lists CSV)

### Total Estimated Effort

| Phase | Effort | Weeks |
|-------|--------|-------|
| Foundation | 10-14h | 1-2 |
| Outreach Engine | 15-18h | 3-4 |
| Dashboard | 25-30h | 5-7 |
| Optimization | Ongoing | 8+ |
| **Total to MVP** | **~50-62h** | **~7 weeks** |

This is realistic for evening/weekend work alongside the campaign itself. Phase 1 enables the campaign to start immediately via Telegram while the dashboard is built in parallel.

---

## Architecture Decisions (Finalized)

Based on our dialogue, these decisions are locked in:

| # | Decision | Choice | Rationale |
|---|----------|--------|-----------|
| 1 | **Dashboard vs. Telegram-first** | Dashboard-first | Wait for full dashboard before launching campaign. Avoids mess of building while running. Claude Code will build it fast. |
| 2 | **Email sending** | Manual-first, Instantly.ai on standby | Start by sending manually from hermann@aitourpilot.co (dedicated outreach domain -- see [Infrastructure Blueprint](../technical/20260318-outreach-infrastructure-blueprint.html)) for maximum personal touch. Touri drafts and schedules, Hermann hits send. Switch to Instantly.ai only if volume overwhelms (50+ active follow-ups). |
| 3 | **LinkedIn automation** | Draft-only (A) | Touri drafts all LinkedIn messages. Hermann copy-pastes into LinkedIn. Zero automation risk to account. |
| 4 | **Pipeline granularity** | Per-museum (A) | Museums are the primary entity. Contacts are sub-records under each museum. You sell to institutions, not individuals. |
| 5 | **Auto-send level** | Approve-first (B) with visibility | Hermann reviews and approves Message 1 (most critical). Messages 2 and 3 are queued on schedule -- visible in calendar and clickable for last-minute edits. If Hermann doesn't intervene, they send automatically. Trust the system after Message 1. |
| 6 | **Campaign vs. build timing** | Build first, campaign after | Complete the full platform before launching outreach. No parallel mess. This is a sprint build with Claude Code. |

---

## Self-Healing System (From HenryBot)

Critical for overnight reliability when Touri runs autonomous tasks (research, email scheduling, follow-up queuing).

### Heartbeat Loop (Every 15 Minutes)

Inherited from HenryBot's proven self-healing architecture:

| Check | What It Does | Recovery Action |
|-------|-------------|-----------------|
| **Zombie task detection** | Finds tasks stuck in "in_progress" with no activity for >30min | Auto-fails, notifies Hermann, optionally restarts |
| **Stale session reaper** | Detects agent sessions that timed out or crashed | Kills process, releases session slot, logs error |
| **Pipeline orphan detector** | Finds museums stuck at a stage with no active job | Re-enqueues the missing stage job |
| **Email queue health** | Checks if scheduled emails are overdue (>1 hour past scheduled time) | Alerts Hermann, does NOT auto-send (safety) |
| **Database integrity** | Verifies SQLite WAL, checks for corruption | Auto-checkpoint, alert if repair needed |
| **Disk/memory/CPU** | System resource monitoring | Alert at 80% thresholds |
| **API key validity** | Tests Anthropic/OpenAI/Google API keys | Alert if any key is expired or rate-limited |

### Kanban Healer (From HenryBot)

If a task is assigned to Touri and has been "in_progress" for >2 hours with no update:

1. Check if an active agent session exists for it
2. If no session: build a resume prompt with task description + last comments
3. Spawn a new session to pick it up (max 3 retries)
4. If 3 retries exhausted: move to "in_review" and notify Hermann

### Self-Healing for Email Sequences

When a museum is at Stage 4 (In Sequence) and the next scheduled email is overdue:

- If email was auto-approved (Messages 2/3): attempt send, alert on failure
- If email needs manual approval (Message 1): escalate to Hermann via Telegram + calendar alert
- If email bounces: flag the contact, update pipeline score, suggest alternate contact

> The system should never silently fail. Every error produces a visible alert and a recovery action.

---

## Process Knowledge (Touri's Domain Expertise)

Touri must internalize the complete Precision Partner Acquisition Engine strategy. This is not just a tool -- it's a knowledgeable companion that can guide Hermann through each step.

### What Touri Knows

| Domain | Knowledge Source | Use Case |
|--------|-----------------|----------|
| **The 6-module outreach system** | 20260314-precision-partner-acquisition-engine.html | Guide Hermann through ICP definition, research, personalization, sequencing |
| **Museum industry landscape** | Competitor analysis, KB research docs | Answer questions like "How does Smartify work?" or "What's Gesso's pricing?" |
| **Spring 2025 campaign data** | 20260314-linkedin-campaign-spring-2025-analysis.html | Reference what worked, what CTR to expect, what hooks performed |
| **La Pedrera proposal** | La Pedrera 5-pager, visitor calculations | Template for future proposals, pricing benchmarks |
| **Engagement response framework** | Campaign analysis doc | How to respond to critics, the "revive curiosity, not resolve it" positioning |
| **Product capabilities** | Content Factory exec summary, KB docs | 28 museums, 5 languages, ~$8/month infrastructure, 24h museum onboarding |
| **Pricing model** | Business model doc, La Pedrera calculations | EUR 45-75K implementation, EUR 24-42K/year license, per-visitor cost $1.80 |
| **Award** | EU Business News "Best Emerging Cultural AI Experience 2026" | Weave into every outreach and LinkedIn post |

### How Touri Uses This Knowledge

When Hermann asks "I have a call with a history museum in Denmark tomorrow, help me prepare":

1. Touri checks the pipeline for that museum's record
2. Pulls the personalization package (Module 3 output)
3. References similar museums in the data (Moesgaard Museum is a Danish subscriber)
4. Pulls relevant competitor info (izi.TRAVEL is Amsterdam-based, strong in Nordics)
5. Suggests talking points tailored to history museums
6. Reminds Hermann of the "Best Emerging Cultural AI Experience" award for credibility
7. Drafts a follow-up email template ready for after the call

### Process Guidance Mode

When Hermann says "What should I do next?", Touri:

1. Checks the current week against the 8-week execution timeline
2. Reviews the pipeline: how many museums at each stage
3. Identifies the highest-leverage action right now
4. Provides a concrete, actionable next step

Example response:
> "You're in Week 3. You have 15 museums at Stage 3 (Outreach Sent), 4 at Stage 5 (Responded). Two Score-4 replies are waiting for your review -- I've drafted responses. The LinkedIn teaser for this week is ready for your approval. I'd prioritize the two Score-4 replies first -- they're warm. See Note #7 for the last one's objection about WiFi."

---

## Apple Calendar and Email Integration

### Apple Calendar (Proven in HenryBot)

HenryBot's calendar integration works reliably. Touri inherits the same approach:

| Feature | How It Works |
|---------|-------------|
| **Read calendar** | Query Apple Calendar via AppleScript/EventKit for today's events, upcoming demos |
| **Create events** | Schedule email send reminders, demo prep blocks, LinkedIn posting reminders |
| **Morning briefing** | Include today's calendar events in the daily digest |
| **Email review events** | Create calendar events for pending Message 2/3 sends, clickable to review |

### Email Review Flow in Calendar

This is the key UX for the "approve-first, visible rest" model:

```
Message 1 drafted by Touri
        ↓
Calendar event created: "Review & Send: Museum X - Email 1"
  - Date: Today (or when Hermann wants)
  - Notes field contains: full email text + one-click edit link
  - Hermann reviews, adjusts if needed, sends manually
        ↓
Message 1 sent → Pipeline moves to Stage 4
        ↓
Calendar event auto-created: "Queued: Museum X - Email 2 (Day 3)"
  - Date: 3 days after Message 1
  - Notes: full email text, editable until send time
  - If Hermann clicks and edits: updated version sends
  - If Hermann ignores: original version auto-sends at scheduled time
        ↓
Calendar event auto-created: "Queued: Museum X - Email 3 (Day 8)"
  - Same pattern as Email 2
```

**Calendar event color coding:**
- Red: needs Hermann's action (Message 1 review, Score 5 reply)
- Orange: auto-sends soon, editable (Message 2/3 queued)
- Green: completed actions (sent, demo done)
- Blue: scheduled demos and calls

### Apple Mail Integration

For manual sending from hermann@aitourpilot.co (outreach domain):

| Feature | How It Works |
|---------|-------------|
| **Draft creation** | Touri creates a draft in Apple Mail via AppleScript with To, Subject, Body pre-filled |
| **Send reminder** | Calendar event links to the draft -- Hermann opens, reviews, sends |
| **Reply detection** | Monitor inbox for replies from pipeline contacts (regex match on known email addresses) |
| **Auto-scoring** | When a reply is detected, Touri reads it, scores it (1-5), drafts a response |

> The integration keeps Hermann in his natural email workflow (Apple Mail) while Touri handles all the preparation and scheduling behind the scenes.

---

## Updated Build Plan

Revised for dashboard-first approach and all decisions above:

### Phase 1: Foundation (Week 1)

| Task | Effort |
|------|--------|
| Fork HenryBot core: GOTCHA, memory, API gateway, cost logger, heartbeat | 2-3h |
| Create soul.md with museum industry knowledge + process expertise | 1-2h |
| Create settings.yaml (marketing model areas, cost caps) | 30min |
| Build pipeline_db.py: museums (11 stages), contacts, messages, scores, email_queue | 3-4h |
| Build pipeline tool for brain (create/update/query/advance museums) | 2h |
| Import 74 warm contacts into pipeline at Stage 0 | 1h |
| Wire Apple Calendar integration (read/write events) | 1-2h |
| Wire self-healing heartbeat with pipeline orphan detection | 2h |
| **Subtotal** | **~13-16h** |

### Phase 2: Outreach Engine (Week 2)

| Task | Effort |
|------|--------|
| Build personalization.py: website scrape + LinkedIn + insight generation | 3-4h |
| Build sequences.py: 3-step message templates with personalization merge | 2h |
| Build response_scorer.py: AI classification of replies (Score 1-5) | 2h |
| Build email_drafter.py: Apple Mail draft creation via AppleScript | 2h |
| Build email_queue.py: schedule Messages 2/3, create calendar events | 2-3h |
| Auto-advancement logic: Stage 0→1, 1→2, 3→4, reply→5 | 2h |
| Morning briefing adapted for pipeline + calendar + email queue status | 2h |
| LinkedIn message drafter (outputs to clipboard/notes for copy-paste) | 1h |
| **Subtotal** | **~16-20h** |

### Phase 3: Dashboard (Week 3-4)

| Task | Effort |
|------|--------|
| Fork HenryBot dashboard (Next.js), strip non-marketing pages | 2h |
| Build pipeline board view (kanban 11-stage, museum cards, drag-and-drop) | 6-8h |
| Build museum detail page (history, messages, research, timeline, contacts) | 4-5h |
| Build chat interface (from ChatProgElectron: threads, voice, images, markdown) | 4-5h |
| Build email review page (pending sends, preview, edit, approve/skip) | 3-4h |
| Cost monitor page (copy from HenryBot) | 1h |
| Calendar page with color-coded pipeline events | 2-3h |
| Notes page (copy from HenryBot) | 1h |
| Dashboard overview (pipeline stats, funnel, activity feed) | 3-4h |
| Model selector + cache stats page | 1-2h |
| **Subtotal** | **~28-35h** |

### Phase 4: Campaign Launch (Week 5+)

> **Infrastructure dependency:** The [Outreach Infrastructure Blueprint](../technical/20260318-outreach-infrastructure-blueprint.html) requires a 6-week email warm-up protocol on aitourpilot.co before full outreach volume. Domain registration and warm-up should begin in Week 1 (parallel to TouriBot Foundation build) so that email reputation is ready when the platform launches in Week 5.

Platform is complete. Campaign begins:

- Week 5: Post LinkedIn award announcement, send reactivation to 74 contacts
- Week 6-7: Launch outreach batches, process responses
- Week 8-9: Demo calls, pilot proposals
- Week 10-12: Close deals

### Total Estimated Effort

| Phase | Effort | Duration |
|-------|--------|----------|
| Foundation | 13-16h | Week 1 |
| Outreach Engine | 16-20h | Week 2 |
| Dashboard | 28-35h | Week 3-4 |
| **Total to campaign launch** | **~57-71h** | **~4 weeks** |

With Claude Code building alongside you, this is achievable in focused evening/weekend work across 4 weeks, or faster in dedicated sprint days.

---

## Additional Decisions (Finalized)

| # | Decision | Choice | Rationale |
|---|----------|--------|-----------|
| 7 | **Telegram** | Notifications only | Dashboard is primary interface. Telegram for: reply alerts, morning briefing, stale pipeline warnings. No full chat. |
| 8 | **Reply detection** | IMAP polling | Monitors hermann@aitourpilot.co (outreach domain) server-side. Works when Mail.app is closed. Essential for overnight auto-scoring. |
| 9 | **Data seeding** | Full context, token-smart (C with Tier 2) | All business docs loaded into memory.db (Tier 2). Searched on demand, never bulk-loaded. CLAUDE.md stays lean. |

---

## Memory Architecture (Token-Smart Knowledge)

The single most important architectural decision: **load everything, surface only what's relevant.**

HenryBot's 3-tier memory system is purpose-built for this. It prevents the context window problem that kills ChatGPT conversations mid-campaign.

### Tier 0: Always In Context (~100 lines, ~2K tokens)

| File | Contents | Loaded |
|------|----------|--------|
| CLAUDE.md | Identity, GOTCHA framework, active pipeline summary, current week | Every message |
| USER.md | Hermann's preferences, communication style, decision history | Every message |
| soul.md | Touri personality, museum industry context, specialist routing | Every message |

**Rule:** CLAUDE.md must never exceed ~100 lines. If it grows, move content to hardprompts/ or Tier 2.

### Tier 1: Working Memory (~5000 chars, auto-managed)

MEMORY.md -- facts that matter right now:

- "Museum X's director mentioned budget approval in Q3" (from a demo call)
- "Email hook version 3 outperforms version 1 by 2x reply rate"
- "Moesgaard Museum contact is on parental leave until June"
- "WiFi objection: use the training-wheels metaphor (see Note #7)"

**Auto-promoted** from conversations when importance >= 8 AND subtype == "permanent". **Auto-expired** after 90 days (unless pinned). FIFO cap of 50 entries. This ensures working memory stays relevant and lean.

### Tier 2: Deep Knowledge (Unlimited, search-only)

memory.db (SQLite with FTS5 + sentence-transformers embeddings):

| Category | Source Documents | Chunks |
|----------|-----------------|--------|
| **Competitor intelligence** | Competitor analysis (Smartify, Gesso, Cuseum, izi.TRAVEL, GuidiGO) | ~50 chunks |
| **Product capabilities** | Content Factory exec summary, pipeline overview, 28 museum details | ~40 chunks |
| **Pricing & business model** | La Pedrera visitor calculations, pricing hypotheses, LTV analysis | ~30 chunks |
| **Campaign history** | Spring 2025 campaign analysis (audience, results, post style, engagement) | ~60 chunks |
| **Strategy playbook** | Precision Partner Acquisition Engine (6 modules, sequences, timeline) | ~40 chunks |
| **Proposal templates** | La Pedrera 5-pager, pilot structure, SLA options | ~20 chunks |
| **Market data** | Market sizing ($412M to $2.15B), industry trends, conference calendar | ~15 chunks |

**Total: ~255 chunks, ~500K characters stored, 0 tokens used until queried.**

### How Search Works

When Hermann asks: "What's our cost per visitor at La Pedrera?"

1. Query is embedded (sentence-transformers, local, free)
2. Hybrid search: 70% vector similarity + 30% FTS5 BM25 keyword match
3. Top 3-5 relevant chunks returned (~500-1000 tokens)
4. Touri answers with precise, sourced information

Cost per query: essentially free (local embeddings) + ~500 tokens of retrieved context. No bulk loading of 30-page documents.

### Hardprompts & Skills (On-Demand Loading)

For structured process knowledge, use the hardprompts/ folder (HenryBot pattern):

```
hardprompts/
├── architecture.md          # This document (for dev reference)
├── outreach_process.md      # The 6-module system, step by step
├── linkedin_playbook.md     # Content calendar, posting rules, hooks
├── objection_handling.md    # Top 10 museum objections + responses
├── email_templates.md       # All message templates (3-step + reactivation)
└── pricing_guide.md         # Pilot pricing, license tiers, negotiation ranges
```

These are loaded into context **only when the relevant skill is activated** -- not on every message. The CLAUDE.md references them by path, and Touri reads them when the conversation topic matches.

> This is the Anthropic skills pattern: keep the main prompt lean, load specialized knowledge on demand. HenryBot does this with its goals/ and hardprompts/ system. Token cost stays minimal while knowledge depth is unlimited.

---

## All Architecture Decisions Summary

| # | Area | Decision |
|---|------|----------|
| 1 | Interface priority | Dashboard-first, no campaign until platform is complete |
| 2 | Email sending | Manual from Apple Mail via hermann@aitourpilot.co (Touri drafts, Hermann sends). Instantly.ai on standby. |
| 3 | LinkedIn | Draft-only. Touri writes, Hermann copy-pastes. Zero automation. |
| 4 | Pipeline entity | Per-museum. Contacts as sub-records. |
| 5 | Auto-send | Approve Message 1. Messages 2/3 auto-send on schedule, visible + editable in calendar. |
| 6 | Build vs campaign | Build first (4 weeks), then campaign. |
| 7 | Telegram | Notifications only (reply alerts, morning briefing, stale warnings). |
| 8 | Reply detection | IMAP polling on hermann@aitourpilot.co (outreach domain). Works overnight. |
| 9 | Knowledge loading | Full context in Tier 2 (search-only). CLAUDE.md lean. Hardprompts on demand. |

---

*Architecture spec complete. All decisions finalized through dialogue on March 17, 2026.*

*Based on: HenryBot v3.2 architecture, ChatProgElectron chat system, AITourPilot Content Factory pipeline, and Precision Partner Acquisition Engine strategy.*

*Version 3 (Final) -- March 2026*
