# 20260406-bug-report-issues-found-during-henry-v3-implementation-april-2026

*Source: Business Wiki / development/Archive/20260406-bug-report-issues-found-during-henry-v3-implementation-april-2026.html*

## Overview

Bugs, malfunctions, and technical debt items identified during the Henry V3 Adaptive Personality implementation (April 2026). **All 16 items are now resolved** (14 fixed, 2 intentionally left as-is). Each item includes severity, status, root cause, and resolution.

---

## Critical: Pipeline Intake JSON Parse Failures

**Severity:** Critical (blocks pipeline runs)
**Status:** FIXED (2026-04-06)
**Found during:** Phase 3 Belvedere run

**Symptom:** INTAKE stage fails with `Failed to parse JSON from LLM output: Expected ',' or ']' after array element in JSON at position 21420`. The LLM produces a malformed JSON research plan. Pipeline status goes to FAILED with 0 artifacts. Additionally, `maxTokens` formula was too low for 100+ artifact plans (yielded 10,000 tokens for 100 pieces, actual output needs ~10,500), causing Claude to truncate mid-JSON.

**Root cause:** Two compounding issues: (1) `parseJsonFromLlm` had no repair logic for truncated or malformed JSON, (2) `maxTokens` formula in intake capped too low for large research plans.

**Fixes applied (4 changes):**
1. `src/lib/parse-json.ts`: Added 5-strategy progressive JSON repair -- trailing comma removal, stack-based truncation repair (`closeTruncatedJson`), combined strategies. Validated with 23 unit tests.
2. `src/pipeline/stages/00-intake.ts`: maxTokens formula changed from `targetPieceCount * 80 + 2000` (cap 16K) to `targetPieceCount * 120 + 3000` (cap 32K). Gives 15,000 tokens for 100 pieces (50% margin).
3. `src/pipeline/stages/00-intake.ts`: Zod schema defaults added for `people`, `exhibitions`, `estimatedScope` -- graceful degradation if LLM omits optional fields.
4. `src/integrations/llm/anthropic.ts` + `router.ts` + `00-intake.ts`: `stopReason` now surfaced and logged when LLM hits max_tokens limit.

**Verified:** Belvedere Standard run (101 artifacts) passed INTAKE successfully after fixes.

---

## High: Wiki Server Subfolder Articles Placed Outside Folders

**Severity:** High (every subfolder article needs manual fix)
**Status: FIXED** — server.py now handles subfolder insertion, href paths, and folder counts correctly
**Found during:** Phase 1 and Phase 2 wiki publishing

**Symptom:** When creating articles via `POST /api/create-article` with a `subfolder` parameter (e.g., `content-pipeline-v3-henry`), the server correctly places the HTML file in the subfolder on disk, but:
- In `prompts.html`: the card is added as a standalone above the folder section, not inside the folder's `<div class="folder-body">`
- In `index.html`: the teaser is added outside the `<div class="teaser-folder-items">`, often injected inside the wrong folder's body
- The `href` paths point to `prompts/filename.html` instead of `prompts/subfolder/filename.html`
- Folder counts are not updated

**Root cause:** `_add_card_to_category_page()` and `_add_teaser_to_index()` in `server.py` don't understand the folder structure for prompts subfolders. They insert at the generic "BEGIN DOCUMENT CARDS" sentinel without checking if the article belongs inside a specific folder.

**Impact:** Required manual fixing for all 7 V3 prompt articles (Phase 1 + Phase 2). Every future subfolder article will need the same manual fix.

**Suggested fix:**
1. `_add_card_to_category_page()`: When `subfolder` is provided, find the matching folder `<div>` by ID (e.g., `id="folder-v3"`) and insert inside its `<div class="folder-body">`. Update the folder count.
2. `_add_teaser_to_index()`: When `subfolder` is provided, find the matching `<div class="teaser-folder-items">` and insert inside it. Update the folder count.
3. If the folder doesn't exist yet, create it (with chevron, icon, title, count, body div).
4. Fix the href to include the subfolder path.

