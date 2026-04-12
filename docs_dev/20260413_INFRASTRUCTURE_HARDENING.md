# Infrastructure Hardening Plan — TouriBot Gap Audit

**Date:** 2026-04-13
**Scope:** Address all gaps identified in the infrastructure audit (3 Critical, 6 High, 4 Medium, 1 Low)

---

## Executive Summary

| Severity | Count | Examples |
|----------|-------|---------|
| Critical | 3 | launchd plist broken, Gemini key missing in production, synthesizer crashes on large content |
| High | 6 | No budget enforcement, no per-page checkpoint, daemon thread for research, no Gemini retry, max_tokens hardcoded, no cost logging |
| Medium | 4 | No research status polling, no error reporting, context budget unbounded, memory truncation absent |
| Low | 1 | Production mode dashboard differences undocumented |

Phases H1–H3 are blocking production stability. H4–H6 prevent cost blowouts and silent failures. H7 is polish for operator confidence.

---

## Phase H1: Quick Wins (P0)

**Goal:** Eliminate crashes and misconfiguration that block any production use.

**Gaps addressed:** Critical ×3

| Fix | File(s) |
|-----|---------|
| Repair launchd plist — correct Python path, working directory, env vars | `deploy/com.aitourpilot.touribot.plist` |
| Add `GEMINI_API_KEY` to `.env` and validate on startup | `.env`, `tools/research/gateway.py` |
| Add `max_tokens` guard to synthesizer — raise before Anthropic rejects | `tools/research/synthesizer.py` |
| Validate required API keys at import time with clear error messages | `tools/research/gateway.py`, `run.py` |

**Verification:**
- `launchctl load` succeeds without error; `launchctl list | grep touribot` shows PID
- Startup with missing key prints actionable message and exits cleanly (exit code 1)
- Synthesizer with 200k-token input does not raise `InvalidRequestError`; truncates with warning

**Effort:** 2–3 hours

---

## Phase H2: Budget Enforcement

**Goal:** Cap per-research-run API spend before it hits the wire.

**Gaps addressed:** High — no spend ceiling

**Approach:** Port `ResearchBudget` from FelixBot. Track cumulative token usage and USD cost across all gateway calls in a single research session. Abort with a structured `BudgetExceededError` when the ceiling is reached.

| Task | File(s) |
|------|---------|
| Port `ResearchBudget` class (token counter + USD ceiling) | `tools/research/budget.py` (new) |
| Inject budget into `ResearchSession`; wrap every gateway call | `tools/research/session.py`, `tools/research/gateway.py` |
| Expose ceiling in `settings.yaml` (`research.budget_usd_max`) | `args/settings.yaml` |
| Surface budget consumed in research result object | `tools/research/models.py` |

**Verification:**
- Set ceiling to $0.01; confirm research aborts mid-run with `BudgetExceededError`
- Normal run logs total cost at completion
- `settings.yaml` ceiling respected without code change

**Effort:** 3–4 hours

---

## Phase H3: Crash Safety

**Goal:** Survive process interruption during multi-page deep reads; resume without re-fetching.

**Gaps addressed:** High — deep_reading has no checkpoint

**Approach:** After each page is fetched and parsed, write a checkpoint file (`output/research/.checkpoints/<run_id>/page_<n>.json`). On resume, skip pages already present. Checkpoint cleared on clean completion.

| Task | File(s) |
|------|---------|
| Add `CheckpointManager` (write/read/clear per run_id) | `tools/research/checkpoint.py` (new) |
| Integrate into `deep_reading` page loop | `tools/research/deep_reading.py` |
| Add `run_id` to research invocation (uuid4) | `tools/research/session.py` |
| Prune stale checkpoints older than 7 days at startup | `run.py` |

**Verification:**
- Kill process mid-crawl (`kill -9`); rerun same query; observe pages skipped in log
- Completed run leaves no checkpoint directory
- Stale checkpoint from 8 days ago removed on next startup

**Effort:** 3–4 hours

---

## Phase H4: Subprocess Isolation

**Goal:** Run research in an isolated process so a crash or timeout cannot kill the chat session.

**Gaps addressed:** High — daemon thread provides no isolation or timeout

**Approach:** Port `research_runner.py` from FelixBot. Spawn research as a subprocess (`multiprocessing` or `subprocess`). Result written to a temp file; parent reads on completion. Replace the current daemon thread entirely.

