# 20260309-updated-roadmap-phases-6-10

*Source: Business Wiki / technical/20260309-updated-roadmap-phases-6-10.html*

## Prerequisite Reading

> **Important:** This roadmap builds directly on **Architecture Evolution — Part 1: Research & Analysis**. That document establishes the technical foundations — ElevenLabs session overrides, the content optimization flywheel, Open API integration architecture, and the lean pgvector stack — that every phase in this roadmap depends on. **Read Part 1 first** before implementing any phase described here.

---

## Vision & Current State

**Vision:** A self-improving knowledge system that transforms any museum into a world-class voice-guided experience — available in any language, powered by structured data from open institutional APIs, enriched with proprietary narratives that exist nowhere else, and refined by every visitor conversation. No app store update. No museum partnership required. Just a museum name.

**Current state (March 2026):** The Content Factory is feature-complete and cloud-hosted:

| Metric | Value |
|--------|-------|
| Museums processed | 28 |
| Languages live | 5 (EN, DE, ES, FR, IT) |
| ElevenLabs agents deployed | ~150 (28 museums x ~5 languages) |
| Pipeline stages | 10 + Content Top-Up + Re-Run |
| Discovery engine | 4 proprietary IP modules, ~8 discoveries per museum |
| Legal engine | CC-BY-SA firewall, 41,407 provenance records, full audit trail |
| Infrastructure cost | ~$8/month fixed |
| Per-museum cost | ~$10 (Light), ~$20 (Standard), ~$30 (Full) |

**What already exists but is unused:**

- VectorChunk type and chunk generation in Stage 6 — produces semantic chunks but only passes them in memory (never persisted)
- `get_deep_museum_content` Server Tool registered on every agent — webhook points to `/api/rag/query` which currently returns empty context
- `/api/rag/query` endpoint scaffolded with auth, error handling, and Phase 2 comments marking where pgvector search goes

---

## Unique Value Proposition

Three capabilities that no competitor — not museum-provided audio guides, not generic AI assistants, not tour guide apps — can replicate:

**1. Proprietary Content** — The Discovery engine generates narratives that do not exist anywhere else on the internet. Hidden connections between artworks across centuries. Cross-museum synthesis that reveals how a Klimt painting in Vienna connects to a Monet in Paris through a shared patron. These are not summaries of Wikipedia — they are original intellectual property with full provenance chains.

**2. Self-Improving Flywheel** — Every visitor conversation is an implicit signal. When 200 visitors ask about the same painting and the agent hedges, that is a gap. When visitors consistently follow up on Impressionism but never ask about the gift shop, that is an interest pattern. The 100th museum automatically benefits from everything learned at the first 99.

**3. Zero-Friction Multilingual Scaling** — ElevenLabs session overrides allow a single agent per museum to serve all languages. Adding a new language requires only a voice mapping and a translation template. Zero ElevenLabs API calls to create agents.

---

## Phase 6: Dynamic Agent Architecture

**MVP: "One Agent, Any Language"** — 2--3 weeks

The current architecture creates one ElevenLabs agent per museum per language. At 100 museums and 10 languages, that is 1,000 agents. The dynamic architecture collapses this to one agent per museum. Language, voice, system prompt, and first message are injected at session start.

**Deliverables:**

| Deliverable | Description |
|-------------|-------------|
| Session Context API | `GET /api/public/museums/{id}/session-context?lang=de` — returns system prompt, voice ID, first message, and language code |
| Voice ID Registry | `SystemLanguage.voiceId` column — native speaker ElevenLabs voice per language |
| App-Side Override | AITourPilot4 sends `conversation_config_override` in the WebSocket initiation message |
| Agent Consolidation Migration | Script that identifies the EN agent as canonical, merges KB doc IDs, deletes redundant per-language agents |
| Pipeline Update | Stage 7 creates/updates a single agent per museum. Stage 7b generates translated content but does NOT create separate agents |
| Backward Compatibility | Public API continues to return per-language agent IDs (all pointing to the same canonical agent) |

**Dependencies:** None. Can start immediately.

**Risk:** ElevenLabs session override has not been tested at scale with KB documents. Mitigation: test with 3 museums across all 5 languages before running migration. Keep per-language agent creation code behind a feature flag for rollback.

**Success criteria:**
- Agent count drops from ~150 to ~28
- German visitor at Rijksmuseum hears native German voice, sees German greeting, gets German system prompt — all via session override on a single agent
- KB documents uploaded once per museum, not once per language
- New language addition requires: voice ID + translation template. Zero ElevenLabs API calls.

---

## Phase 6b: Open API Integration

**MVP: "300 Artifacts from Public APIs"** — 2--3 weeks, can overlap with Phase 6