**Files:** `/Users/hermannkudlich/Desktop/AITourPilot Project/BUSINESS_CONTENT/wiki/server.py` (functions `_add_card_to_category_page`, `_add_teaser_to_index`)

---

## High: Wiki Template Diagram Code Not Fully Stripped

**Severity:** High (causes blank pages)
**Status:** Fixed (server.py patched)
**Found during:** Initial wiki article creation

**Symptom:** Newly created articles render as blank pages. The hero/sidebar appears but the article body is empty.

**Root cause:** The demo template (`technical/demo-content-pipeline-overview.html`) contains diagram-specific JavaScript: event handlers referencing `diagramClose` and `diagramFullscreen` DOM elements. The server's `_generate_article_html()` stripped the diagram functions and overlay div, but left the event handler block. `getElementById('diagramClose')` returns null, `.addEventListener()` throws, and the script halts before `renderContent()` executes.

**Fix applied:** Added regex to strip the fullscreen close handler block in `server.py`. Also manually fixed 3 affected articles.

**Files:** `server.py` (diagram cleanup section in `_generate_article_html`)

---

## High: Wiki Template Content Injection Regex Mismatch

**Severity:** High (articles created with demo content instead of actual content)
**Status:** Fixed (server.py patched)
**Found during:** Initial wiki article creation

**Symptom:** Server returns `{"ok": true}` but the article contains the demo template's "Content Pipeline Architecture Overview" instead of the submitted content.

**Root cause:** The content-replacement regex expected `window.__MD_EN` immediately after `<script>`, but the template has `window.__META = {...};` between them. The regex silently failed to match, leaving the demo content intact.

**Fix applied:** Updated regex to optionally match the `__META` block before `__MD_EN`.

**Files:** `server.py` (content replacement regex in `_generate_article_html`)

---

## Medium: Wiki Double-Escaped Backticks in Template Literals

**Severity:** Medium (causes blank pages or broken rendering)
**Status:** Fixed (server.py patched + 24 files repaired)
**Found during:** Wiki content audit

**Symptom:** Articles render blank or with garbled content. In the HTML source, backticks inside `window.__MD_EN` appear as double-backslash followed by backtick instead of single-backslash followed by backtick.

**Root cause:** Agents pre-escaped markdown before passing to the server API. The server's `_escape_for_template_literal()` then escaped again, producing double-escaping. JavaScript interprets double-backslash + backtick as literal backslash + closing delimiter, prematurely terminating the template literal.

**Fix applied:** Made `_escape_for_template_literal()` idempotent -- it undoes pre-escaping before re-escaping. Also bulk-repaired 24 existing articles.

**Files:** `server.py` (`_escape_for_template_literal` function)

---

## Medium: rewrite.ts Contains Dead Code

**Severity:** Medium (technical debt, causes confusion)
**Status: FIXED** (Apr 8, 2026) — file deleted
**Found during:** Phase 2 research (confirmed independently by 2 agents)

**Symptom:** `src/lib/prompts/rewrite.ts` exports `CONTENT_GENERATION_PROMPT` and `VOICE_OPTIMIZATION_PROMPT`, but neither is imported by any file in the codebase.

**Root cause:** These were part of an earlier LLM-based voice rewrite pass that was replaced by deterministic string transforms in `optimizeForVoice()` within `04-content-write.ts`. The file was never cleaned up.

**Resolution:** File deleted. Zero imports confirmed across the entire codebase. Was causing confusion during research phases — agents wasted time analyzing 57 lines of dead code.

---

## Medium: Supabase Session Pooler Connection Failures from Local

**Severity:** Medium (blocks local DB queries)
**Status: LEAVE** — infrastructure limitation, not a code bug
**Found during:** Phase 3 pipeline monitoring

