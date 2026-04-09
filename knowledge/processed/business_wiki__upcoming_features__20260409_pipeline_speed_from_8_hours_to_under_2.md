# 20260409-pipeline-speed-from-8-hours-to-under-2

*Source: Business Wiki / upcoming-features/20260409-pipeline-speed-from-8-hours-to-under-2.html*

# Pipeline Speed -- From 8 Hours to Under 2

The content factory pipeline transforms a museum name into production-ready audio guide content across 10 stages. For Standard-mode museums with 80-100 artifacts, this currently takes 4-8 hours. The Belvedere run (101 Standard artifacts, EN+DE) took 8+ hours. This research maps where time goes and how to cut it to under 2 hours without sacrificing V3 quality.

---

## The Problem

The pipeline runs every stage sequentially, and within each stage, most work is done one item at a time. For a Standard museum with 80 artifacts:

- **Content Write (Stage 04):** 80 artifacts x 1-3 Sonnet calls each = 80-240 sequential LLM calls. At 10-30 seconds per call, this alone takes **2-4 hours**.
- **Deep Research (Stage 02):** ~200 sources x 1 GPT-5-mini call each = 200 sequential LLM calls. **1-2 hours.**
- **Source Discovery (Stage 01):** ~95 sequential Tavily API calls. **15-30 minutes.**
- **Copyright Check (Stage 03):** Sequential embedding + LLM similarity checks. **15-30 minutes.**

The core issue: **artifacts are independent**. Writing content for painting #1 does not depend on painting #50. Yet they process one-by-one.

---

## Where Time Goes

| Stage | Current Time | % of Total | Bottleneck |
|-------|-------------|-----------|------------|
| INTAKE | 1-2 min | 1% | Single LLM call |
| SOURCE_DISCOVERY | 15-30 min | 5% | Sequential Tavily searches |
| **DEEP_RESEARCH** | **60-120 min** | **25%** | **Sequential fact extraction (200 calls)** |
| COPYRIGHT_CHECK | 15-30 min | 5% | Sequential embeddings + LLM |
| **CONTENT_WRITE** | **120-240 min** | **50%** | **Sequential Sonnet calls (80-240 calls)** |
| QA | 5-15 min | 3% | Fast -- few LLM calls |
| DATA_STRUCTURE | 1-3 min | 1% | No LLM -- string assembly |
| ELEVENLABS_DEPLOY | 5-10 min | 2% | KB upload + indexing |
| TRANSLATION (per lang) | 30-60 min | 10% | Chunked LLM translation |
| REPORTING | 2-5 min | 1% | DB queries |

**75% of pipeline time is in two stages** (Deep Research + Content Write), both of which process items one-by-one in a simple for loop when they could process 5-10 at a time.

---

## Quick Wins (Days, Not Weeks)

These changes parallelize work within existing stages using batched Promise.allSettled. No architecture changes needed. No quality loss.

### Win 1: Parallelize Content Write (Stage 04)

**Impact: 120-240 min down to 15-30 min**

The artifact write loop is the single biggest time sink. Each artifact is fully independent -- it reads from a shared read-only facts array, writes to its own DB row, and creates its own provenance records.

Change: Process artifacts in batches of 5-8 concurrently.

- Anthropic Tier 2 rate limits allow ~26 concurrent Sonnet calls (at 3K output tokens each)
- Safe concurrency of 5-8 stays well within limits with margin for retries
- Must accumulate token/cost counters atomically and send heartbeats between batches

**Effort:** 1 day.

### Win 2: Parallelize Fact Extraction (Stage 02, Pass 1)

**Impact: 60-90 min down to 5-10 min**

The fact extraction loop processes ~200 sources one-by-one through GPT-5-mini. Each call is independent -- source N's facts don't affect source N+1's extraction.

Change: Process sources in batches of 10-15 concurrently.

- GPT-5-mini has very generous rate limits for structured output
- Resume support (skip already-extracted sources) works naturally with batched processing

**Effort:** 1 day.

### Win 3: Parallelize Source Discovery (Stage 01)

**Impact: 15-30 min down to 3-6 min**

Artifact source searches are independent Tavily API calls. Each creates its own source records.

Change: Process artifact searches in batches of 5-10 concurrently.

- Tavily paid plans allow 100+ RPM
- HTML snapshot uploads can also be parallelized within each batch

**Effort:** 0.5 day.

### Win 4: Parallelize Copyright Check (Stage 03)

**Impact: 15-30 min down to 5-10 min**

Embedding cache building and entity x source checks are both sequential. Embeddings are independent API calls. Entity checks are independent per entity.