The current pipeline discovers artifacts through web scraping. For major museums, open institutional APIs provide structured, CC0-licensed data with accession numbers, dimensions, materials, provenance chains, and high-resolution image URLs. This data is more accurate, more complete, and legally cleaner than anything scraped from the web.

**Target APIs:**

| API | Coverage | License | Data Quality |
|-----|----------|---------|-------------|
| Europeana | 50M+ objects across 3,000+ institutions | CC0 | Structured, multilingual, linked to source institutions |
| Met Museum | 400K+ objects | CC0 | Accession numbers, dimensions, materials, department, period |
| Rijksmuseum | 700K+ objects | CC0 | Dutch + English, high-res images, detailed provenance |
| Harvard Art Museums | 230K+ objects | CC0 | Excellent conservation data, color analysis |
| Smithsonian | 4.4M+ objects | CC0 | Multi-institution, diverse media types |

**Deliverables:**

| Deliverable | Description |
|-------------|-------------|
| Source Adapter Framework | Pluggable adapter interface: `search(museumName, city) => StructuredArtifact[]` |
| Europeana + Met Adapters | Query respective APIs, return structured artifacts with provenance |
| Enhanced Entity Schema | Extend Artifact model: accessionNumber, department, provenance (text), apiSourceId |
| Source Discovery Integration | Stage 1 queries open APIs first (Tier 0), then falls back to web scraping |
| Comparison Report | Rijksmuseum pipeline run: API-sourced (300+ artifacts) vs web-scraped (20 artifacts) |

**Dependencies:** None. Can run in parallel with Phase 6.

**Success criteria:**
- Rijksmuseum pipeline produces 300+ artifact entries (vs current ~20)
- All API-sourced artifacts have accession numbers and structured metadata
- CC0 sources pass copyright check with zero overhead
- Per-museum cost increase: < $2

---

## Phase 7: External RAG Gateway

**MVP: "Unlimited Knowledge Depth"** — 3--4 weeks

At 300+ artifacts per museum, managing all content within ElevenLabs' native KB becomes impractical. The RAG gateway moves deep content out of the agent's KB and serves it on demand via the already-registered Server Tool. The scaffolded `/api/rag/query` endpoint becomes a hybrid search engine backed by pgvector on existing Supabase PostgreSQL.

**Three-Tier Knowledge Serving:**

| Tier | What | Latency | Source |
|------|------|---------|--------|
| **Tier 1: Session Injection** | Common questions pre-answered in system prompt | 0ms | Top 10 FAQ + operational data |
| **Tier 2: Native KB RAG** | Small KB: museum overview + top highlights | ~155ms | Stage 6 "Museum Quick Guide" document |
| **Tier 3: External RAG Gateway** | Full content: all artifacts, all people, all discoveries | 200--400ms | VectorChunk table with pgvector embeddings |

**Deliverables:**

| Deliverable | Description |
|-------------|-------------|
| pgvector Migration | `CREATE EXTENSION vector;` on Supabase. VectorChunk table with embedding vector(1536) |
| Embeddings Pipeline | Stage 6 generates OpenAI text-embedding-3-small embeddings, persists to vector_chunks table |
| Hybrid Search Engine | pgvector cosine similarity + pg_trgm trigram matching with Reciprocal Rank Fusion |
| RAG Gateway | `/api/rag/query` upgraded: parse request, call hybrid search, format chunks, return to ElevenLabs |
| Stage 6 Dual Output | Quick Guide becomes sole in-agent KB document (~50K chars). Remaining content exists only as vector chunks |

**Dependencies:** Requires Phase 6 for session injection (Tier 1). Phase 6b provides richer content but is not strictly required.

**Success criteria:**
- Visitor asks about obscure Rijksmuseum artwork; Server Tool returns relevant chunks in <300ms
- Small KB + vector chunks together serve the full content catalog of 300+ artifacts
- Total per-museum vector storage: <5MB

---

## Phase 8: Content Optimization Flywheel

**MVP: "The Learning Museum"** — 3--4 weeks

This phase turns AITourPilot from a content delivery system into a self-improving knowledge platform. Every conversation is a learning opportunity.

**Three Analysis Passes:**

- **Pass 1 — Gap Detection (what is MISSING):** Agent hedged, deflected, or got corrected. Gaps feed back as new source tasks for Content Top-Up.
- **Pass 2 — Interest Detection (what is POPULAR):** Measures engagement depth, not just topic frequency. Popular topics get expanded; high-frequency questions get zero-latency session injection.
- **Pass 3 — Pattern Aggregation (what is UNIVERSAL):** Cross-museum patterns inform content strategy for new museums before they have any conversation data.

**Deliverables:**

