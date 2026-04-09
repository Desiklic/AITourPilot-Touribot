# 20260407_TOURIBOT_BUILD_PLAN

*Source: Development Docs / 20260407_TOURIBOT_BUILD_PLAN.md*

# TouriBot Implementation Plan

**Date:** 2026-04-07
**Project:** /Users/hermannkudlich/Documents/ClaudeProjects/AITourPilot-Touribot
**Architecture:** See ARCHITECTURE.md (780 lines, full component design)
**Status:** Ready to build

---

## Context for Future Agents

This document is the complete implementation plan for TouriBot — an AI-powered museum outreach assistant. **Any agent executing this plan should read these documents first:**

1. `ARCHITECTURE.md` (in project root) — component design, data model, interface, soul.md template
2. This file — phased build steps with verification criteria
3. HenryBot source at `~/HenryBot/` — memory system to extract from

### What TouriBot Is

A CLI-based AI assistant that helps Hermann Kudlich (sole founder of AITourPilot) write deeply personalized outreach emails to museum professionals. It maintains persistent memory of all business context, every email drafted, every response received, and learns from outcomes.

### What TouriBot Is NOT

- Not a general-purpose assistant
- Not a web app or dashboard (v1 is CLI only)
- Not a fork of HenryBot (built from scratch, selectively extracts memory system)
- Not an email sender (Hermann always sends manually)

### Key Constraints

- **Python 3.12** (installed at /Users/hermannkudlich/Documents/Miniforge3/envs/comfyenv/)
- **Anthropic SDK** for LLM calls (not Agent SDK — direct API is simpler for this use case)
- **sentence-transformers** globally installed (all-MiniLM-L6-v2, 384-dim)
- **sqlite-vec** 0.1.6 installed for accelerated vector search
- **SQLite** for all persistence (no external databases)
- All emails sent from `hermann@aitourpilot.com` (Zoho, .com domain) — NOT from .co

---

## Research Findings Summary

### From Deep Investigator (HenryBot Codebase Analysis)

**Memory system files to extract (4 files, ~1,712 lines total):**
- `~/HenryBot/tools/memory/memory_db.py` (1,142 lines) — core DB engine with hybrid search
- `~/HenryBot/tools/memory/memory_write.py` (301 lines) — write flow with Tier 1 promotion
- `~/HenryBot/tools/memory/memory_read.py` (163 lines) — session-start context loader
- `~/HenryBot/tools/memory/memory_curator.py` (106 lines) — daily expiry

**Key adaptation needed:** Change `DB_PATH` constants, replace HenryBot-specific topic routes with TouriBot categories (leads, emails, campaign_strategy, product_knowledge). Remove Telegram alert dependencies.

**External dependencies confirmed installed:**
- `sentence-transformers` 5.2.2 (all-MiniLM-L6-v2)
- `sqlite-vec` 0.1.6
- `anthropic` SDK
- `PyYAML`
- `beautifulsoup4`, `html2text` (for knowledge ingestion)

### From External Researcher (Tools & Patterns)

**Claude API (not Agent SDK):** Use the Anthropic Python SDK directly (`anthropic.Anthropic().messages.create()`). Agent SDK is overkill for TouriBot's sequential tasks. Direct API gives: system prompt control, streaming, tool use if needed, and simpler error handling.

**CLI interface:** Use `prompt_toolkit` (needs install) for rich input with multiline support + `rich` (already installed v13.9.4) for formatted output with markdown rendering.

**Email drafting:** Apple Mail via AppleScript is simplest for the initial version. Gmail API is the robust alternative. Since Hermann sends from Zoho (Apple Mail client), AppleScript drafts work. BUT for v1: just save drafts to `output/emails/` as markdown files. Hermann copy-pastes into email client. This is the fastest path.

**Reply detection:** Manual for v1. Hermann pastes reply text into `log-response` command. Automated IMAP/Gmail API polling is Phase 5+.

**Embedding model recommendation:** Consider upgrading to `BAAI/bge-small-en-v1.5` (same 384-dim, better MTEB scores). BUT for v1: keep `all-MiniLM-L6-v2` — it's already installed and working. Don't add migration risk.

