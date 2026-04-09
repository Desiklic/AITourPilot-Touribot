# 20260309-research-path-forward

*Source: Business Wiki / technical/20260309-research-path-forward.html*

## Overview

This document captures the foundational research behind AITourPilot's architecture evolution from Phase 6 onward. It analyses three breakthrough capabilities that transform the Content Factory from a content delivery system into a self-improving knowledge platform:

1. **Single-Agent-Per-Museum** — ElevenLabs session overrides that collapse agent proliferation from O(museums x languages) to O(museums)
2. **Content Optimization Flywheel** — implicit visitor signals from conversation transcripts that drive continuous content improvement
3. **Open Institutional API Integration** — structured CC0 data from Europeana, the Met, Rijksmuseum, and others as a high-quality factual backbone

> This research informs **Architecture Evolution -- Part 2: Roadmap (Phases 6--10)**, which defines the implementation plan and timelines.

---

## The Single-Agent-Per-Museum Breakthrough

### The Problem with Agent Proliferation

The current architecture creates one ElevenLabs agent per museum per language. The translation engine clones all 4--5 KB documents, translates them via Claude Sonnet, uploads them to ElevenLabs, and creates a fully independent agent. This works at current scale (28 museums, 5 languages) but the math gets uncomfortable quickly:

| Scale | Agents | KB Documents | Operational Refresh API Calls (per cycle) |
|-------|--------|-------------|------------------------------------------|
| 30 museums, 5 languages | 150 | 750 | 600 |
| 50 museums, 5 languages | 250 | 1,250 | 1,000 |
| 100 museums, 5 languages | 500 | 2,500 | 2,000 |
| 100 museums, 10 languages | 1,000 | 5,000 | 4,000 |

Each operational data refresh requires 4 API calls per agent. ElevenLabs API rate limits, KB document storage costs, and management complexity all scale linearly with agent count.

### ElevenLabs Session Override — Confirmed Viable

Research against ElevenLabs' official documentation (March 2026) confirms that the `conversation_initiation_client_data` payload supports per-session overrides at WebSocket connection time.

**Override Capability Matrix:**

| Parameter | Per-Session Override | Notes |
|-----------|---------------------|-------|
| System prompt | **YES** | Full replacement per session |
| Language code | **YES** | Controls ASR + response language |
| Voice ID | **YES** | Native speaker voice per language |
| First message | **YES** | Greeting in target language |
| LLM model | **YES** | Could vary by use case |
| TTS speed / stability / similarity | **YES** | |
| Dynamic variables | **YES** | Key-value injection into prompt template |
| Temperature / Max tokens | **YES** | |
| KB documents | **NO** | Agent-level only, set at creation |
| Server Tools (webhooks) | **NO** | Agent-level only |
| Built-in tools (skip_turn) | **NO** | Agent-level only |
| Turn timeout | **NO** | Agent-level only |

The critical insight: **everything that varies by language** (system prompt, voice, greeting, language code) CAN be overridden per session. Everything that is **language-agnostic** (KB documents, Server Tools, built-in tools, turn configuration) CANNOT be overridden but does not need to be, because those components work identically across languages.

### Architecture: One Agent, Many Languages

1. **One agent per museum** with English KB documents (baseline knowledge), Server Tool webhook registered, `skip_turn` built-in tool enabled, `turn_timeout: -1`.
2. **At session start**, the mobile app calls the factory's Session Context API, receives language-specific configuration, and passes it to ElevenLabs via `conversation_initiation_client_data`.

The WebSocket initiation payload transforms an English-configured agent into a German-speaking guide with a native German voice, German greeting, and a system prompt containing operational data already translated into German. The KB documents remain in English, but the LLM reads them and responds in the overridden language.

### The KB Language Tradeoff

KB documents stay in English because they cannot be overridden per session. This is an acceptable tradeoff for three reasons:

**First**, deep content comes via the Server Tool webhook. The `get_deep_museum_content` Server Tool fires a POST request to our RAG gateway. This webhook CAN return language-specific content because our API controls the response.

**Second**, the system prompt carries the language-sensitive content. Operational data, voice personality, cultural context, and visitor interaction style are all injected via the system prompt override. This is where language matters most for user experience.

**Third**, ElevenLabs enforces plan-based RAG storage limits (Creator: 20MB, Pro: 100MB). Keeping KB in English only avoids duplicating storage per language.