| Deliverable | Description |
|-------------|-------------|
| Transcript Storage | ElevenLabs conversation-end webhook stores transcripts in Conversation table |
| Gap Detection Job | Event-driven: Claude Haiku scans for hedging, deflection, corrections. Results in KnowledgeGap table |
| Interest Detection Job | Nightly batch: aggregates topic mentions, measures follow-up depth. Results in InterestSignal table |
| Pattern Dashboard | `/analytics/patterns` — top 20 gaps and interests per museum, cross-museum universal patterns |
| Session Context Auto-Adjustment | Top 5 most-asked questions per museum auto-inserted into session injection context |
| Content Top-Up Integration | Gap detection output feeds into `POST /api/museums/{id}/top-up` — suggests artifacts to expand |
| Flywheel Metrics | Gap closure rate, interest coverage, pattern utilization |

**Dependencies:** Phase 7 (transcripts reference the RAG gateway). Phase 6 for session injection.

**Success criteria:**
- System auto-identifies at least 5 knowledge gaps per museum within first 100 conversations
- Gap closure rate: >80% within 2 Content Top-Up cycles
- Most-asked questions moved to session injection: response latency drops from 400ms to 0ms

---

## Phase 9: Institutional Data Integration

**MVP: "Museum-Grade Knowledge"** — when museum partnerships happen

This phase activates when museums approach AITourPilot wanting to integrate their institutional data. The system works without any museum involvement (Phases 6--8), but becomes dramatically better with it.

| Aspect | Without Partnership | With Partnership |
|--------|---------------------|------------------|
| Source data | Web scraping + Open APIs | Curator notes, conservation records, internal databases |
| Accuracy | High (multi-source fact-checked) | Authoritative (museum-verified) |
| Content review | Automated QA only | Museum approves before deployment |
| Coverage | Top 20--300 artifacts | Complete collection catalog |
| Operational data | Website scraping | Direct CMS API feed |
| Images | CC0 stock photos | Museum's professional photography (IIIF manifests) |
| Branding | AITourPilot standard | Co-branded: museum logo, "Official Partner" badge |

**Deliverables:**

| Deliverable | Description |
|-------------|-------------|
| Museum Admin Portal | Upload interface: PDF, CSV, JSON, API endpoint configuration |
| Tier 0 Source Integration | Museum-provided data as highest trust level, bypasses web scraping |
| Content Review Dashboard | Museum staff review generated content before deployment |
| CMS Integration Framework | Adapters for TMS (Gallery Systems), MuseumPlus (Zetcom), Axiell Collections |
| IIIF Manifest Integration | Parse IIIF manifests for high-resolution artwork images |
| Revenue Model | Custom voice, branded app experience, analytics dashboard, priority updates |

**Dependencies:** Phases 6--8 complete (self-service pipeline must work flawlessly first).

---

## Phase 10: Advanced Personalization

**MVP: "Your Personal Guide"** — Phase 9+

With the flywheel providing aggregate visitor interest data and session overrides providing per-session context injection, personalization becomes possible without storing personal data.

**Personalization Tiers:**

**Tier 1 — Within-Session Adaptation (privacy-safe, no storage):** The agent tracks what the visitor has discussed within the current session and adapts. "You seem particularly interested in the Impressionists — let me tell you about two more works in Gallery 4." No data storage, no opt-in, no privacy implications.

**Tier 2 — Thematic Tours (content-driven, no personal data):** Pre-generated thematic paths through the museum: "Art and War," "Women Artists," "Hidden Masterpieces." Generated from Phase 8 pattern data — the themes visitors consistently find engaging.

**Tier 3 — Cross-Session Recognition (opt-in, personal data):** Returning visitor gets: "Welcome back! Last time you were fascinated by Klimt's use of gold leaf. The museum has a temporary exhibition on Byzantine mosaics that inspired Klimt." Requires explicit opt-in, minimal preference data, GDPR right to deletion.

**Dependencies:** Phase 8 (pattern data drives personalization). Phase 6 (session injection delivers personalized context).

---

## Infrastructure Evolution

The architecture stays lean. No Neo4j. No Qdrant. No Airflow. No Kafka. PostgreSQL + pgvector handles everything.

| Phase | Infrastructure Changes | Monthly Cost |
|-------|----------------------|-------------|
| Current | Vercel + Render ($7) + Supabase Free + Upstash (~$1) + R2 Free | ~$8 |
| 6 | Same. Session Context API is a Vercel serverless function. Agent consolidation reduces ElevenLabs usage | ~$8 |
| 6b | Same. Open API adapters are pipeline code, not infrastructure | ~$8 |
| 7 | pgvector extension on Supabase (free on Free tier). Possible upgrade to Supabase Pro ($25) | $8--$33 |
| 8 | Transcript storage in existing Supabase. Nightly batch on existing Render worker | $8--$33 |
| 9 | Museum admin portal on Vercel. Possible Render Pro ($25) for worker headroom | $33--$58 |
| 10 | Upstash Redis session cache. Visitor profiles in Supabase | $38--$63 |

