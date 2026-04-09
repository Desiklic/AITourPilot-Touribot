# 20260408-phase-2-scaling-beyond-native-rag

*Source: Business Wiki / upcoming-features/20260408-phase-2-scaling-beyond-native-rag.html*

> **Execution order: 1 of 2** -- This document is the **prerequisite** infrastructure plan. It must be implemented before [Henry Evolves -- Visitor Intelligence, Conversational Learning, and the Self-Improving Museum Companion](20260408-henry-evolves-visitor-intelligence-conversational-learning-and-the-self-improvin.html), whose features (Visitor Profile DB, Henry's Notebook, Adaptation Dashboard) depend on the Session Context API (Phase 6), External RAG Gateway (Phase 7), and Content Optimization Flywheel (Phase 8) defined here.

---

## Executive Summary

Phase 2 is the scaling strategy that takes AITourPilot from 28 museums and 5 languages to 100+ museums, 10+ languages, and a self-improving knowledge system. The plan builds entirely on existing production infrastructure -- no new services, no architectural rewrites. PostgreSQL + pgvector replaces the need for Neo4j, Qdrant, or Airflow.

**Current state (April 2026):** 28 museums live, 5 languages, ~150 ElevenLabs agents, $8/month infrastructure, ~$10/museum pipeline cost (Light mode). 10-stage pipeline with legal engine, discovery engine, and 3-layer operational data delivery.

**Target state:** 100+ museums, 10+ languages, ~100 agents (one per museum), self-improving content from visitor conversation analysis, unlimited content depth via external RAG gateway.

---

## The Problem We Are Solving

The current architecture creates one ElevenLabs agent per museum per language. At scale, this becomes unmanageable:

| Scale | Agents | KB Documents | Operational Refresh Calls/Cycle |
|-------|--------|-------------|-------------------------------|
| 30 museums x 5 langs | 150 | 750 | 600 |
| 100 museums x 5 langs | 500 | 2,500 | 2,000 |
| 100 museums x 10 langs | 1,000 | 5,000 | 4,000 |

Each agent consumes ElevenLabs KB storage, requires independent operational data refresh, and adds management complexity. Additionally, the ElevenLabs native KB has plan-based RAG storage limits (Creator: 20MB, Pro: 100MB) that constrain content depth per museum.

---

## The Five Phases

### Phase 6: Dynamic Agent Architecture (2--3 weeks)

**One agent per museum, any language.**

ElevenLabs confirmed that system prompt, language, voice ID, and first message can be overridden per session via conversation_initiation_client_data. Knowledge base documents and Server Tools cannot be overridden -- but they don't need to be, because those components are language-agnostic.

**How it works:**
1. One agent per museum with English KB documents, Server Tool webhook, skip_turn tool, turn_timeout: -1
2. At session start, the mobile app calls a new Session Context API that returns language-specific overrides
3. The app sends these overrides in the WebSocket conversation_initiation_client_data message

**Impact:** 500 agents become 100. KB uploads drop by 80%. Operational refresh calls drop by 80%. Adding a new language requires only a voice ID and translation template -- zero new agents.

**New endpoint:** GET /api/public/museums/{id}/session-context?lang=de

### Phase 6b: Open API Integration (2--3 weeks, parallel with Phase 6)

**300+ artifacts from public institutional APIs.**

Major museums expose structured, CC0-licensed data through public APIs. This data is more accurate, more complete, and legally cleaner than web scraping.

| API | Objects | License |
|-----|---------|---------|
| Europeana | 50M+ across 3,500+ institutions | CC0 |
| Metropolitan Museum | 470K+ objects | CC0 |
| Rijksmuseum | 700K+ objects | CC0 |
| Harvard Art Museums | 250K+ objects | CC0 |
| Smithsonian | 14M+ objects | CC0 |

**Integration:** New source adapter framework in Stage 1 (Source Discovery). API results feed into the existing fact extraction pipeline -- same copyright checks, same content generation, same legal engine. CC0 sources pass copyright checks with zero overhead.

**Why this matters:** The raw API data is available to anyone. Our competitive advantage is what the pipeline does with it -- the discovery engine generates proprietary narratives (hidden connections, emotional stories, cross-museum synthesis) that no API provides. The legal engine proves that originality paragraph by paragraph.

### Phase 7: External RAG Gateway (3--4 weeks)

**Unlimited knowledge depth via pgvector.**

The Server Tool webhook (get_deep_museum_content) is already registered on every ElevenLabs agent -- currently returning empty context. The /api/rag/query endpoint is scaffolded. Vector chunks are already generated in Stage 6 (Data Structure) but not yet persisted to a vector database.

**Three-Tier Knowledge Serving:**

- **Tier 1 -- Session Injection (Phase 6):** Top FAQ + operational data pre-loaded in system prompt. Latency: 0ms.
- **Tier 2 -- Native KB RAG (existing):** Museum overview + top highlights in small KB. Latency: ~155ms.
- **Tier 3 -- External RAG Gateway (this phase):** Full artifact database in pgvector. Latency: 200--400ms via Server Tool webhook.

**Infrastructure:** Enable pgvector extension on existing Supabase PostgreSQL (one SQL command: CREATE EXTENSION vector). No new services. HNSW index for sub-100ms similarity search. Hybrid search: pgvector cosine similarity + pg_trgm trigram matching with Reciprocal Rank Fusion.

### Phase 8: Content Optimization Flywheel (3--4 weeks)

**The system that learns from every conversation.**

Every ElevenLabs conversation produces a transcript via webhook. That transcript contains implicit signals about what visitors care about -- no star ratings, no surveys, no friction.

**Three analysis passes per transcript:**

**Pass 1 -- Gap Detection (what is missing):** Agent hedged, deflected, or got corrected. Gaps feed into the Content Top-Up pipeline for automated expansion.

**Pass 2 -- Interest Detection (what is popular):** Topic frequency, follow-up depth, engagement duration. Popular topics get prioritized for content expansion. Low-interest content gets deprioritized.

**Pass 3 -- Pattern Aggregation (what is universal):** Cross-museum patterns ("visitors at art museums always ask about techniques") inform content strategy for new museums before they have any conversation data.

**The flywheel loop:** More conversations --> better pattern data --> better content prioritization --> better session injection --> better conversations --> more engagement --> more conversations.

After ~50 conversations per museum, patterns become statistically meaningful. After 1,000 conversations, the system knows seasonal patterns, language-specific interests, and cross-museum trends.

### Phase 9: Institutional Data Integration (event-triggered)

**When museums become partners, not just subjects.**

This phase activates when museums approach AITourPilot wanting to integrate their institutional data. The system works without any museum involvement (Phases 6--8), but becomes dramatically better with it: curator notes, conservation records, internal databases, official tour scripts, professional photography via IIIF manifests.

CIDOC CRM standards compliance becomes relevant here -- when we need to speak the museum's data language for import/export. Not before.

---

## Infrastructure Evolution

No Neo4j. No Qdrant. No Airflow. No Kafka. PostgreSQL + pgvector handles everything.

| Phase | Infrastructure Changes | Monthly Cost |
|-------|----------------------|-------------|
| Current | Vercel + Render + Supabase Free + Upstash + R2 | ~$8 |
| 6 | Same (session context is a serverless function) | ~$8 |
| 6b | Same (API adapters are pipeline code) | ~$8 |
| 7 | pgvector on Supabase (free or $25 Pro for performance) | $8--$33 |
| 8 | Transcript storage in Supabase. Nightly batch on Render worker | $8--$33 |
| 9 | Museum admin portal on Vercel. Possible Render Pro ($25) | $33--$58 |

**At 100 museums: ~$57--67/month total infrastructure.**

---

## What We Decided Against

A cofounder proposal recommended Neo4j + Qdrant + Airflow + CIDOC CRM ontology (12--20 week timeline). After analysis, we adopted three ideas from it (session injection, gap detection, Open APIs) but rejected the heavyweight infrastructure:

- **Neo4j:** "What other works by this artist?" is a relational join, not a graph traversal problem at our scale
- **Qdrant:** pgvector on existing Supabase gives us vector search for free
- **Airflow:** BullMQ on Upstash Redis already provides job orchestration with retries and orphan detection
- **CIDOC CRM:** Correct standard, but weeks of schema work that doesn't improve visitor experience. Relevant in Phase 9 when museums are partners.

Same capabilities. A third of the infrastructure. A fifth of the operational overhead.

---

## The Competitive Moat (Built in Layers)

1. **Proprietary content** (now): Discovery engine creates narratives that exist nowhere else -- hidden connections, emotional stories, cross-museum synthesis
2. **Efficient architecture + rich data** (Phase 6--6b): One agent per museum, hundreds of artifacts from Open APIs
3. **Unlimited depth** (Phase 7): Any question about any artifact answered in under a second via pgvector
4. **Self-improving flywheel** (Phase 8): Every conversation makes the next one better. Gaps get filled, popular topics get deeper content, patterns transfer across museums
5. **Institutional depth** (Phase 9+): Museum partnerships add curator-grade knowledge on top of the self-improving base

Each layer strengthens the ones below it.

---

## Document Reference

All Phase 2 documents live in the content-factory repository under docs/phase-2/:

| Document | Purpose | Status |
|----------|---------|--------|
| 20260312_PHASES_UPDATED.md | Approved roadmap (Phases 6--10) with MVPs, deliverables, success metrics | APPROVED PLAN |
| 20260312_RESEARCH_PATH_FORWARD.md | Research: single-agent-per-museum, flywheel, Open APIs, lean architecture | APPROVED RESEARCH |
| 20260312_ANSWER_TO_DATA_EXTRACT_PIPELINE.md | Response to cofounder proposal -- what we adopt and what we skip | REFERENCE |
| 20260309_data_extract_pipeline.md | Cofounder's original Neo4j/Qdrant/Airflow proposal | REFERENCE |
| PHASE_2_ARCHITECTURE.md | Original Phase 2 design -- RAG Gateway + Knowledge Graph sections remain active | PARTIALLY IMPLEMENTED |
| PHASE_2_WARNINGS.md | 10 architectural risks for external RAG -- informs Phase 7 design | ACTIVE REFERENCE |
| PHASE_2_STRESS-TEST.md | 100-museum scale projections -- infrastructure bottlenecks | ACTIVE REFERENCE |
| PHASE_2_ANALYZE_TOOL_CALLING_FAILURES.md | Server Tool reliability analysis -- 5 failure modes mapped | ACTIVE REFERENCE |
| 20260217_EXPLORATION_LONG_TERM_ARCHITECTURE_BEYOND_RAG.md | Long-term Phase 1/2/3 evolution path beyond ElevenLabs native RAG | DRAFT REFERENCE |

**Archived to docs/completed/ (superseded/implemented):**
- PHASE_2_SPRINTS.md -- Sprint structure not followed; replaced by PHASES_UPDATED.md
- PHASE_2_HYBRID.md -- 3-layer operational data architecture implemented in production
- PHASE_2_REDESIGN_MAXIMUM_ROBUSTNESS.md -- 3-layer architecture spec, now live

---

## Timeline

| Phase | What | Duration | Can Overlap? |
|-------|------|----------|-------------|
| 6 | Dynamic Agent Architecture | 2--3 weeks | -- |
| 6b | Open API Integration | 2--3 weeks | Yes (parallel with Phase 6) |
| 7 | External RAG Gateway | 3--4 weeks | After Phase 6 |
| 8 | Content Optimization Flywheel | 3--4 weeks | After Phase 7 |
| 9 | Institutional Integration | When partnerships happen | After Phase 8 |

**Critical path:** Phase 6 --> Phase 7 --> Phase 8 (serial). Phase 6b runs in parallel. Phase 9 is event-triggered.

**Total estimated duration for Phases 6--8: ~10--14 weeks.**