### Impact: Agent Reduction

| Metric | Current (per-language agents) | Single-agent-per-museum |
|--------|------------------------------|------------------------|
| Agents at 100 museums | 500 | 100 |
| KB documents | 2,500 | 500 |
| Operational refresh API calls per cycle | 2,000 | 400 |
| Translation engine runs | Full KB retranslation per language | System prompt + operational data only |
| ElevenLabs monthly cost | Scales with agent count | **5x reduction** |

### Session Context API

A new endpoint assembles everything the app needs to override an agent's configuration for a specific museum and language:

`GET /api/public/museums/{id}/session-context?lang=de`

This endpoint replaces per-language agent creation with dynamic assembly. The system prompt is generated on the fly from the stored English prompt template + translated operational data + language-specific voice personality instructions. Cache headers (ETag + `Cache-Control: max-age=3600`) ensure the app does not re-fetch unnecessarily within a visit.

---

## The Content Optimization Flywheel

### Beyond Gap Detection

A knowledge gap detection system that analyzes conversation transcripts for hedging language, deflections, and user corrections captures what the agent FAILS at. That is valuable for filling holes — but it is incomplete. Gap detection is defensive. The real opportunity is offensive: understanding what visitors **CARE about**. What sparks genuine curiosity? What makes someone spend eight turns on Impressionism? This is not error correction. This is content optimization.

### Implicit Signals Beat Explicit Ratings

The conversation transcript IS the rating. Every ElevenLabs conversation generates a full transcript via webhook. That transcript contains rich implicit signals that require zero user effort:

- **What someone asks about** = what they care about
- **How long they stay on a topic** (turn count) = how engaged they are
- **Whether they ask follow-up questions** = how deep their interest goes
- **What they skip or redirect away from** = what they do not value
- **What they correct** = where the content is wrong
- **What they express surprise or excitement about** = what resonates emotionally

No star rating, no thumbs up/down, no survey. Zero friction. The signal-to-noise ratio is far higher than explicit ratings because people reveal their true interests through behavior, not through the cognitive overhead of rating systems.

### Three Analysis Passes

Every conversation transcript runs through three parallel analysis passes:

**Pass 1: Gap Detection** (what is MISSING)

The agent hedged, deflected, or the user corrected a factual error. These gaps feed directly into the content pipeline: automatically generate source discovery tasks for missing topics, flag factual errors for correction in the next pipeline run, and track recurring gaps across conversations to prioritize high-impact fixes.

**Pass 2: Interest Detection** (what is POPULAR)

Interest detection measures engagement depth, not just topic frequency. A visitor asked 3 follow-up questions about Klimt's gold-leaf technique — high interest signal. 70% of visitors at Leopold Museum ask about Schiele's personal life within the first 5 minutes — universal interest pattern. These signals drive content prioritization: popular topics get expanded via the Content Top-Up pipeline, high-frequency questions get moved into session-injection context for zero-latency answers.

**Pass 3: Pattern Aggregation** (what is UNIVERSAL)

Aggregating across ALL conversations at a museum — and across museums — reveals structural patterns:

- **Top 20 questions per museum** go into session-injection context for instant answers
- **Most-discussed artifacts** are candidates for content expansion
- **Least-asked-about content** gets deprioritized in KB allocation
- **Cross-museum patterns** inform content strategy for new museums before they have any conversation data
- **Seasonal patterns** allow content emphasis to shift automatically
- **Language-specific patterns** enable language-specific session context adaptation

### The Full Flywheel Loop

More conversations lead to better pattern data, which leads to better content prioritization, which leads to better session injection, which leads to better conversations, which leads to more engagement, which leads to more conversations. This is a self-improving system — every museum visit makes the next visit better.

The flywheel has a cold-start problem (no data before the first conversation), but the Content Top-Up pipeline and cross-museum pattern transfer provide reasonable initial content. After approximately 50 conversations per museum, the pattern data becomes statistically meaningful.

### Three Content Pillars

**Stories / Entertainment** — The emotional hook. Hidden connections between artworks, fascinating backstories, "the thing the museum does not tell you on the plaque." This is the discovery engine's domain, generating proprietary IP that no competitor can replicate.

