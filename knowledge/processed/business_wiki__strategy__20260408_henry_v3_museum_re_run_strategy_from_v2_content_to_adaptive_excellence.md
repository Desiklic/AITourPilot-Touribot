# 20260408-henry-v3-museum-re-run-strategy-from-v2-content-to-adaptive-excellence

*Source: Business Wiki / strategy/20260408-henry-v3-museum-re-run-strategy-from-v2-content-to-adaptive-excellence.html*

## Why Re-Run All Museums with Henry V3

### The Gap Between V2 and V3

Henry V2 was a warm museum companion who told stories. Henry V3 is a warm museum companion who **adapts to each visitor** -- changing vocabulary, depth, pacing, emotional register, and story selection based on who is listening. But this adaptation only works if the content gives Henry the material to adapt with.

**V2 content** was written as a single narrative per artifact -- one story for everyone. **V3 content** is structured into 7 narrative layers that Henry selects from in real-time:

| Layer | Purpose | V2 Status | V3 Status |
|-------|---------|-----------|-----------|
| Hook | One-sentence entry point for rushed visitors | Implicit | Explicit |
| Quick ID | "Who/what/when" for identification questions | Missing | Present |
| Visual Journey | Guided seeing with type-specific instructions | Present but formulaic | Enhanced with rotation |
| Human Story | Artist as a person | Present | Present |
| Deep Thread | Art-historical depth for experts | Blended/weak | Standalone |
| Wonder Moment | The "wow" detail, enriched with IpRegistry discoveries | Present | Enhanced |
| Connection Thread | Cross-references to real artworks in same museum | Missing | Present via artifact roster |

**The 29 existing museums have V2 content.** The V3 system prompt is deployed (it went live with Belvedere), but when Henry encounters V2 content, he can't fully adapt because the layers aren't there. The Kunstkenner who asks for lesser-known works gets the same content as the casual tourist. The child asking "what's this?" gets the same depth as the expert.

### What a Re-Run Does

The re-run pipeline (`POST /api/museums/{id}/rerun`) performs a **full content regeneration** using the V3 prompts:

1. **RERUN_INTAKE** -- Transactional cleanup of old content (artifacts, people, sources, facts, provenance, AI marks, IP registry, old jobs/logs). Preserves: images, recent operational data (< 7 days), agent IDs, agent settings.
2. **INTAKE** -- Fresh research plan with V3-aware artifact selection
3. **SOURCE_DISCOVERY** -- Fresh web sources
4. **DEEP_RESEARCH** -- Fresh fact extraction + discovery engine (hidden connections, emotional narratives)
5. **COPYRIGHT_CHECK** -- Fresh legal compliance verification
6. **CONTENT_WRITE** -- V3 7-layer content generation with IpRegistry injection
7. **QUALITY_ASSURANCE** -- V3-aligned voice quality gates
8. **DATA_STRUCTURE** -- V3 Quick Guide extraction (Hook + Quick ID)
9. **ELEVENLABS_DEPLOY** -- Atomic KB swap (agent ID unchanged, visitors see no disruption)
10. **TRANSLATION** -- Parallel chunk translation for all target languages
11. **REPORTING** -- Health check + quality report

**What visitors experience during re-run:** Nothing. The atomic KB swap means the old content is live until the moment the new content is ready. Agent IDs don't change. The mobile app doesn't need to update. Visitors mid-conversation continue with old content; new conversations get V3 content.

**What changes after re-run:**
- All artifact content has 7 narrative layers
- IpRegistry discoveries woven into Wonder Moment and Connection Thread
- Quick Guide uses Hook + Quick ID instead of blind 500-char truncation
- Museum overview has V3-quality opening material for Henry's greeting
- Person biographies have Quick ID for fast identification
- TTS params set explicitly (stability: 0.35, similarity_boost: 0.65)
- V3 system prompt active (already deployed, but now content matches)

---

## Prerequisites Before First Re-Run

### Must Be Complete

| Prerequisite | Status | Notes |
|-------------|--------|-------|
| **Phase 1: V3 System Prompt** | DONE | Deployed to all agents via pipeline |
| **Phase 2: Content Pipeline Enrichment** | DONE | 7-layer prompts, IpRegistry injection, parallel chunks |
| **Phase 3: Belvedere Validation** | 1/5 test personas done | Need casual tourist, child/family, quiet visitor, German test |
| **Phase 4: Codify V3 Standard** | NOT STARTED | QA gates must align with V3 before mass re-runs |
| **Content-factory deploy** | DONE (auto-deploy on push to main) | `rerunCount` in public API response |
| **AITourPilot4 app deploy** | ON DEVELOPMENT BRANCH | Must be released before re-runs |
| **Bug fixes** | ALL 16 DONE | JSON repair, translation resilience, UI messaging, etc. |