Change: Build embedding cache in parallel batches. Run entity checks in parallel batches.

**Effort:** 0.5 day.

### Quick Wins Total

| Metric | Before | After |
|--------|--------|-------|
| Total pipeline time (80 artifacts, EN+DE) | 4-8 hours | 90-150 min |
| Content Write | 2-4 hours | 15-30 min |
| Deep Research | 1-2 hours | 5-10 min |
| Source Discovery | 15-30 min | 3-6 min |
| Copyright Check | 15-30 min | 5-10 min |
| Implementation effort | -- | 3 days |

---

## Medium Wins (1-2 Weeks)

### Win 5: Multi-Language Translation Parallelism

Currently, if a museum targets EN + DE + ES, translations run sequentially: DE finishes, then ES starts. Each language takes 30-60 min for a Standard museum.

Change: Translate all languages concurrently. Each language writes to independent MuseumAgent rows and creates independent ElevenLabs agents.

**Savings:** 30-60 min per extra language.

### Win 6: Stage Overlap (Pipeline Streaming)

The current architecture runs stages strictly in sequence: all of Deep Research must complete before Content Write begins. But early-finishing artifacts could start their content write while later artifacts are still in research.

This requires splitting the per-artifact pipeline from the per-museum pipeline -- a significant refactor.

**Savings:** 30-60 min overlap between Research and Writing stages.

### Win 7: Anthropic Batch API for Classification

Anthropic's Batch API offers 50% cost reduction with 24-hour turnaround. For non-urgent classification calls (copyright checks, gap analysis), batching could reduce costs significantly.

**Savings:** 50% cost reduction on classification calls (not time -- batch API is async).

---

## Architecture Wins (Phase 2 Timeline)

### Win 8: Multi-Worker BullMQ

Run multiple BullMQ workers: one for research stages, one for writing stages, one for deployment. Allows true pipeline parallelism where museum A is in Content Write while museum B is in Deep Research.

### Win 9: Render Worker Scaling

Upgrade from Starter (512MB, $7/mo) to Standard (2GB, $25/mo) to support in-process concurrency. Or move to Fly.io with autoscaling for demand-based worker count.

### Win 10: Concurrent Museum Processing

Process 3-5 museums simultaneously. Rate limits allow it. DB connections allow it. The only constraint is worker memory and the current concurrency: 1 BullMQ setting.

---

## The Target

| Timeline | Target | How |
|----------|--------|-----|
| This week | Under 2 hours for 80 Standard artifacts | Quick Wins 1-4 (batch parallelism) |
| This month | Under 90 minutes | + Translation parallelism + stage overlap |
| This quarter | Under 60 minutes for any museum | + Multi-worker + Render scaling |
| At scale (100+ museums) | Process 5 museums/day | + Concurrent museum runs |

---

## What NOT to Change

These quality gates must remain sequential -- they are the backbone of legal compliance and content quality:

- **Copyright Check must follow Deep Research** -- facts must be verified clean before content generation
- **QA must follow Content Write** -- content must exist before quality checks
- **V3 7-layer content architecture** -- each artifact's content must be self-contained
- **Discovery Engine for Standard/Full** -- feeds Wonder Moment and Connection layers
- **Provenance tracking** -- every paragraph traced to source (legal requirement)
- **Meta-response detection** -- prevents deploying LLM refusals as museum content
- **Atomic KB swap on deploy** -- no degraded agent window during updates

---

## Rate Limit Safety

All parallelization stays within API rate limits:

| Provider | Safe Concurrency | Current Limit |
|----------|-----------------|---------------|
| Anthropic Sonnet | 5-8 concurrent | ~1000 RPM, ~80K output tokens/min |
| Anthropic Haiku | 10-15 concurrent | Higher RPM |
| OpenAI GPT-5-mini | 10-15 concurrent | Very generous |
| Tavily Search | 5-10 concurrent | 100+ RPM (paid) |
| OpenAI Embeddings | 10-20 concurrent | Very high |

All parallelized code uses Promise.allSettled (not Promise.all) so individual failures don't crash the batch.

---

## Cost Impact

Parallelization does NOT increase cost. The same number of LLM calls are made -- they just run concurrently instead of sequentially. Total API spend remains ~$16-24 per Standard museum.

The only cost increase comes from infrastructure scaling (Render upgrade from $7 to $25/mo) if multi-worker parallelism is needed.

---

*Research document: docs/dev-specs/20260409_PIPELINE_SPEED_RESEARCH.md*
*Based on analysis of the Belvedere V3 run (101 Standard artifacts) and full codebase review of all 10 pipeline stages.*