**Symptom:** `psql $DATABASE_URL` fails with `server closed the connection unexpectedly` when connecting from a local machine to the Supabase session pooler (`aws-1-eu-west-1.pooler.supabase.com:5432`).

**Root cause:** Supabase session pooler connection limits or timeouts. The pooler may reject connections from IPs outside the expected Vercel/Render ranges, or the connection pool is saturated during pipeline runs.

**Workaround:** Use the Vercel API with Firebase auth instead of direct DB queries (see CLAUDE.md "Dashboard API Authentication" section). The direct URL (`db.xxx.supabase.co`) works but is IPv6-only and may fail on some networks.

**Why LEAVE:** This is a Supabase infrastructure limitation, not a codebase bug. The workaround is documented in CLAUDE.md. An `/api/admin/query` endpoint would be nice-to-have but isn't blocking any workflow.

---

## Medium: IpRegistry Discoveries Were Not Fed to Content Write

**Severity:** Medium (content quality gap)
**Status:** Fixed (Phase 2 implementation)
**Found during:** Phase 2 research (confirmed by all 3 agents)

**Symptom:** Stage 02's Discovery Engine produces hidden connections, emotional narratives, and cross-museum synthesis, stored in the `IpRegistry` table. But Stage 04 (content-write) never queried this table. Discovery content only reached agents through Stage 06's separate "Deep Stories" KB document, not woven into per-artifact narratives.

**Root cause:** Stage 04 was written before the Discovery Engine was fully integrated. The `rewrite.ts` dead code actually had a `{{discoveriesJson}}` slot for this purpose, but since `rewrite.ts` was never connected, the data path was broken.

**Fix applied:** Phase 2 added IpRegistry queries to `04-content-write.ts` with try/catch fallback. Discoveries are now injected into artifact prompts for Wonder Moment and Connection Thread layers.

**Files:** `src/pipeline/stages/04-content-write.ts`

---

## Low: Wiki Escaped Closing Backtick in Template Literals

**Severity:** Low (causes blank pages, but was caught and bulk-fixed)
**Status:** Fixed (24 files repaired)
**Found during:** Wiki content audit

**Symptom:** The closing backtick-semicolon of `window.__MD_EN` template literals was escaped (backslash-backtick + semicolon) instead of raw (backtick + semicolon). JavaScript treats the escaped backtick as content, not as the closing delimiter, so the template literal runs past its intended end into the rendering JavaScript, causing a syntax error.

**Root cause:** The server's escaping function escaped ALL backticks including the closing one. The closing backtick must be raw.

**Fix applied:** Server patching + bulk repair of 24 articles. The `_escape_for_template_literal()` idempotency fix prevents recurrence.

---

## Low: ElevenLabs TTS Parameters Not Explicitly Set

**Severity:** Low (cosmetic/quality)
**Status: FIXED** — `stability: 0.35`, `similarity_boost: 0.65` now in `agent-defaults.ts`, applied in Stage 07
**Found during:** Phase 1 ElevenLabs constraints research

**Symptom:** The pipeline deployed agents without explicitly setting `stability` and `similarity_boost` TTS parameters. The proven MVP reference agents used `stability: 0.35` and `similarity_boost: 0.65`, but production agents were using API defaults (`0.5` / `0.8`).

**Resolution:** TTS parameters added to `src/lib/constants/agent-defaults.ts` and applied during Stage 07 deploy. All future deploys and re-runs use the proven MVP values.

**Files:** `src/lib/constants/agent-defaults.ts`, `src/pipeline/stages/07-elevenlabs-deploy.ts`

---

## Low: Stage 06 Quick Guide 500-Char Blind Truncation (Pre-V3)

**Severity:** Low (only affects pre-V3 content as fallback)
**Status: LEAVE** — pre-V3 fallback becomes dead code after museum re-runs
**Found during:** Phase 2 research

