# demo-content-pipeline-overview

*Source: Business Wiki / technical/demo-content-pipeline-overview.html*

## Overview

The AI Tour Pilot Content Pipeline (internally called "The Factory") is a **10-stage automated system** that transforms a simple museum name into a complete, legally-cleared, multilingual audio guide experience powered by ElevenLabs Conversational AI.

The pipeline handles everything from initial research through content generation, legal verification, deployment, and translation — producing 25,000 to 100,000 words of original content per museum across up to five languages.

**Key metrics (as of March 2026):**

| Metric | Value |
|--------|-------|
| Museums processed | 28 |
| Pipeline stages | 10 (+ 2 entry variants) |
| Supported languages | 5 (EN, DE, ES, FR, IT) |
| Pipeline modes | 3 (Light, Standard, Full) |
| LLM providers | 3 (Claude, Gemini, GPT) |
| Average processing time | 15–45 minutes per museum |

> **Input:** A museum name. **Output:** Production-ready, multilingual ElevenLabs AI agents with legally-cleared knowledge bases.

---

## System Architecture

The diagram below shows the complete system architecture — from LLM providers through the 10-stage pipeline to cloud infrastructure and external services.

<div id="diagram-slot"></div>

The architecture is organized in five layers: **LLM Providers** (Claude, Gemini, GPT) at the top, **entry variants** (Top-Up and Re-Run) feeding into the main **Pipeline Stages**, supported by **External Services** (Tavily, ElevenLabs, image providers) and underpinned by **Cloud Infrastructure** (Vercel, Render, Supabase, Upstash, Cloudflare R2).

---

## The 10 Pipeline Stages

Each stage is a pure function that takes input from the previous stage and produces structured output. The entire pipeline is orchestrated via BullMQ jobs running on a Render background worker.

| # | Stage | Purpose | Key Output |
|---|-------|---------|------------|
| 00 | **Intake** | Parse museum prompt, plan artifacts, set targets | Museum record, artifact plan |
| 01 | **Source Discovery** | Find and classify web sources (museum sites, academic papers, open data) | Tiered source list with legal classification |
| 02 | **Deep Research** | AI agents extract structured facts from each source | Fact extractions (JSON), embeddings |
| 03 | **Copyright Check** | N-gram Jaccard + semantic cosine similarity analysis | Legal clearance per artifact, provenance chain |
| 04 | **Content Write** | Generate original prose from structured research notes | Guide scripts per artifact |
| 05 | **Quality Assurance** | Automated fact-checking, voice consistency, plagiarism re-check | QA scorecard, gap analysis |
| 06 | **Data Structure** | Format content for ElevenLabs knowledge base (JSON + markdown chunks) | KB documents (up to 300K chars) |
| 07 | **ElevenLabs Deploy** | Create conversational AI agent, upload knowledge base via API | Live agent with voice config |
| 07b | **Translation** | Translate KB + operational data into target languages | Per-language agents (DE, ES, FR, IT) |
| 08 | **Reporting** | Generate cost, quality, and compliance report | Pipeline run summary |

### Entry Variants

In addition to the standard pipeline, two entry variants allow content lifecycle management:

- **00b — Top-Up Intake:** Adds new artifacts to a completed museum without re-running the full pipeline. Atomic KB swap preserves the existing agent ID.
- **00c — Re-Run Intake:** Full re-run with new settings. Transactional cleanup of old content, then delegates to standard intake.

### Image Sub-Pipeline

A separate, manually-triggered sub-pipeline handles museum imagery:

1. Multi-provider search (Pexels, Pixabay, Wikimedia Commons)
2. Metadata ranking via Claude
3. Exterior/identity filtering
4. Visual thumbnail judging
5. Final selection with confidence score
6. Sharp crop to card (600x400) and background (1920x1080) formats
7. Upload to Cloudflare R2 CDN

---

## Pipeline Modes

Museums run through the factory in one of three modes. "Light" means shorter content — **not** lower quality. All modes use the best available models.

| Mode | Target Characters | Approx. Words | Approx. Pages | Use Case |
|------|------------------|---------------|---------------|----------|
| **Light** | 150,000 | ~25,000 | ~50 | Small museums, focused collections |
| **Standard** | 300,000 | ~50,000 | ~100 | Mid-size museums, diverse collections |
| **Full** | 600,000 | ~100,000 | ~200 | Major museums, comprehensive coverage |

The mode affects content depth and artifact count — research quality, legal checks, and QA rigor are identical across all modes.

---

## LLM Model Routing

The pipeline uses a multi-provider LLM strategy, routing each task to the most capable and cost-effective model:

| Task | Light / Standard | Full |
|------|-----------------|------|
| Fact extraction, classification, copyright checks | Claude Haiku 4.5 | Claude Haiku 4.5 |
| Content writing, planning, QA factual verification | Claude Sonnet 4.5 | Claude Sonnet 4.5 |
| Cross-reference research | Gemini 2.5 Pro | Claude Sonnet 4.5 |
| Discovery synthesis | Gemini 3 Pro (Standard) / skip (Light) | Claude Opus 4.6 |
| Structured JSON extraction | GPT-5-mini | GPT-5-mini |

> Model selection is configurable via the Settings UI and stored in the SystemConfig database. The model registry supports dynamic routing without code changes.

---

## Legal & Copyright Engine

The pipeline includes a multi-layered legal engine to ensure all generated content is original and properly sourced.

### Source Tier Classification