### Critical Deploy Chain (Memory Invalidation)

The re-run pipeline increments `rerunCount` in the database. The mobile app uses this to detect stale visitor memories. **If any link is missing, returning visitors will have memories referencing artworks that no longer exist.**

The chain:
1. Stage 00c (RERUN_INTAKE) increments `rerunCount` in DB
2. Public API (`/api/public/museums`) returns `rerunCount` in response -- **DONE** (content-factory)
3. Mobile app (`MuseumAPIClient.ts`) parses `rerunCount` -- **ON DEVELOPMENT BRANCH**
4. `MuseumView.tsx` uses `rerunCount` for `VisitorMemoryService.isInvalidated()` -- **ON DEVELOPMENT BRANCH**
5. Old memory discarded, visitor starts fresh with V3 content

**Action needed:** AITourPilot4 development branch must be merged and released (Xcode build) before any museum re-run. Additional app changes on the development branch:
- Conversation lifecycle fixes (EOS, AppState, logout) for clean closure during/after re-runs
- "Clear Visit History" button in Settings for testers after re-run

### Phase 4 Must Run First

Phase 4 (Codify V3 Standard) ensures:
- QA stage voice quality criteria align with V3 (adaptive dimensions, 7-layer structure)
- No V2 prompt remnants in the active pipeline path
- V3 is the default for all new runs
- A Light-mode test run proves the full V3 pipeline end-to-end

**The test museum for Phase 4:** Run a Light-mode re-run of **Bletchley Park** (20 artifacts, EN only, smallest museum, fastest run). This validates the V3 pipeline without risking a large museum. If Bletchley Park's V3 content passes quality review, the pipeline is ready for mass re-runs.

---

## Re-Run Priority List

Prioritized by: visitor impact (popular museums first), content quality gap (V2-to-V3 improvement potential), and strategic value (partnership prospects, demo museums).

### Tier 1: High-Value Flagships (Re-Run First)

These are the museums most likely to be experienced by real visitors, demo partners, or press. V3 quality here is a competitive differentiator.

| # | Museum | City | Mode | Artifacts | Why First |
|---|--------|------|------|-----------|-----------|
| 1 | **Kunsthistorisches Museum Wien** | Vienna | LIGHT | 50 | Our home museum. User testing happened here. Hermann demos here. Already has real conversation data showing V2 limitations. Re-run as STANDARD with 80-100 artifacts for full V3 depth. |
| 2 | **Albertina** | Vienna | STANDARD | 96 | Second Vienna flagship. User testing with Mathias exposed KB gaps. Has 9 re-runs already (most tested museum). STANDARD re-run with V3 will fill content gaps. |
| 3 | **Leopold Museum** | Vienna | STANDARD | 101 | Third Vienna museum. Already STANDARD with 101 artifacts but V2 content. V3 re-run adds 7-layer structure and IpRegistry discoveries. |
| 4 | **Galleria degli Uffizi** | Florence | LIGHT | 50 | World-class collection. High demo value. Re-run as STANDARD with 80+ artifacts. |
| 5 | **Museo del Prado** | Madrid | LIGHT | 50 | Top European museum. Spanish-speaking market. Re-run as STANDARD. |

### Tier 2: Major European Destinations (Re-Run Second)

Popular tourist destinations where Henry can make the biggest impact on visitor experience.

| # | Museum | City | Mode | Artifacts | Notes |
|---|--------|------|------|-----------|-------|
| 6 | Musee d'Orsay | Paris | LIGHT | 45 | Impressionist masterpieces. High tourist traffic. |
| 7 | Van Gogh Museum | Amsterdam | LIGHT | 35 | Iconic single-artist museum. Deep visitor engagement expected. |
| 8 | National Gallery | London | LIGHT | 45 | Major English-speaking market. |
| 9 | Pergamon Museum | Berlin | LIGHT | 35 | Unique collection (ancient art). Tests Henry on non-painting content. |
| 10 | Galleria Borghese | Rome | LIGHT | 30 | Intimate, high-quality collection. |
| 11 | Palazzo Ducale | Venice | LIGHT | 35 | Architecture + painting mix. |
| 12 | Acropolis Museum | Athens | LIGHT | 35 | Archaeological collection. Tests Henry on sculpture/artifacts. |