**Symptom:** For pre-V3 content (no markdown headers), `buildQuickGuide()` in Stage 06 blindly truncates artifact descriptions to 500 characters, potentially cutting mid-sentence.

**Fix applied:** Phase 2 added `extractQuickLayers()` that extracts `## Hook` and `## Quick ID` layers for V3 content. Pre-V3 content still uses the 500-char fallback.

**Why LEAVE:** All 28 museums are about to be re-run through the V3 pipeline. After re-runs, every artifact has V3-format content with markdown headers, so the pre-V3 fallback path is never hit. The code is harmless and self-resolves.

**Files:** `src/pipeline/stages/06-data-structure.ts`

---

## Summary Table

| # | Issue | Severity | Status | Category |
|---|-------|----------|--------|----------|
| 1 | Intake JSON parse failures | Critical | **FIXED** (2026-04-06) | Pipeline |
| 2 | Wiki subfolder article placement | High | **FIXED** — server.py handles subfolder insertion, href paths, counts | Wiki server |
| 3 | Wiki diagram code not stripped | High | Fixed | Wiki server |
| 4 | Wiki content injection regex | High | Fixed | Wiki server |
| 5 | Wiki double-escaped backticks | Medium | Fixed | Wiki server |
| 6 | rewrite.ts dead code | Medium | **FIXED** — file deleted (Apr 8) | Tech debt |
| 7 | Supabase local connection failures | Medium | **LEAVE** — infrastructure limitation, workaround documented | Infrastructure |
| 8 | IpRegistry not fed to Stage 04 | Medium | Fixed | Pipeline |
| 9 | Wiki escaped closing backtick | Low | Fixed | Wiki server |
| 10 | ElevenLabs TTS params not explicit | Low | **FIXED** — stability: 0.35, similarity_boost: 0.65 in agent-defaults.ts | Pipeline |
| 11 | Stage 06 blind truncation fallback | Low | **LEAVE** — pre-V3 fallback irrelevant after museum re-runs | Pipeline |
| 12 | Manual translation stale-job guard bypass | Critical | **FIXED** (2026-04-07) | Pipeline |
| 13 | singleLanguage not passed to handler | Critical | **FIXED** (2026-04-07) | Pipeline |
| 14 | Disconnected UI messaging on translation failures | High | **FIXED** — warning icons, per-language logs, health check cross-ref (commit 295513e) | UI |
| 15 | Sequential translation too slow for Standard V3 | Medium | **FIXED** — docs now translate in parallel via Promise.all() | Pipeline |
| 16 | Operational data parse crash rolls back KB docs | Critical | **FIXED** (2026-04-07) | Pipeline |

---

## Critical: Manual Translation Killed by Stale-Job Guard (FIXED)

**Severity:** Critical (manual translations never execute)
**Status:** FIXED (2026-04-07)
**Found during:** Phase 3 Belvedere German translation

**Root cause:** The orchestrator's stale-job guard (`orchestrator.ts` ~line 248) checks if a COMPLETED job exists for the same stage+museum. Pipeline runs create a COMPLETED TRANSLATION job. When a manual translation is enqueued, the guard sees the existing COMPLETED job and silently skips it -- `translateMuseumContent()` is never called. The MuseumAgent stays CREATING forever.

**Fix:** Jobs carrying `singleLanguage` (manual translation marker) are now exempted from the stale-job guard. Also `singleLanguage` is now passed through to `handleTranslation()` so only the requested language is translated.

**Files:** `src/pipeline/orchestrator.ts` (2 changes), `src/pipeline/orphan-detector.ts` (Pass 4 added)

---

## High: Disconnected UI Messaging on Translation Failures

**Severity:** High (confusing operator experience)
**Status: FIXED** (commit 295513e) — warning icons, per-language logs, health check cross-referencing
**Found during:** Phase 3 Belvedere run