### From Museum Sales Specialist

**Prioritized contact list (Week 1-2):**
1. Georgie Power — SS Great Britain (UK) — had a meeting, warmest lead
2. Lisa Witschnig — Universalmuseum Joanneum (Austria) — DACH home ground
3. Nils van Keulen — Slot Loevestein (Netherlands) — sophisticated buyer
4. Sebastien Mathivet — Cap Sciences (France) — innovation-forward
5. Treglia-Detraz — MAH Geneva (Switzerland) — premium market

**La Pedrera: REMOVED** (declined Feb 2026)

**Key timing:** Museum AI Summit May 27-28 (virtual). Outreach should land in inboxes before that.

---

## Build Phases

---

### PHASE 1: Core Intelligence (Day 1 — ~6 hours)

#### Goal
Touri is alive. Hermann can talk to her and she remembers across sessions.

#### Files to Create

| File | Lines (est.) | Description |
|------|-------------|-------------|
| `soul.md` | 80 | Touri's identity (template in ARCHITECTURE.md Section F) |
| `memory/USER.md` | 20 | Hermann's identity for Tier 0 |
| `memory/MEMORY.md` | 5 | Empty Tier 1 (will fill over time) |
| `args/settings.yaml` | 80 | Stripped config: models, memory, session, cost_caps |
| `.env` | 5 | ANTHROPIC_API_KEY only |
| `.gitignore` | 30 | data/, .env, __pycache__, output/ |
| `requirements.txt` | 15 | All pip dependencies |
| `tools/__init__.py` | 0 | Package init |
| `tools/memory/__init__.py` | 0 | Package init |
| `tools/memory/memory_db.py` | ~1142 | **COPY from HenryBot** — update DB_PATH |
| `tools/memory/memory_write.py` | ~301 | **COPY from HenryBot** — update paths, topic routes |
| `tools/memory/memory_read.py` | ~163 | **COPY from HenryBot** — update paths |
| `tools/memory/memory_curator.py` | ~106 | **COPY from HenryBot** — update paths |
| `tools/chat/__init__.py` | 0 | Package init |
| `tools/chat/session.py` | ~200 | Chat session: context build, Anthropic API call, memory extraction, conversation log |
| `run.py` | ~100 | Entry point: `chat`, `recall`, `remember` commands |
| `CLAUDE.md` | 50 | Lean project handbook |

#### Files to Copy from HenryBot (with modifications)

**Source:** `~/HenryBot/tools/memory/memory_db.py`
**Target:** `tools/memory/memory_db.py`
**Changes:**
- Update `DB_PATH` computation to use `TOURI_DATA_DIR` env var or `data/memory.db` relative to project root
- Remove any imports that reference HenryBot-specific modules
- Keep ALL search logic (hybrid_search, FTS5, vector, MMR, temporal decay) unchanged

**Source:** `~/HenryBot/tools/memory/memory_write.py`
**Target:** `tools/memory/memory_write.py`
**Changes:**
- Update `HENRYBOT_DIR` → project root path
- Replace `_TOPIC_ROUTES` keywords: `projects/preferences/people/gotcha` → `leads/emails/campaign/product/museums`
- Update `MEMORY_MD_PATH` to `memory/MEMORY.md` relative to project root

**Source:** `~/HenryBot/tools/memory/memory_read.py`
**Target:** `tools/memory/memory_read.py`
**Changes:**
- Update path constants
- Update topic file references

**Source:** `~/HenryBot/tools/memory/memory_curator.py`
**Target:** `tools/memory/memory_curator.py`
**Changes:**
- Update `HENRYBOT_DIR` → project root path

#### What Changes and Why

The memory system is TouriBot's backbone — it enables cross-session learning and persistent business context. Copying from HenryBot saves ~20 hours of reimplementation. The modifications are limited to path constants and topic classification keywords.

The chat session (`tools/chat/session.py`) is NEW. It:
1. Loads `soul.md` + `memory/MEMORY.md` as system prompt
2. Searches memory DB for context relevant to the user's message
3. Calls Anthropic API (`claude-sonnet-4-6`) with assembled context
4. Streams response to terminal via `rich`
5. After response, runs a memory extraction pass: evaluates the exchange for facts worth saving
6. Appends exchange to `memory/logs/YYYY-MM-DD.md`