**Information** — Factual depth. Artist biographies, provenance chains, conservation histories, techniques, dimensions, materials. This is where Open APIs and structured data shine. The depth must be sufficient that a visitor can ask about ANY artwork in a 300-artifact museum and receive an informed answer.

**Community** — Aggregate visitor insights. "Most visitors find this painting surprising because of the hidden figure in the lower left corner." Content generated FROM visitor patterns, not just for visitors. It transforms the experience from one-directional information delivery into a sense of shared discovery.

---

## Open Institutional APIs as Data Source

### What Open APIs Provide

Major cultural institutions and aggregators expose structured collection data through public APIs:

| API | Objects | License | Key Data |
|-----|---------|---------|----------|
| **Europeana** | 50M+ across 3,500+ institutions | CC0 | Multilingual metadata (30+ languages), provenance, exhibition history |
| **Metropolitan Museum** | 470K+ | CC0 | Accession numbers, dimensions, materials, artist bios, image URLs |
| **Rijksmuseum** | 700K+ | CC0 | High-res images, detailed provenance, conservation notes |
| **Harvard Art Museums** | 250K+ | CC0 | Technical studies, exhibition history, publications |
| **Smithsonian** | 14M+ across 20 museums | CC0 | Cross-collection relationships, archival documents |
| **Art Institute of Chicago** | 120K+ | CC0 | IIIF images, detailed medium descriptions |

This data is free, requires no partnership agreement, and comes with CC0 licensing (public domain dedication). No attribution required, no derivative work restrictions, no legal ambiguity.

### What Our Pipeline Adds On Top

Open APIs provide facts. Our pipeline generates value:

- **Original IP**: The discovery engine creates hidden connections, emotional narratives, cross-museum synthesis, and archive deep-dives that no API provides.
- **Voice-optimized prose**: Museum catalog descriptions ("Oil on canvas, 1889, 73.7 x 92.1 cm") become spoken content ("Imagine standing in front of this painting. It is nearly a meter wide, and Van Gogh painted it in the summer of 1889...").
- **Copyright-safe generation**: The CC-BY-SA firewall, plagiarism scanning, and provenance audit trail ensure that generated prose is original, not derived from copyrighted expression.
- **The "lesser known stuff, secrets" differentiator**: The discovery engine specifically seeks content that is NOT on the museum's main tour, NOT on the Wikipedia page, NOT in the standard guidebook.

### Integration Architecture

Open APIs integrate into the existing pipeline as a Tier 1 source, augmenting and partially replacing web scraping:

- **Tier 1: Open APIs** (Europeana, Met, Rijksmuseum, etc.) — Structured data: facts, dates, dimensions, provenance, exhibition history. Replaces/supplements web scraping for factual data in Stage 1 (Source Discovery). Higher reliability, structured format, no HTML parsing failures.
- **Tier 2: Web scraping** (Wikipedia, museum websites, specialist publications) — Additional context: current exhibitions, recent scholarship, visitor reviews. CC-BY-SA firewall applies (fact extractions only, never prose).
- Both feed into Stage 2 (Deep Research) through the existing fact extractions pipeline, maintaining the same copyright protections regardless of source type.

### Legal Strength

Open API sourcing materially strengthens the legal position. The provenance chain becomes:

1. **Source**: Museum's own public API, CC0 licensed (public domain)
2. **Extraction**: Structured facts stored in fact extractions table (dates, dimensions, materials — not expression)
3. **Generation**: Claude generates 100% original prose from structured facts
4. **Verification**: Plagiarism scanner confirms <15% textual similarity AND <0.50 semantic similarity to any source

In a hypothetical dispute, the argument is airtight: the source data was the museum's own public API with a CC0 public domain dedication, only facts were extracted (which are not copyrightable under Feist v. Rural), and entirely original prose was generated. Full provenance audit trail available. No gray areas, no fair-use arguments needed.

### Museum Partnership Readiness

By launching with public APIs and AI-generated content, museums discover their institution on AITourPilot without any partnership agreement. The content is already good — accurate facts, engaging narratives, proper voice optimization. When a museum approaches wanting to integrate their proprietary data (curator notes, conservation records, internal databases), the pipeline is ready to accept it as premium Tier 0 sources. The museum gets a better audio guide than they could build themselves; we get exclusive content that no competitor can access.

---

## 300+ Artifacts Without Heavyweight Architecture

