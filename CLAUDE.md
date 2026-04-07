# TouriBot — Project Handbook

## What This Is

TouriBot is an AI-powered museum outreach assistant for AITourPilot. It helps Hermann draft personalized emails, track a pipeline of museum leads, and learn from every interaction.

## Key Files

- `soul.md` — Touri's identity and email drafting principles (DO NOT auto-edit)
- `memory/USER.md` — Hermann's identity (NEVER auto-edit)
- `memory/MEMORY.md` — Working memory (auto-promoted facts)
- `ARCHITECTURE.md` — Full component design and data model
- `docs_dev/20260407_TOURIBOT_BUILD_PLAN.md` — Phased build plan
- `args/settings.yaml` — All configuration

## Running

```bash
python run.py chat                    # Interactive chat with Touri
python run.py recall "<query>"        # Search memory
python run.py remember "<fact>"       # Save a fact
```

## Architecture

- **Memory**: `tools/memory/` — SQLite + FTS5 + vector search (from HenryBot)
- **Chat**: `tools/chat/session.py` — Context assembly, Anthropic API, memory extraction
- **Data**: `data/memory.db` — All persistent memory
- **Output**: `output/emails/` — Saved email drafts

## Constraints

- Python 3.12 (Miniforge comfyenv)
- Anthropic SDK for LLM calls (not Agent SDK)
- SQLite for all persistence
- Emails always sent manually from hermann@aitourpilot.com (Zoho, .com domain)
- Never exceed 3 emails/day from .com domain

## Safety

- `.env` contains secrets — NEVER commit
- `memory/USER.md` is sacred — NEVER auto-modify
- `soul.md` is locked after Phase 1 — only Hermann edits
- All email drafts saved to `output/emails/` before display