#### Safety Invariants
- memory_db.py schema creation must be idempotent (CREATE TABLE IF NOT EXISTS)
- `.env` must be in `.gitignore` before first commit
- Never auto-modify `memory/USER.md` (sacred, human-only)
- `TOKENIZERS_PARALLELISM=false` must be set before importing sentence-transformers

#### How to Verify Phase 1

```bash
# 1. Start a chat session
python run.py chat
# Type: "Hello, I'm Hermann. Tell me about yourself."
# Expected: Touri responds with identity from soul.md

# 2. Test memory persistence
# Type: "Remember that Georgie Power at SS Great Britain had a meeting with us a year ago"
# Type: "exit"

# 3. Start a new session
python run.py chat
# Type: "What do you know about SS Great Britain?"
# Expected: Touri recalls the Georgie Power fact from the previous session

# 4. Test recall command
python run.py recall "SS Great Britain"
# Expected: Returns the memory about Georgie Power
```

---

### PHASE 2: Knowledge Loaded (Day 2 — ~4 hours)

#### Goal
Touri knows everything about AITourPilot — product, pricing, competition, strategy, email templates, objection handling.

#### Files to Create

| File | Lines (est.) | Description |
|------|-------------|-------------|
| `tools/knowledge/__init__.py` | 0 | Package init |
| `tools/knowledge/ingest.py` | ~150 | HTML → markdown extractor |
| `knowledge/raw/` | — | Directory for source HTML files (symlinks or copies) |
| `knowledge/processed/*.md` | ~7 files | Extracted markdown from each source document |
| `hardprompts/business_context.md` | ~100 | Condensed product brief (always loaded) |
| `hardprompts/email_templates.md` | ~80 | The 3-step sequence templates |
| `hardprompts/objection_handling.md` | ~60 | Common museum objections + responses |
| `hardprompts/pipeline_guide.md` | ~40 | Stage definitions and transitions |

#### Source Documents to Ingest