### The Lean Stack

The typical enterprise approach involves deploying a constellation of specialized services. We do not need that.

| Capability | Enterprise Stack | Our Lean Stack |
|------------|-----------------|----------------|
| Entity storage | Neo4j / Neptune (graph DB) | PostgreSQL (existing) with EntityEdge relation table |
| Vector search | Qdrant / Weaviate / Pinecone | pgvector extension on Supabase (existing DB, free tier) |
| Workflow orchestration | Airflow / Prefect / Temporal | BullMQ on Upstash Redis (existing, ~$1/month) |
| Raw content storage | MinIO / S3 (new bucket) | Cloudflare R2 (existing bucket) |
| API data ingestion | Custom Python ETL service | Enhanced Stage 1 source providers (TypeScript, existing codebase) |
| Content serving | Custom RAG API (new service) | Session Context API + Server Tool webhook (existing scaffold) |
| Embedding generation | Dedicated embedding service | OpenAI text-embedding-3-small (existing integration) |

**Total new infrastructure required**: Enable the pgvector extension on our existing Supabase PostgreSQL instance. One SQL command. No new services, no new hosting costs, no new deployment pipelines.

### The Combined Serving Architecture

The complete flow from museum selection to conversation:

1. **User selects museum + language in mobile app**
2. **Session Context API** (~200ms, cached with ETag) — Queries MuseumAgent table for system prompt and voice ID. Queries operational data. Queries pgvector for top-K artifacts for session injection. Assembles conversation config override JSON.
3. **ElevenLabs WebSocket Connection** — Language-specific system prompt with operational data, top 15--20 artifact summaries from session injection, native speaker voice ID, greeting in target language.
4. **Visitor asks common question** — Answered from injected session context with ZERO retrieval latency.
5. **Visitor asks deep/uncommon question** — Server Tool fires POST to /api/rag/query. pgvector similarity search across full artifact database. Returns relevant content chunks (200--300ms round trip). Agent synthesizes response.
6. **Post-Conversation** — ElevenLabs transcript webhook fires. Gap detection, interest detection, pattern aggregation. Flywheel adjusts session injection priorities for next visitor.

### Why This Works

- **Zero latency for common questions.** Session-injection context pre-loads answers to the most frequent questions directly into the conversation.
- **200--300ms for deep dives.** pgvector similarity search against the full artifact database. At 300 artifacts with 1536-dimensional embeddings, pgvector returns results in under 50ms; total round trip including network is 200--300ms.
- **Unlimited content depth.** No document count limit, no character limit, no retrieval ceiling.
- **Language-agnostic agents.** One agent per museum, language overridden per session. The Server Tool webhook can return content in any language.
- **Self-improving content.** The flywheel continuously refines what goes into session-injection context.

---

## Architecture Summary

Seven capabilities compound into something no competitor offers:

1. **Single-agent-per-museum** — 5x reduction in agent count, KB documents, and operational refresh overhead. Management complexity drops from O(museums x languages) to O(museums).

2. **Session injection** — The most common questions at each museum are answered with zero retrieval latency. This is the difference between a 2-second response and a 200ms response for the questions that matter most.

3. **Server Tool webhook** — Unlimited content depth for deep questions. Native KB storage limits become irrelevant when the full artifact database is accessible via pgvector similarity search.

4. **Content optimization flywheel** — Self-improving content from implicit visitor signals. No ratings, no surveys, no friction. Every conversation generates pattern data that improves the next conversation.

5. **Open API integration** — Structured data from Europeana, the Met, Rijksmuseum, and dozens of other institutions provides the factual backbone. CC0 licensing eliminates legal ambiguity.

6. **Lean infrastructure** — pgvector on existing Supabase PostgreSQL. No new services, no new hosting costs. The entire serving stack runs on the existing ~$8/month infrastructure plus one PostgreSQL extension.

7. **Legal fortress** — CC-BY-SA firewall on all web-scraped content. CC0 public domain data from Open APIs. Plagiarism scanning with dual thresholds. Full provenance audit trail. API-sourced provenance chain is legally airtight.

> This is not an audio guide. It is a self-improving knowledge system that gets better with every conversation, powered by structured museum data, enriched with proprietary narratives that no competitor can replicate, and served with zero-latency voice delivery on infrastructure that costs less than a museum entrance ticket per month.