| Tier | Classification | Treatment |
|------|---------------|-----------|
| **Tier 1** — Safe | Public domain, CC-BY, museum press releases, government publications | Full content extraction allowed |
| **Tier 2** — Facts Only | Copyrighted sources, museum own-domain content | Only structured fact extraction; no prose reuse |
| **Tier 3** — Prohibited | All-rights-reserved, explicit no-use terms | Source skipped entirely |

### Copyright Safeguards

- **CC-BY-SA Firewall:** Wikipedia content passes through structured fact extraction (JSON), severing the expression chain before any prose generation.
- **Museum Domain Blocklist:** URLs matching a museum's own domain are auto-classified as Tier 2 (facts-only extraction). This prevents inadvertent reproduction of the museum's own copyrighted descriptions.
- **HTML Snapshots:** Every source page is archived with SHA-256 hash at time of access, creating an immutable audit trail.
- **Plagiarism Thresholds:** Content must pass both textual similarity (<15% n-gram Jaccard) and semantic similarity (<0.50 cosine) checks against all sources.
- **Provenance Chain:** Every piece of generated content has traceable lineage back to its research sources via the content provenance database table.
- **EU AI Act (Article 50):** Disclosure compliance for AI-generated content is maintained throughout the pipeline.

> The fundamental design principle: **AI writes from structured research notes, never directly from copyrighted sources.** The separation between research (fact extraction) and writing (original prose generation) is the core legal safeguard.

---

## Multi-Language Translation

The factory creates **one ElevenLabs agent per language per museum**. Translation is a dedicated pipeline stage, not an afterthought.

### Supported Languages

| Code | Language | Status |
|------|----------|--------|
| EN | English | Primary (content generated in English) |
| DE | German | Translated via Claude Sonnet |
| ES | Spanish | Translated via Claude Sonnet |
| FR | French | Translated via Claude Sonnet |
| IT | Italian | Translated via Claude Sonnet |

### How Translation Works

1. **Stage 07b (Translation)** runs automatically after ElevenLabs Deploy
2. The translation engine translates all KB documents + operational data using Claude Sonnet
3. A new ElevenLabs agent is created for each target language with language-appropriate voice settings
4. Each agent is independent — the MuseumAgent table tracks one row per museum per language
5. Translations can also be triggered manually per language via the API

> Multiple language translations can run in parallel — each language writes to independent database rows and creates independent ElevenLabs agents.

---

## Cloud Infrastructure

The factory is fully cloud-hosted with no local dependencies in production.

| Component | Provider | Purpose |
|-----------|----------|---------|
| **Dashboard + Public API** | Vercel | Next.js app with SSE events for real-time pipeline tracking |
| **Pipeline Worker** | Render | Background worker running BullMQ orchestrator (always-on) |
| **Database** | Supabase | PostgreSQL 16 (EU-Frankfurt) with connection pooling |
| **Job Queue** | Upstash | Serverless Redis for BullMQ job orchestration |
| **Images & Snapshots** | Cloudflare R2 | Public CDN for museum images; private bucket for litigation snapshots |
| **Mobile App** | React Native (Expo) | Consumes public API for museum data and agent connections |

### Data Flow

1. **Operator** triggers a pipeline run from the Vercel dashboard
2. **Vercel** enqueues a job to **Upstash Redis**
3. **Render worker** picks up the job and orchestrates all 10 stages
4. Each stage reads/writes to **Supabase PostgreSQL**
5. Stage 07 deploys agents to **ElevenLabs** and uploads images to **Cloudflare R2**
6. **Mobile app** fetches museum data via the public API on Vercel

---

## Content Lifecycle

### Top-Up (Content Expansion)

Completed museums can be expanded with additional artifacts without re-running the full pipeline:

- **Trigger:** UI button or API call with desired additional piece count
- **Process:** Plans new artifacts, deduplicates against existing content, runs stages 01–08 scoped to new artifacts only
- **Safety:** Atomic KB swap — uploads complete new KB, patches agent, deletes old KB. Agent ID unchanged.
- **Failure handling:** Top-up failure does NOT set the museum to FAILED

### Re-Run (Full Reset)

Museums can be fully re-run with new settings (pipeline mode, target piece count, special instructions):

- Deletes all old content while preserving images and recent operational data
- Runs the complete pipeline from scratch
- ElevenLabs KB handled via atomic swap (no service degradation window)

### Operational Refresh

A weekly cycle automatically updates time-sensitive operational data (opening hours, admission prices, temporary exhibitions) across all deployed agents.

---

## Architecture Benefits

1. **Separation of Research and Writing** — AI writes from structured research notes, never directly from copyrighted sources. This is the core legal safeguard.

2. **Full Auditability** — Every stage produces artifacts that can be reviewed. Source snapshots, fact extractions, provenance chains, QA scorecards, and cost reports create a complete audit trail.

3. **Single-Prompt Scalability** — Adding a new museum requires providing a single name. The pipeline handles everything else automatically.

4. **Multilingual by Design** — Translation is an integrated pipeline stage with independent per-language agents, not a bolt-on feature.

5. **Pipeline Resilience** — Six layers of defense prevent zombie stages and runaway costs: stage pre-condition guards, orchestrator timeouts, zombie job detection, LLM SDK timeouts, frontend polling hardening, and fetch timeout utilities.

6. **Content Lifecycle Management** — Top-up expansion, full re-runs, and automated operational refresh ensure content stays current without manual intervention.
