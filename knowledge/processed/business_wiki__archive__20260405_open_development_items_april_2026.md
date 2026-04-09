# 20260405-open-development-items-april-2026

*Source: Business Wiki / development/Archive/20260405-open-development-items-april-2026.html*

## Executive Summary

Multi-agent research team (3 Sonnet agents) investigated all open development items as of April 2026. **All 6 items are now CLOSED** (April 8, 2026).

| # | Item | Priority | Status | Completed |
|---|------|----------|--------|-----------|
| 1 | Agent Amnesia | HIGH | **DONE** — visitor memory + conversation lifecycle fixes deployed | Apr 8 |
| 2 | Phase 5b Language | LOW | **DONE** — FR/IT i18n added, docs updated | Apr 8 |
| 3 | Liquid Glass | MEDIUM | **DONE** — visual review passed, no opt-out needed | Apr 8 |
| 4 | KB Visibility Backfill | MEDIUM | **DONE** — 36 agents fixed in prod | Apr 8 |
| 5 | Creator Backfill | LOW | **DONE** — 746/1102 artifacts updated (rest self-heal on re-run) | Apr 8 |
| 6 | Orb Animation | -- | **DONE** | Mar 2026 |

---

## 1. Agent Amnesia — Conversation Context Lost on Start/Stop

**Priority:** HIGH | **Status: DONE** (Apr 8, 2026)

### What Was Done

**Visitor Memory system implemented end-to-end:**
- `summarize-visit` public API endpoint — receives transcript, returns structured visit summary via LLM
- `RETURNING_VISITOR_BLOCK` injected into all agent system prompts — instructs Henry how to use prior visit context
- `{{prior_conversation_summary}}` dynamic variable — replaced at conversation start with stored summary
- VisitorMemoryService on mobile — stores/retrieves summaries per museum+language in AsyncStorage
- Memory invalidation via `rerunCount` — stale memories auto-discarded after museum re-run
- Backfill script run against all 28 production agents

**Conversation lifecycle fixes (also Apr 8):**
- EOS message (`ws.send("")`) sent before WebSocket close — commits pending transcript
- AppState listener stops conversation on app background (home button, lock screen, app switch)
- Logout cleanup — stops active conversation before Firebase sign-out
- Error state cleanup — clears stale state after final reconnect failure

---

## 2. Phase 5b — App Language Integration

**Priority:** LOW | **Status: DONE** (Apr 8, 2026)

Implementation was already complete (Mar 9). Remaining doc/cosmetic items closed Apr 8:

- FR/IT added to `getLanguageFullName()` in AppContext.tsx
- FR/IT i18n keys added to all 3 locale files (en, de, es)
- EXECUTIVE_SUMMARY.md updated — Phase 5b moved to Completed table
- Dev spec status updated to "COMPLETE"

---

## 3. Liquid Glass — iOS 26 UI Evaluation

**Priority:** MEDIUM | **Status: DONE** (Apr 8, 2026)

- Xcode 26.3 migration complete (Apr 4). TestFlight build 6 uploaded.
- Visual review on iOS 26 simulator: **looks great, no issues found.**
- UIDesignRequiresCompatibility opt-out NOT needed — Liquid Glass works well with AITourPilot's custom UI.
- No further action required.

---

## 4. KB Visibility Backfill

**Priority:** MEDIUM | **Status: DONE** (Apr 8, 2026)

- Backfill script run against production: **36 agents fixed**
- Fixed: missing RAG indexes, incorrect usage_mode on content docs
- All agents now have correct `auto` (RAG) vs `prompt` (operational) KB doc settings
- Re-runs will regenerate fresh KB docs with correct settings via `kb-strategy.ts`

---

## 5. Creator Attribution Backfill

**Priority:** LOW | **Status: DONE** (Apr 8, 2026)

- Backfill script run against production: **746 of 1102 artifacts updated** (70% coverage)
- 356 artifacts have no extractable creator in their descriptions — these self-heal on museum re-run (pipeline extracts at Intake + refines in Deep Research Pass 1b)
- Cost: ~$0.02 (GPT-5-mini)

---

## 6. Orb Animation Freeze Fix

**Status:** COMPLETED (March 2026)

All 3 phases implemented: per-chunk feature extraction, procedural modulation (multi-sine noise x audio level), numeric tuning. The orb now pulses continuously during sustained speech.

---

## Full Research Document

Detailed findings with code references, line numbers, and trade-off analysis: docs_dev/20260405_OPEN_DEVELOPMENT_ITEMS.md in the AITourPilot4 repository.