**At 100 museums:** Total infrastructure ~$57--67/month. The ElevenLabs API cost is the dominant factor at scale; Phase 6 (agent consolidation) directly reduces this by 80% at 10 languages.

---

## MVPs & Critical Path

| Phase | MVP Name | What Proves It Works | Timeline |
|-------|----------|---------------------|----------|
| 6 | One Agent, Any Language | German visitor gets native German voice + prompt via session override on a single agent | Weeks 1--3 |
| 6b | 300 Artifacts from Public APIs | Rijksmuseum agent answers questions about 300+ artworks from Europeana/Rijksmuseum API | Weeks 2--5 (overlaps Phase 6) |
| 7 | Unlimited Knowledge Depth | Visitor asks about obscure artwork; Server Tool returns vector chunks in <300ms | Weeks 5--8 |
| 8 | The Learning Museum | Dashboard shows top 20 questions per museum; session injection auto-adjusts | Weeks 9--12 |
| 9 | Museum-Grade Knowledge | Partner museum reviews and approves content; deploys within 24 hours | When first partnership materializes |
| 10 | Your Personal Guide | Agent adapts within session; returning visitor gets personalized welcome | Phase 9+ |

**Critical path:** Phase 6 --> Phase 7 --> Phase 8 (serial, each builds on the previous). Phase 6b runs in parallel. Phases 9--10 are event-triggered, not calendar-scheduled.

---

## Risk Mitigation

| Phase | Risk | Likelihood | Impact | Mitigation |
|-------|------|-----------|--------|------------|
| 6 | Session override does not support all fields reliably | Low | High | Test with 3 museums before migration. Feature flag for rollback |
| 6 | Agent consolidation migration corrupts existing agents | Medium | High | Dry-run on staging. Backup all agent IDs and KB doc IDs. Rollback script ready |
| 6b | Open API rate limits during pipeline runs | Low | Low | Exponential backoff per adapter. Cache in Source table |
| 6b | API data quality varies across institutions | Medium | Medium | Validate required fields. Fall back to web scraping for missing entities |
| 7 | pgvector latency exceeds 400ms on Supabase Free tier | Medium | Medium | HNSW index. Pre-filter by museum_id. Upgrade to Pro ($25/mo) if needed |
| 8 | ElevenLabs transcript webhook reliability | Medium | Medium | Idempotent handler with dedup. Store raw payload for reprocessing |
| 8 | False positive gap detection | Medium | Low | Relevance check in classifier. Operator review before auto-triggering top-up |
| 9 | Museum IT departments slow to provide API access | High | Low | Start with manual upload (PDF/CSV). Automate CMS sync later |
| 10 | GDPR compliance for visitor profiles | Medium | High | Minimal data by design. Explicit opt-in. Full deletion endpoint. Legal review before launch |

---

## Success Metrics

### Efficiency

| Metric | Current | Target (100 museums) |
|--------|---------|----------------------|
| Agent count | ~150 | <120 (one per museum + legacy) |
| KB uploads per pipeline run | 25 (5 per language) | 2 per museum |
| Infrastructure cost | ~$8/month | <$70/month |

### Content

| Metric | Current | Target |
|--------|---------|--------|
| Artifacts per museum (Standard) | ~20 | >300 (with Open API data) |
| Proprietary discoveries per museum | 8 avg | 15+ |
| Languages supported | 5 | 10+ (adding PT, JA, ZH, KO, AR) |

### Quality

| Metric | Current | Target |
|--------|---------|--------|
| Average response latency | Unknown | <1s for 70% of questions |
| Knowledge gap closure rate | N/A | >80% within 2 pipeline cycles |
| Questions answered without Server Tool | Unknown | >60% |

---

## The Moat

The competitive advantage is built in layers, each strengthening the ones below:

**Layer 1 (now):** Proprietary content from the Discovery engine. Hidden connections, emotional narratives, cross-museum synthesis — content that exists nowhere else on the internet.

**Layer 2 (Phase 6--6b):** Efficient architecture + rich data. One agent per museum serving any language. Hundreds of artifacts from open institutional APIs. Lower cost, higher coverage.

**Layer 3 (Phase 7):** Unlimited depth. Any question about any artifact, no matter how obscure, gets a knowledgeable answer in under a second. ElevenLabs KB limits become irrelevant.

**Layer 4 (Phase 8):** The flywheel. Every conversation makes the next conversation better. The 100th museum benefits from everything learned at the first 99.

**Layer 5 (Phase 9--10):** Institutional depth + personal experience. Museum partnerships add curator-grade knowledge. Personalization makes every visit unique.

> All of it runs on PostgreSQL, a $7 Render worker, and a free Vercel deployment. The competitive advantage is not in the infrastructure — it is in the knowledge and the system that generates it.