| # | Source File | Target | Priority |
|---|-----------|--------|----------|
| 1 | `~/Desktop/AITourPilot Project/BUSINESS_CONTENT/wiki/marketing-platform/20260314-precision-partner-acquisition-engine.html` | `knowledge/processed/precision_partner_engine.md` | P0 |
| 2 | `~/Desktop/AITourPilot Project/BUSINESS_CONTENT/wiki/marketing-platform/20260406-campaign-launch-research-summary.html` | `knowledge/processed/campaign_research.md` | P0 |
| 3 | `~/Desktop/AITourPilot Project/BUSINESS_CONTENT/wiki/marketing-platform/20260403-aitourpilot-product-overview-platform-benefits-and-case-study.html` | `knowledge/processed/product_overview.md` | P1 |
| 4 | Extract email templates section from Engine doc | `hardprompts/email_templates.md` | P0 |
| 5 | Extract engagement response framework from Spring 2025 campaign analysis | `hardprompts/objection_handling.md` | P1 |
| 6 | Extract museum procurement section from campaign research | `knowledge/processed/museum_procurement.md` | P1 |
| 7 | LinkedIn Campaign Spring 2025 Analysis (for what worked/didn't) | `knowledge/processed/campaign_2025_analysis.md` | P2 |

#### Changes to Existing Files

**`tools/chat/session.py`** — Update context assembly:
- Always load: `soul.md` + `memory/MEMORY.md` + `hardprompts/business_context.md`
- Load when drafting emails: `hardprompts/email_templates.md`
- Load when scoring responses: `hardprompts/objection_handling.md`
- Load on demand: any `knowledge/processed/*.md` when the topic is relevant

**`run.py`** — Add commands:
- `ingest` — runs knowledge ingestion
- `recall "<query>"` — searches memory (if not already added in Phase 1)
- `remember "<fact>"` — saves a fact to memory

#### Safety Invariants
- Ingestion must be idempotent (running `ingest` twice produces the same output)
- Source HTML files are read-only — never modify originals
- Knowledge files must be markdown only — no HTML in processed output
- Context assembly must respect Claude's context window limit (~200K tokens)

#### How to Verify Phase 2

```bash
# 1. Run ingestion
python run.py ingest
# Expected: 7 files created in knowledge/processed/

# 2. Test knowledge access
python run.py chat
# Type: "What is AITourPilot's pilot pricing?"
# Expected: "EUR 8,000-12,000 for 90 days" or similar from ingested docs

# Type: "What are the 3 steps in the outreach email sequence?"
# Expected: Describes Message 1 (Insight Hook), Message 2 (Hypothesis), Message 3 (Pattern Interrupt)

# Type: "Who are AITourPilot's competitors?"
# Expected: Lists Smartify, Gesso, Cuseum, izi.TRAVEL with correct differentiators

# Type: "What does a Tier 1 museum look like?"
# Expected: Heritage sites, 500K-5M visitors, UNESCO-listed, rich archives
```

---

### PHASE 3: Email Drafting Engine (Day 3 — ~6 hours)

#### Goal
Touri drafts a museum-specific personalized email — the core product value.

#### Files to Create

| File | Lines (est.) | Description |
|------|-------------|-------------|
| `tools/outreach/__init__.py` | 0 | Package init |
| `tools/outreach/personalizer.py` | ~150 | Builds per-museum context package |
| `tools/outreach/drafter.py` | ~200 | Calls Claude with focused drafting prompt, saves output |
| `tools/outreach/scorer.py` | ~100 | Classifies inbound replies 1-5 |
| `output/emails/` | — | Directory for saved email drafts |
| `output/research/` | — | Directory for museum research packages |

#### What Changes and Why

**`tools/outreach/personalizer.py`:**
- Input: museum name + contact name
- Searches memory DB for all `[MUSEUM: name]` tagged memories
- Searches knowledge base for relevant product/strategy context
- Builds a structured brief: what we know, what we don't, suggested angle, preferred language
- Returns a dict used by the drafter

**`tools/outreach/drafter.py`:**
- Input: personalizer brief + message type (initial/follow-up/response) + any Hermann context
- Constructs a focused drafting prompt with: soul.md email principles + personalizer brief + template structure + Hermann's additional context
- Calls Claude (claude-sonnet-4-6) with streaming
- Saves draft to `output/emails/YYYY-MM-DD-contact-name-v1.md`
- Returns draft text for display

**`tools/outreach/scorer.py`:**
- Input: pasted reply text + museum context from personalizer
- Prompt: "Score this reply 1-5 using the framework: 5=meeting, 4=strong interest, 3=bad timing, 2=unclear, 1=decline"
- Returns: score, classification, suggested next action, draft response

#### Changes to Existing Files

**`run.py`** — Add commands:
- `draft "<name>, <institution>"` — drafts an email
- `draft --follow-up <museum_name>` — drafts Message 2 or 3
- `log-response <museum_name>` — score an inbound reply

**`tools/chat/session.py`** — When `draft` intent is detected in chat, automatically load email templates + engagement framework + personalizer output

#### Safety Invariants
- Every draft MUST be saved to output/emails/ before displaying — never lose work
- Drafter must NOT hallucinate museum facts — if uncertain, must say so explicitly
- Scorer must return a score AND explanation — never a bare number
- Never auto-send emails. Drafts only.

#### How to Verify Phase 3

```bash
# 1. Draft a reactivation email
python run.py chat
# Type: "Draft a reactivation email for Georgie Power at SS Great Britain.
#        We had a meeting about a year ago, she seemed interested, neither of us followed up."
# Expected:
#   - Email draft ~150 words, specific to SS Great Britain
#   - Saved to output/emails/YYYY-MM-DD-georgie-power-v1.md
#   - No made-up facts about the museum
#   - Ends with a specific question, not "let me know"

# 2. Draft in German
# Type: "Draft for Lisa Witschnig at Universalmuseum Joanneum, in German"
# Expected: German email, references Joanneum specifically

# 3. Score a reply
python run.py log-response "SS Great Britain"
# Paste: "Thanks Hermann, yes I remember our conversation. We've been busy with
#         our conservation project but I'd love to catch up. How about next week?"
# Expected: Score 5 (meeting requested), suggests booking link, drafts confirmation
```

---

### PHASE 4: Pipeline Tracking (Day 4-5 — ~6 hours)

#### Goal
Touri tracks every museum in the process. Nothing falls through the cracks.

#### Files to Create

| File | Lines (est.) | Description |
|------|-------------|-------------|
| `tools/leads/__init__.py` | 0 | Package init |
| `tools/leads/lead_db.py` | ~250 | SQLite CRUD for museums, contacts, interactions, research |
| `tools/leads/pipeline.py` | ~150 | Stage queries, stale detection, pipeline summary |
| `leads/hubspot_export.csv` | ~31 rows | HubSpot demo leads (Hermann provides) |
| `leads/mailerlite_export.csv` | ~43 rows | MailerLite subscribers (Hermann provides) |

#### What Changes and Why

**`tools/leads/lead_db.py`:**
- Creates `data/leads.db` with schema from ARCHITECTURE.md Section C1
- CRUD: add_museum(), add_contact(), add_interaction(), get_museum(), update_stage()
- Import: import_csv(filepath, source) — reads CSV, creates museum + contact records
- FTS5 search on contacts and interactions

**`tools/leads/pipeline.py`:**
- pipeline_summary() — counts per stage, total museums, active sequences
- stale_contacts(days=5) — museums where last interaction is >N days ago
- next_actions() — suggests what to do next based on stage and timing
- pipeline_table() — formatted table output via `rich`

#### Changes to Existing Files

**`run.py`** — Add commands:
- `pipeline` — show pipeline overview
- `pipeline --stage N` — filter by stage
- `add-lead` — interactive prompt to add museum/contact
- `update-lead <museum_name> --stage N` — move museum to new stage
- `log-email <museum_name>` — mark draft as sent, advance to Stage 3
- `import-leads <csv> --source hubspot|mailerlite` — bulk import
- `status` — quick briefing (pipeline stats + stale contacts + next actions)

**`tools/chat/session.py`** — Inject pipeline summary into every session context:
- "Pipeline: 31 museums total. Stage 0: 25, Stage 1: 3, Stage 2: 2, Stage 3: 1. Stale: Joanneum (8 days)"

#### Safety Invariants
- lead_db schema creation must be idempotent
- CSV import must handle duplicates gracefully (skip if email already exists)
- Stage can only advance forward (0→1→2→...), never backward without explicit override
- All stage transitions are logged in interactions table

#### How to Verify Phase 4

```bash
# 1. Import HubSpot leads
python run.py import-leads leads/hubspot_export.csv --source hubspot
# Expected: "Imported 31 contacts from HubSpot"

# 2. View pipeline
python run.py pipeline
# Expected: Formatted table with all 31 contacts at Stage 0

# 3. Update a lead
python run.py update-lead "SS Great Britain" --stage 2
# Expected: "SS Great Britain moved to Stage 2 (Personalized)"

# 4. Check status
python run.py status
# Expected: Summary with counts, stale contacts, next suggested actions

# 5. Test pipeline in chat
python run.py chat
# Type: "What's the pipeline status?"
# Expected: Touri describes the pipeline state from injected context
```

---

## PHASE 5: Learning & Adaptation (Week 2+, Deferred)

Deferred until real response data exists (need 10+ sent emails). See ARCHITECTURE.md Section G, Phase 5.

---

## Phase 3 & 4 Agent Execution Templates

The following templates should be used by future agents executing Phases 3 and 4 of the implementation.

---

### TEMPLATE: Phase 3 Implementation (Email Drafting Engine)

```
PHASE 3 — IMPLEMENT:

GOAL: Implement Phase 3 (Email Drafting Engine) of the TouriBot build plan at
/Users/hermannkudlich/Documents/ClaudeProjects/AITourPilot-Touribot/docs_dev/20260407_TOURIBOT_BUILD_PLAN.md

READ FIRST (required context):
1. ARCHITECTURE.md (project root) — full component design, data model, soul.md template
2. docs_dev/20260407_TOURIBOT_BUILD_PLAN.md — this plan, Phase 3 section
3. soul.md (project root) — Touri's identity and email drafting principles
4. hardprompts/email_templates.md — the 3-step outreach sequence templates
5. tools/memory/memory_db.py — understand how to search memory for museum context

This is a production codebase beyond MVP. Sloppy changes break working systems.
Quality and system integrity are non-negotiable.

Create an agent team:

1. **Implementer A** — Owns: tools/outreach/personalizer.py, tools/outreach/drafter.py
   - personalizer.py: build per-museum context package from memory + knowledge + lead DB
   - drafter.py: call Claude with focused prompt, stream response, save to output/emails/

2. **Implementer B** — Owns: tools/outreach/scorer.py, run.py updates
   - scorer.py: classify inbound replies 1-5 with explanation
   - run.py: add draft, log-response commands
   - tools/chat/session.py: update context assembly for drafting mode

3. **Architect Overseer** — Does NOT write code. Reviews every file for:
   - Correct integration with memory system (search patterns, memory tagging)
   - Correct context assembly (soul.md principles enforced in prompts)
   - No hardcoded museum facts (must come from memory/knowledge, never from the code)
   - Output saved before display (never lose a draft)
   - Error handling at API boundaries

SAFETY INVARIANTS:
- Every draft saved to output/emails/ before displaying
- Drafter must not hallucinate museum facts
- Scorer returns score + explanation, never bare number
- No auto-sending of emails
- Memory extraction after every drafting session
- tools/memory/ files MUST NOT be modified in this phase

VERIFICATION: Run all tests from Phase 3 "How to Verify" section in the build plan.
```

---

### TEMPLATE: Phase 4 Implementation (Pipeline Tracking)

```
PHASE 4 — IMPLEMENT:

GOAL: Implement Phase 4 (Pipeline Tracking) of the TouriBot build plan at
/Users/hermannkudlich/Documents/ClaudeProjects/AITourPilot-Touribot/docs_dev/20260407_TOURIBOT_BUILD_PLAN.md

READ FIRST (required context):
1. ARCHITECTURE.md (project root) — Section C1 for exact SQL schema
2. docs_dev/20260407_TOURIBOT_BUILD_PLAN.md — this plan, Phase 4 section
3. tools/leads/ — does not exist yet, create from scratch
4. Existing run.py — understand current command structure

Create an agent team:

1. **Implementer A** — Owns: tools/leads/lead_db.py
   - Create data/leads.db with schema from ARCHITECTURE.md Section C1
   - CRUD functions: add_museum, add_contact, add_interaction, update_stage
   - CSV import: import_csv(filepath, source) with duplicate handling
   - FTS5 virtual tables on contacts and interactions

2. **Implementer B** — Owns: tools/leads/pipeline.py, run.py updates
   - pipeline_summary(), stale_contacts(), next_actions(), pipeline_table()
   - run.py: add pipeline, add-lead, update-lead, log-email, import-leads, status commands
   - tools/chat/session.py: inject pipeline summary into session context

3. **Architect Overseer** — Reviews for:
   - Schema matches ARCHITECTURE.md exactly (museums → contacts → interactions → research)
   - Stage transitions logged in interactions table
   - CSV import handles edge cases (missing fields, duplicates, encoding)
   - Pipeline summary injected into chat context doesn't exceed token budget
   - Stale detection uses correct timezone (UTC)

SAFETY INVARIANTS:
- Schema creation is idempotent (CREATE TABLE IF NOT EXISTS)
- CSV import skips duplicates (by email)
- Stage only advances forward without explicit override
- All stage transitions logged
- Pipeline commands work with 0 leads (empty state handling)
- tools/memory/ and tools/outreach/ MUST NOT be modified in this phase

VERIFICATION: Run all tests from Phase 4 "How to Verify" section in the build plan.
```

---

### TEMPLATE: Validation (After Each Phase)

```
PHASE — VALIDATE:

GOAL: Validate Phase [N] implementation of TouriBot. This is the final quality gate.

READ: docs_dev/20260407_TOURIBOT_BUILD_PLAN.md — Phase [N] "How to Verify" section

Create an agent team of 2-3:

1. **Architect Validator** — Full system integrity review:
   - Trace execution through the entire modified flow end-to-end
   - For every modified file: verify consistency with callers and callees
   - Check: broken imports, missing error handling, functions with changed signatures
   - Verify downstream consumers still work
   - Check edge cases: empty database, missing .env, no knowledge files loaded
   - Run ALL verification commands from the build plan

2. **Code Quality Reviewer** — Line-by-line review:
   - Look for bugs, null risks, unhandled exceptions
   - Verify error handling is adequate (not excessive)
   - No debug code or temporary hacks left in
   - Naming consistency with existing codebase patterns
   - No SQL injection risks (use parameterized queries)
   - No secrets in code (API keys from .env only)

3. **Regression Checker**:
   - Verify files listed as "MUST NOT be modified" were not touched
   - Run `python run.py chat` and confirm previous phases still work
   - Check that memory from previous sessions is still accessible
   - Verify .gitignore covers data/, .env, __pycache__, output/

DELIVERABLE: Each validator produces ✅ PASS or ❌ FAIL with file:line references.
If ANY fails, fix and re-validate.
```

---

## Downstream Impact Analysis

| Component | Affected by Phase 1 | Phase 2 | Phase 3 | Phase 4 |
|-----------|---------------------|---------|---------|---------|
| soul.md | Created | Read | Read | Read |
| memory/MEMORY.md | Created | Read/write | Read/write | Read |
| tools/memory/* | Created | No change | Read only | Read only |
| tools/chat/session.py | Created | Modified (knowledge loading) | Modified (drafting context) | Modified (pipeline injection) |
| run.py | Created | Modified (ingest cmd) | Modified (draft cmds) | Modified (pipeline cmds) |
| tools/knowledge/ingest.py | — | Created | Read only | No change |
| tools/outreach/* | — | — | Created | Read only |
| tools/leads/* | — | — | — | Created |
| data/memory.db | Created | Read/write | Read/write | Read/write |
| data/leads.db | — | — | — | Created |

## Risk Areas

### #1: Memory system extraction from HenryBot
The memory_db.py file (1,142 lines) has path dependencies and may import HenryBot-specific utilities. **Mitigation:** Read the full import section of every extracted file. Replace any `from tools.xxx import yyy` that references HenryBot-specific modules with local equivalents or remove.

### #2: Context window management
Loading soul.md + MEMORY.md + knowledge files + pipeline summary + conversation history could exceed Claude's context limit. **Mitigation:** Measure total token count of assembled context before API call. Implement progressive context reduction: drop P2 knowledge first, then P1, then older conversation history.

## Rollback Approach

Each phase produces independent files. If a phase fails:
- Phase 1: Delete tools/memory/, tools/chat/, run.py, soul.md, args/. Start over.
- Phase 2: Delete tools/knowledge/, knowledge/processed/, hardprompts/. Revert session.py changes.
- Phase 3: Delete tools/outreach/, output/emails/. Revert run.py and session.py changes.
- Phase 4: Delete tools/leads/, data/leads.db. Revert run.py and session.py changes.

Git commit after each phase provides clean rollback points.

## Files NOT to Touch

These files should never be modified after their initial creation in the specified phase:

| File | Created in | Never modify after |
|------|-----------|-------------------|
| `soul.md` | Phase 1 | Phase 1 (unless Hermann explicitly requests changes) |
| `memory/USER.md` | Phase 1 | Ever (sacred, human-only) |
| `tools/memory/memory_db.py` | Phase 1 | Phase 1 (HenryBot's proven code) |
| `.env` | Phase 1 | Phase 1 (secrets only) |
| `ARCHITECTURE.md` | Pre-build | Never (reference document) |

---

*This plan is the complete blueprint for building TouriBot. Each phase is independently verifiable. The total build is ~24 hours across 5 days. Campaign begins on Day 5 with the first real email to Georgie Power at SS Great Britain.*

*Created: 2026-04-07*