| Task | File(s) |
|------|---------|
| Port `research_runner.py` entry point | `tools/research/research_runner.py` (new) |
| Replace daemon thread in chat session with subprocess call | `tools/chat/session.py` |
| Pass timeout from `settings.yaml` (`research.timeout_seconds`) | `args/settings.yaml`, `tools/research/research_runner.py` |
| Handle subprocess timeout — kill child, surface timeout error to user | `tools/chat/session.py` |

**Verification:**
- Simulate infinite loop in synthesizer; confirm parent chat session recovers after timeout
- Normal research completes and result returned to chat
- `settings.yaml` timeout respected

**Effort:** 4–5 hours

---

## Phase H5: Progress Visibility

**Goal:** Users see research progress in real time rather than waiting silently.

**Gaps addressed:** Medium — no polling, no notifications

**Approach:** Research runner writes incremental status to a shared status file (`output/research/.status/<run_id>.json`). Chat session polls this file and streams stage updates to the terminal.

| Task | File(s) |
|------|---------|
| Define status schema (stage, pages_done, pages_total, elapsed_s, last_error) | `tools/research/models.py` |
| Write status file at each stage transition in runner | `tools/research/research_runner.py` |
| Poll status file in chat session; print progress line | `tools/chat/session.py` |
| Add `--quiet` flag to suppress progress for scripted use | `run.py` |

**Verification:**
- `python run.py chat` shows stage names and page counts during a live research run
- `--quiet` flag produces no intermediate output
- Status file present during run; absent after clean completion

**Effort:** 2–3 hours

---

## Phase H6: Gateway Hardening

**Goal:** Make all external API calls robust against transient failures and cost surprises.

**Gaps addressed:** High ×3 — no Gemini retry, max_tokens hardcoded, no cost logging

| Fix | File(s) |
|-----|---------|
| Add exponential backoff retry (3 attempts, 2× delay) for Gemini calls | `tools/research/gateway.py` |
| Read `max_tokens` for all LLM calls from `settings.yaml` | `args/settings.yaml`, `tools/research/gateway.py`, `tools/research/synthesizer.py` |
| Log cost per call (model, input_tokens, output_tokens, usd_est) to SQLite `api_calls` table | `data/memory.db`, `tools/research/gateway.py` |
| Expose `GET /research/cost?since=<date>` query in CLI (`python run.py cost`) | `run.py` |

**Verification:**
- Mock Gemini to return 429 twice; confirm third attempt succeeds and is logged
- Change `settings.yaml` max_tokens; confirm new value used without code change
- After any research run, `python run.py cost` returns non-zero totals

**Effort:** 3–4 hours

---

## Phase H7: Polish

**Goal:** Operator confidence — good errors, complete observability, no unbounded memory use.

**Gaps addressed:** Medium ×4, Low ×1

| Fix | File(s) |
|-----|---------|
| Structured error reporting — all unhandled exceptions logged to `output/errors/YYYYMMDD_<run_id>.json` | `run.py`, `tools/chat/session.py` |
| Document production vs. dev mode dashboard differences in `ARCHITECTURE.md` | `ARCHITECTURE.md` |
| Enforce context budget ceiling — truncate oldest messages when chat history exceeds `settings.yaml` `chat.context_tokens_max` | `tools/chat/session.py` |
| Memory truncation — cap memory injection to top-N results; log when truncation occurs | `tools/memory/retrieval.py` |

**Verification:**
- Force an unhandled exception; confirm JSON error file written with traceback and run_id
- Chat history with 200 exchanges does not exceed configured token ceiling
- Memory retrieval with 500 candidates returns only top-N (configurable)

**Effort:** 3–4 hours

---

## Sequencing & Dependencies

```
H1 (P0, unblocks everything)
  └─> H2 + H3 (can run in parallel)
        └─> H4 (subprocess wraps session; needs budget + checkpoint ready)
              └─> H5 (status file inside runner)
H6 (independent; start after H1)
H7 (independent; can be done any time after H1)
```

**Total estimated effort:** 20–27 hours across 2–3 work sessions.

---

## Acceptance Criteria (done when)

- [ ] `launchctl start com.aitourpilot.touribot` starts and stays running
- [ ] Missing API key exits cleanly with actionable message
- [ ] A 200k-token research result synthesizes without API error
- [ ] Research budget ceiling aborts the run before exceeding configured USD cap
- [ ] Killing the process mid-crawl and rerunning skips already-fetched pages
- [ ] Chat session survives a research subprocess crash or timeout
- [ ] Progress lines appear in terminal during research
- [ ] All LLM `max_tokens` values are driven by `settings.yaml`
- [ ] `python run.py cost` reports accurate totals
- [ ] Error JSON written for every unhandled exception