### Tier 3: Distinctive Collections (Re-Run Third)

Museums with unique character that test Henry's adaptability across different museum types.

| # | Museum | City | Mode | Artifacts | Notes |
|---|--------|------|------|-----------|-------|
| 13 | Dali Theatre-Museum | Figueres | LIGHT | 30 | Surrealism. Tests Henry on unconventional art. |
| 14 | MUNCH | Oslo | LIGHT | 30 | Single-artist, emotionally intense. |
| 15 | Magritte Museum | Brussels | LIGHT | 25 | Surrealism. Small but deep. |
| 16 | Topkapi Palace Museum | Istanbul | LIGHT | 40 | Islamic art + Ottoman history. Cultural diversity test. |
| 17 | Museu Calouste Gulbenkian | Lisbon | LIGHT | 35 | Eclectic private collection. |
| 18 | MAH - Musee d'Art et d'Histoire | Geneva | LIGHT | 20 | Swiss collection. |

### Tier 4: Historical/Heritage Sites (Re-Run Last)

Non-traditional museums where Henry adapts to architecture, history, and objects rather than paintings.

| # | Museum | City | Mode | Artifacts | Notes |
|---|--------|------|------|-----------|-------|
| 19 | Prague Castle | Prague | LIGHT | 35 | Architecture + history. |
| 20 | Edinburgh Castle | Edinburgh | LIGHT | 35 | Military history + architecture. |
| 21 | Hungarian Parliament Building | Budapest | LIGHT | 30 | Architecture-focused. |
| 22 | Rosenborg Castle | Copenhagen | LIGHT | 30 | Crown jewels + royal history. |
| 23 | Wieliczka Salt Mine | Krakow | LIGHT | 30 | Underground heritage site. |
| 24 | Vasa Museum | Stockholm | LIGHT | 30 | Single-object museum (the ship). |
| 25 | National Museum of Ireland | Dublin | LIGHT | 30 | Archaeological. |
| 26 | Bletchley Park | Milton Keynes | LIGHT | 20 | WWII codebreaking. Phase 4 test museum. |
| 27 | SS Great Britain | Bristol | LIGHT | 20 | Maritime heritage. |
| 28 | La Pedrera (Casa Mila) | Barcelona | LIGHT | 20 | Architecture (Gaudi). |
| 29 | Neues Museum | Berlin | LIGHT | 35 | Egyptian + prehistoric. |

### Mode Upgrade Candidates

Some Tier 1-2 museums currently run in LIGHT mode but deserve STANDARD for V3 depth:

| Museum | Current | Recommended | Reason |
|--------|---------|-------------|--------|
| KHM Wien | LIGHT (50) | STANDARD (80-100) | Home museum, demo flagship, user testing site |
| Uffizi | LIGHT (50) | STANDARD (80) | World-class, high demo value |
| Prado | LIGHT (50) | STANDARD (80) | Major market, Spanish-speaking audience |
| Orsay | LIGHT (45) | STANDARD (70) | Impressionist masterpieces, Paris tourist traffic |
| Van Gogh | LIGHT (35) | STANDARD (60) | Deep single-artist engagement |

---

## Execution Plan

### Step 1: Complete Phase 3 Testing (remaining 4 personas)
### Step 2: Phase 4 -- Codify V3 Standard + Bletchley Park test re-run
### Step 3: Deploy AITourPilot4 app (development branch -> release build)
### Step 4: Verify the memory invalidation chain end-to-end
### Step 5: Begin Tier 1 re-runs (KHM Wien first, then Albertina, Leopold, Uffizi, Prado)

**Estimated timeline:** Phase 3 testing (1-2 days) + Phase 4 (1 session) + app deploy (1 day) + Tier 1 re-runs (3-5 days, can run 2-3 in parallel) = **~2 weeks to complete Tiers 1-2.**

**Parallel strategy:** Tier 1 museums can run 2-3 in parallel on the Render worker. Each STANDARD re-run takes ~6 hours. With parallel execution, 5 Tier 1 museums complete in ~2 days of wall-clock time.

---

*This document is a companion to the [Henry V3 Implementation Roadmap](../strategy/20260402-henry-v3-adaptive-personality-implementation-roadmap.html) (Phase 5: Existing Museum Migration) and the [Phase 2: Scaling Beyond Native RAG](../technical/20260408-phase-2-scaling-beyond-native-rag.html) technical architecture. Every re-run produces V3 content that is ready for the Phase 6 Dynamic Agent Architecture and Phase 7 External RAG Gateway.*