**Symptom:** Multiple inconsistencies in the museum detail page:
- Pipeline progress bar shows "Translation running" while Languages section shows German as "FAILED"
- Live Logs show "TRANSLATION completed successfully" but Health Check shows "5 stale jobs found"
- Pipeline shows "10/10 Complete" but German agent is CREATING/FAILED
- Health Check issue viewer catches problems the Live Logs don't surface

**Root cause:** Pipeline progress reads from `pipelineJobs` table, Languages section reads from `museumAgents` table, and Health Check reads from both. These tables can be in inconsistent states during translation failures, retries, and manual interventions. The "TRANSLATION completed successfully" log comes from the P0 fix that makes translation always return success:true (to prevent pipeline blocking), even when individual languages fail.

**Suggested fix:**
1. Pipeline progress should cross-reference `museumAgents` status when showing Translation stage
2. If Translation stage is COMPLETED but any target language agent is FAILED/CREATING, show a warning icon instead of green checkmark
3. Live Logs should surface per-language translation outcomes, not just the stage-level result
4. Health Check should distinguish "pipeline Translation stage complete" from "all target languages translated"

**Files:** `src/app/museums/[id]/page.tsx` (pipeline progress tracker, Languages section), `src/pipeline/stages/08-reporting.ts` (health check logic)

---

## Medium: Sequential Translation Too Slow for Standard V3 Museums

**Severity:** Medium (blocks operator workflow, not visitors)
**Status: FIXED** — documents now translate in parallel via `Promise.all()`, chunks in batches of 4
**Found during:** Phase 3 Belvedere German translation

**Symptom:** Belvedere DE translation takes 60-90+ minutes. The Complete Collection Guide alone is 687K chars, split into 26 sequential Claude Sonnet chunks at ~45s each (~20 min for one document).

**Fixes applied:**
1. Chunks within each document translated in parallel batches of 4 (`PARALLEL_BATCH_SIZE = 4`) using `Promise.allSettled()`
2. Documents now translated in parallel via `Promise.all()` (previously sequential)
3. Chunk-level retry (3 attempts, exponential backoff) and in-memory caching added

**Files:** `src/pipeline/translation.ts`

---

## Critical: Operational Data Parse Crash Rolls Back All KB Docs (FIXED)

**Severity:** Critical (silently destroys successfully uploaded KB content)
**Status:** FIXED (2026-04-07)
**Found during:** Phase 3 Belvedere German translation (local debug run)

**Symptom:** All 4 KB documents translate and upload successfully (Quick Guide, 26-chunk Collection Guide, People Database, Deep Stories). Then `translateOperationalEntries()` fails to parse the LLM's JSON response. The catch block throws, triggering rollback of all 4 KB uploads. The MuseumAgent is marked FAILED. No DE docs persist on ElevenLabs. This was the ACTUAL root cause of the Belvedere translation failures -- not the stale-job guard, not timeouts, not OOM.

**Root cause:** `translateOperationalEntries()` at line ~930 used raw `JSON.parse()` without repair strategies. When the LLM produced slightly malformed JSON for operational data, the parse threw, which propagated up through the main catch block, which rolled back all KB docs.

**Fix applied:**
1. Replaced `JSON.parse()` with `parseJsonFromLlm()` (includes trailing comma repair, truncation repair)
2. Made operational data failure NON-CRITICAL: on parse failure, logs a warning and returns gracefully instead of throwing. The KB docs and agent are preserved.

**Files:** `src/pipeline/translation.ts` (line ~925-932)

---

**Final Status (Apr 8, 2026): All 16 items resolved.**

| Status | Count | Items |
|--------|-------|-------|
| **FIXED** | 14 | #1, #2, #3, #4, #5, #6, #8, #9, #10, #12, #13, #14, #15, #16 |
| **LEAVE** | 2 | #7 (infra workaround, documented), #11 (self-resolves after V3 re-runs) |

This document is safe to archive.
