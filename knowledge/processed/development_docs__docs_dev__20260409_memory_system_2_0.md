# 20260409_MEMORY_SYSTEM_2_0

*Source: Development Docs / 20260409_MEMORY_SYSTEM_2_0.md*

# Memory System 2.0 -- Implementation Plan

**Date:** 2026-04-09
**Author:** Architecture Analyst (Claude Opus 4.6)
**Status:** Ready for implementation
**Estimated effort:** 20--28 hours across 6 phases
**Risk level:** Medium (data migration on live SQLite DB)

---

## Executive Summary

TouriBot's memory system was copied from HenryBot as a generic fact/event/insight store. It has no structural link to the museum pipeline, uses junk-prone Haiku extraction, scores FTS results by ordinal rank instead of BM25, leaves orphaned embeddings on delete, and walls off research intelligence from the memory search. Memory System 2.0 fixes all of this by making memory **museum-centric** -- every memory can be structurally linked to a museum via foreign key, extracted with Sonnet using JSON schema output, searched with Reciprocal Rank Fusion scoring, and loaded in progressive tiers that match the current task. The research orchestrator will bridge its findings into memory.db so nothing discovered is ever siloed.

Six independently verifiable phases. Each phase ships a working system. Rollback is possible at every step.

---

## Architecture Diagram

```
                              MEMORY SYSTEM 2.0 — DATA FLOW
 ┌─────────────────────────────────────────────────────────────────────────────────┐
 │                                                                                 │
 │   ┌──────────────┐     ┌──────────────┐     ┌──────────────┐                   │
 │   │  CLI Chat     │     │  Dashboard   │     │  Research    │                   │
 │   │  session.py   │     │  chat_handler│     │  orchestrator│                   │
 │   └──────┬───────┘     └──────┬───────┘     └──────┬───────┘                   │
 │          │                    │                     │                            │
 │          │         ┌──────────┴──────────┐          │                            │
 │          │         │  Tiered Context     │          │                            │
 │          │         │  Assembly           │          │                            │
 │          │         │                     │          │                            │
 │          │         │  T1: soul + user +  │          │                            │
 │          │         │      pipeline +     │          │                            │
 │          │         │      top memories   │          │                            │
 │          │         │                     │          │                            │
 │          │         │  T2: museum-        │          │                            │
 │          │         │      specific       │          │                            │
 │          │         │      memories +     │          │                            │
 │          │         │      contacts       │          │                            │
 │          │         │                     │          │                            │
 │          │         │  T3: full research  │          │                            │
 │          │         │      + templates +  │          │                            │
 │          │         │      history        │          │                            │
 │          │         └──────────┬──────────┘          │                            │
 │          │                    │                     │                            │
 │          ▼                    ▼                     │                            │
 │   ┌────────────────────────────────┐                │                            │
 │   │    Sonnet Extraction           │                │                            │
 │   │    (JSON Schema Output)        │                │                            │
 │   │                                │                │                            │
 │   │  classify → extract →          │                │                            │
 │   │  resolve museum_id →           │                │                            │
 │   │  dedup check → write           │                │                            │
 │   └────────────┬───────────────────┘                │                            │
 │                │                                    │                            │
 │                ▼                                    ▼                            │
 │   ┌──────────────────────────────────────────────────────┐                      │
 │   │                    memory.db                          │                      │
 │   │                                                       │                      │
 │   │  memories                                             │                      │
 │   │  ┌────┬─────────┬──────────────┬─────┬────────────┐  │                      │
 │   │  │ id │ content │ museum_id FK │ tags│ source     │  │                      │
 │   │  │    │         │ (nullable)   │ JSON│ extraction/│  │                      │
 │   │  │    │ type: contact_intel,   │     │ manual/    │  │                      │
 │   │  │    │   museum_intel,        │     │ research/  │  │                      │
 │   │  │    │   interaction,         │     │ cli        │  │                      │
 │   │  │    │   strategy, research,  │     │            │  │                      │
 │   │  │    │   general              │     │            │  │                      │
 │   │  └────┴─────────┴──────────────┴─────┴────────────┘  │                      │
 │   │                                                       │                      │
 │   │  memory_embeddings  (384-dim, all-MiniLM-L6-v2)      │                      │
 │   │  vec_memories       (sqlite-vec accelerated)          │                      │
 │   │  memories_fts       (FTS5, BM25 scoring)              │                      │
 │   │  session_chunks     (conversation transcript search)  │                      │
 │   │  embedding_cache    (content-hash dedup)              │                      │
 │   └──────────────────────────────────────────────────────┘                      │
 │                │                                                                │
 │                │  RRF Hybrid Search                                             │
 │                │  (museum_id filtering when context known)                      │
 │                ▼                                                                │
 │   ┌──────────────────────────────────────────────────────┐                      │
 │   │                    leads.db                           │                      │
 │   │  museums (id, name, stage, ...) <── FK ── memories   │                      │
 │   │  contacts                                             │                      │
 │   │  interactions                                         │                      │
 │   │  research                                             │                      │
 │   └──────────────────────────────────────────────────────┘                      │
 │                                                                                 │
 └─────────────────────────────────────────────────────────────────────────────────┘
```

---

## Files NOT to Touch (Scope Fence)

These files are out of scope for Memory System 2.0. Changes to them would indicate scope creep.

| File | Reason |
|------|--------|
| `soul.md` | Locked. Only Hermann edits. |
| `memory/USER.md` | Sacred. Never auto-modified. |
| `tools/leads/lead_db.py` | Stable CRM schema. Memory links TO it; it does not change. |
| `tools/leads/pipeline.py` | Display layer only. No memory coupling needed. |
| `tools/outreach/drafter.py` | Email drafting engine. Consumes memory via personalizer, not directly. |
| `tools/outreach/scorer.py` | Response scoring. Unchanged. |
| `tools/knowledge/ingest.py` | One-time knowledge ingestion. Unrelated to memory. |
| `tools/research/search_client.py` | Search API wrapper. Unchanged. |
| `tools/research/jina_reader.py` | Page fetcher. Unchanged. |
| `tools/research/research_planner.py` | Query planning. Unchanged. |
| `tools/research/research_evaluator.py` | Coverage evaluation. Unchanged. |
| `tools/research/research_synthesizer.py` | Report synthesis. Unchanged. |
| `tools/research/research_state.py` | State persistence. Unchanged. |
| `run.py` | CLI entry point. Might get a minor tweak in M6 but is not a target. |
| `hardprompts/*` | Static prompt templates. Unchanged. |
| `knowledge/*` | Processed knowledge files. Unchanged. |

---

## Global Rollback Strategy

Memory System 2.0 uses **additive migrations only** (ALTER TABLE ADD COLUMN, new functions alongside old ones). The nuclear rollback option at any phase:

1. **Restore `memory.db` from backup.** Every phase begins with a backup step: `cp data/memory.db data/memory_backup_MXXX.db`
2. **Git revert the phase commit.** Each phase is a single commit with a clear message.
3. **Re-run `init_db()`** -- the old schema still works because new columns are nullable and old code ignores them.

The migration functions are idempotent. Running them twice is safe. The backfill function checks for existing values before overwriting.

---

## Phase M1: Schema Migration + museum_id Linkage

### Goal

Add `museum_id`, `tags`, and `source` columns to the `memories` table, backfill museum_id from `[MUSEUM: X]` text tags, and fix the orphaned embedding bug on delete.

### Files to Modify

| File | Function(s) | What Changes |
|------|------------|--------------|
| `tools/memory/memory_db.py` | `init_db()` | Add 3 new columns via ALTER TABLE. Add index on `museum_id`. Add DELETE trigger for embeddings cleanup. |
| `tools/memory/memory_db.py` | NEW `_migrate_memories_v2()` | Idempotent migration: adds columns if missing, backfills museum_id from `[MUSEUM: X]` tags. |
| `tools/memory/memory_db.py` | NEW `_resolve_museum_id(name)` | Fuzzy-match a museum name against `leads.db` museums table. Returns int or None. |
| `tools/memory/memory_db.py` | `add_memory()` | Accept optional `museum_id`, `tags`, `source` params. Pass them through to INSERT. |
| `tools/memory/memory_db.py` | `delete_memory()` | Delete from `memory_embeddings` AND `vec_memories` before deleting from `memories`. |
| `tools/memory/memory_db.py` | `search_memories()` | Return new columns in result dicts. |
| `tools/memory/memory_db.py` | `list_memories()` | Return new columns. Accept optional `museum_id` filter parameter. |
| `tools/memory/memory_db.py` | `hybrid_search()` | Accept optional `museum_id` filter. When provided, add WHERE clause on both FTS and vector paths. |
| `tools/memory/memory_write.py` | `write_memory()` | Accept and pass through `museum_id`, `tags`, `source` to `add_memory()`. |

### What Changes and Why

**New columns on `memories` table:**

```sql
ALTER TABLE memories ADD COLUMN museum_id INTEGER REFERENCES museums(id);
ALTER TABLE memories ADD COLUMN tags TEXT;      -- JSON array: ["outreach", "pricing"]
ALTER TABLE memories ADD COLUMN source TEXT;    -- "extraction", "manual", "research", "cli"
CREATE INDEX IF NOT EXISTS idx_memories_museum_id ON memories(museum_id);
```

- `museum_id` -- nullable FK to `leads.db.museums.id`. NULL means "global" (not museum-specific). This is the structural link that replaces the `[MUSEUM: X]` text tag hack.
- `tags` -- JSON array for flexible categorization beyond the `type` column. Supports multiple tags per memory.
- `source` -- provenance tracking: where did this memory come from? Values: `extraction` (auto-extracted from chat), `manual` (user ran `remember`), `research` (from research bridge), `cli` (from dashboard or API).

**Cross-database museum_id resolution:** `_resolve_museum_id(name)` opens a read-only connection to `leads.db` and does a case-insensitive LIKE match against `museums.name`. This is the same pattern used in `lead_db.get_museum()`. It must handle: (a) leads.db not existing yet, (b) no match found, (c) multiple matches (take first by ID).

**Backfill logic in `_migrate_memories_v2()`:**

```python
# For each memory where museum_id IS NULL and content contains [MUSEUM: ...]
# Extract the museum name from the tag
# Resolve to museum_id via _resolve_museum_id()
# UPDATE memories SET museum_id = ? WHERE id = ?
```

The regex pattern: `\[MUSEUM:\s*(.+?)\]`

**Delete cleanup:** Current `delete_memory()` only deletes from `memories`. The FTS trigger handles `memories_fts`, but `memory_embeddings` and `vec_memories` rows are orphaned. Fix:

```python
def delete_memory(memory_id: int):
    conn = init_db()
    cursor = conn.cursor()
    # Clean up embeddings first
    cursor.execute("DELETE FROM memory_embeddings WHERE memory_id = ?", (memory_id,))
    try:
        cursor.execute("DELETE FROM vec_memories WHERE memory_id = ?", (memory_id,))
    except Exception:
        pass  # vec0 table may not exist
    cursor.execute("DELETE FROM memories WHERE id = ?", (memory_id,))
    deleted = cursor.rowcount
    conn.commit()
    conn.close()
    return {"deleted": deleted, "id": memory_id}
```

### Safety Invariants

1. **Existing memories must not be lost.** ALTER TABLE ADD COLUMN is non-destructive. All new columns are nullable.
2. **Old code paths must still work.** `add_memory()` defaults: `museum_id=None`, `tags=None`, `source=None`. Callers that don't pass these get the old behavior.
3. **leads.db may not exist.** `_resolve_museum_id()` must handle FileNotFoundError gracefully and return None.
4. **Backfill must be idempotent.** Only update rows where `museum_id IS NULL` and content contains a `[MUSEUM:]` tag.
5. **FTS triggers must still fire.** Do not modify or drop existing triggers.

### How to Verify

1. Run `python -c "from tools.memory.memory_db import init_db; init_db()"` -- no errors.
2. Check schema: `sqlite3 data/memory.db ".schema memories"` shows `museum_id`, `tags`, `source` columns.
3. Check backfill: `sqlite3 data/memory.db "SELECT id, museum_id, content FROM memories WHERE museum_id IS NOT NULL"` returns rows for memories that had `[MUSEUM: X]` tags AND have matching museums in leads.db.
4. Check delete: add a test memory, note its ID, delete it, verify no row in `memory_embeddings` or `vec_memories` for that ID.
5. Check filtered search: `python -c "from tools.memory.memory_db import hybrid_search; print(hybrid_search('test', museum_id=1))"` -- returns only memories for museum_id=1 (or empty if none).
6. Run existing `python run.py recall "Joanneum"` -- still works, returns results with new columns in output.

### Downstream Impact

| Component | Impact | Action Required |
|-----------|--------|----------------|
| `memory_write.py` | Must pass new params | Updated in this phase |
| `session.py` `_extract_and_save_memories()` | Calls `write_memory()` -- still works with old signature | None yet (Phase M2 updates this) |
| `personalizer.py` `_search_museum_memories()` | Calls `hybrid_search()` -- still works | None yet (can use museum_id filter in M3) |
| `chat_handler.py` | Calls `_search_memory_context()` which calls `hybrid_search()` | None |
| Dashboard `memory-db.ts` | SELECT * returns new columns -- TS type must be updated | Phase M6 |
| Dashboard `types.ts` Memory interface | Missing new fields | Phase M6 |

### Risk Areas

1. **#1: Cross-database FK resolution.** `memory.db` and `leads.db` are separate SQLite files. There is no real FK enforcement -- `museum_id` is a logical FK. If a museum is deleted from leads.db, the memory still references its old ID. Mitigation: document this as a known limitation; add a comment in code. The museum count is small (<200) and deletes are rare.

2. **#2: Backfill regex matching ambiguity.** The `[MUSEUM: X]` tags in existing memories may not match museum names in leads.db exactly (e.g., "Great Britain" vs "SS Great Britain"). Mitigation: use the same fuzzy LIKE match from `get_museum()`, which does `LOWER(name) LIKE %query%`. Log any memories where the tag was found but no museum matched.

### Rollback

1. `cp data/memory_backup_M1.db data/memory.db` restores the pre-migration state.
2. `git revert <M1-commit>` restores the old code. The extra columns in the DB are harmless -- old code ignores them via `SELECT *` and dict construction.

---

## Phase M2: Domain-Specific Memory Types + Sonnet Extraction

### Goal

Replace the generic fact/event/insight/error type taxonomy with museum-sales-domain types, switch extraction from Haiku free-text to Sonnet JSON schema output, and add a classify-first gate to skip trivial exchanges.

### Files to Modify

| File | Function(s) | What Changes |
|------|------------|--------------|
| `tools/memory/memory_db.py` | `add_memory()` | Accept new type values. No validation change needed (type is TEXT, not ENUM). |
| `tools/memory/memory_db.py` | `list_memories()` | Accept new type values in filter. |
| `tools/memory/memory_write.py` | `append_to_log()` | Expand `type_marker` dict with new types. |
| `tools/memory/memory_write.py` | `main()` argparse | Update `choices` list for `--type`. |
| `tools/chat/session.py` | `_extract_and_save_memories()` | Complete rewrite: Sonnet model, JSON schema prompt, classify-first gate, museum_id resolution. |
| `args/settings.yaml` | `models.memory_extraction` | Change model to `claude-sonnet-4-6`, max_tokens to 1024 (fix mismatch). |

### What Changes and Why

**New type taxonomy:**

| New Type | Replaces | Semantic Meaning |
|----------|----------|-----------------|
| `contact_intel` | fact (about people) | Information about a specific person: role, preferences, communication style, response history |
| `museum_intel` | fact (about museums) | Information about a museum: visitor numbers, tech stack, budget cycles, digital maturity |
| `interaction` | event | A specific dated interaction: email sent, meeting held, response received |
| `strategy` | insight | Campaign-level learnings: what angles work, timing insights, template performance |
| `research` | (none -- new) | Findings from the research orchestrator bridged into memory |
| `general` | fact/insight (catch-all) | Anything that doesn't fit the above: product facts, business context, Hermann's preferences |

**Why switch types:** The old types (`fact`, `event`, `insight`, `error`) are too generic for a museum sales assistant. When Touri assembles context for drafting an email to Joanneum, she needs to know: "What do we know about the people there?" (contact_intel), "What do we know about the museum itself?" (museum_intel), "What have we done so far?" (interaction). The current types force everything into ambiguous buckets.

**Backward compatibility:** Old memories with type `fact` still work -- they just show as `fact` in search results. No migration needed on existing type values. The new types apply to newly extracted memories only. Over time, the curator (Phase M6) can reclassify old memories.

**Sonnet extraction with JSON schema:**

The current extraction in `session.py` lines 241--296 uses Haiku with free-text prefix tags (`[FACT]`, `[EVENT]`, `[INSIGHT]`). This produces junk: vague summaries, duplicate phrasing, memories that don't add value.

New extraction uses Sonnet with a JSON schema response:

```python
EXTRACTION_SCHEMA = {
    "type": "object",
    "properties": {
        "worth_saving": {
            "type": "boolean",
            "description": "True if this exchange contains information worth remembering for future sessions"
        },
        "memories": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "content": {"type": "string", "description": "The fact to remember, concise and self-contained"},
                    "type": {"type": "string", "enum": ["contact_intel", "museum_intel", "interaction", "strategy", "general"]},
                    "importance": {"type": "integer", "minimum": 1, "maximum": 10},
                    "museum_name": {"type": "string", "description": "Museum name if this memory is about a specific museum, else null"},
                    "tags": {"type": "array", "items": {"type": "string"}, "description": "Optional categorization tags"}
                },
                "required": ["content", "type", "importance"]
            }
        }
    },
    "required": ["worth_saving", "memories"]
}
```

**Classify-first gate:** The `worth_saving` boolean in the schema serves as a gate. When it's `false`, the `memories` array is empty and nothing is saved. This replaces the old "NONE" string check and prevents the model from generating memories for trivial exchanges like "thanks" or "what time is it?"

**Museum name to museum_id resolution during extraction:** When the model returns a `museum_name`, call `_resolve_museum_id(name)` from Phase M1 to get the FK. If no match, still save the memory with `museum_id=None` but include the museum name in tags.

**Pre-write cosine dedup at 0.92:** The dedup check already exists in `add_memory()` at line 858-878 of `memory_db.py`. It uses `_SEMANTIC_DEDUP_THRESHOLD = 0.92`. This is correct and does not need to change. Verify it fires for Sonnet-extracted memories the same way it does for manual ones.

**Extraction prompt (domain-specific):**

```python
EXTRACTION_PROMPT = """Analyze this conversation exchange between Hermann (founder of AITourPilot, 
a conversational AI audioguide for museums) and his outreach assistant Touri.

Extract facts worth remembering for future outreach sessions. Focus on:
- Contact intelligence: names, roles, preferences, communication styles, response patterns
- Museum intelligence: visitor numbers, current tech stack, budget status, decision-maker structure
- Interactions: emails sent/received, meetings held, demos given, responses and their scores
- Strategy: what outreach angles work, timing insights, template performance, campaign learnings

Rules:
- Each memory must be self-contained (understandable without the conversation context)
- Do NOT save vague summaries like "Discussed Joanneum outreach" -- save the SPECIFIC fact
- Do NOT save what Touri said she would do -- only save what was actually decided or learned
- Include the museum name when the memory relates to a specific museum
- Set importance 8-10 only for permanent facts; use 5-6 for routine interactions

If this exchange is trivial (greetings, thanks, small talk, questions about Touri itself), 
set worth_saving to false and return an empty memories array."""
```

### Safety Invariants

1. **Sonnet cost must be bounded.** The extraction call sends at most `user_message + assistant_response[:1000]` -- the 1000-char truncation of the response is already in the current code and must be preserved.
2. **Extraction must not block the chat loop.** It currently runs synchronously after each response. This is acceptable (Sonnet is fast on short prompts). If latency becomes noticeable, it can be moved to a thread in a later optimization.
3. **Old memories with old types must still appear in search results.** `hybrid_search()` does not filter by type. `list_memories()` accepts any string for `memory_type`. No breakage.
4. **The extraction failure path must be silent.** The existing `except Exception` catch-all on line 296 of session.py must be preserved.

### How to Verify

1. Start a chat session: `python run.py chat`
2. Say: "We just had a demo with Lisa Witschnig at Joanneum. She liked the multilingual feature but was concerned about the 90-day pilot commitment."
3. After Touri responds, check the DB: `sqlite3 data/memory.db "SELECT id, content, type, museum_id, source FROM memories ORDER BY id DESC LIMIT 5"`
4. Expect: at least 2 memories -- one `contact_intel` about Lisa's preferences, one `museum_intel` or `interaction` about the demo. Both should have `museum_id` set to Joanneum's ID in leads.db. Source should be `extraction`.
5. Say something trivial: "Thanks Touri, that's helpful." -- Verify no new memories are saved.
6. Check cost: the extraction call should use `claude-sonnet-4-6` (visible in logs if `verbose: true` in settings).

### Downstream Impact

| Component | Impact | Action Required |
|-----------|--------|----------------|
| `chat_handler.py` | Calls `_extract_and_save_memories()` -- interface unchanged | None |
| `memory_write.py` | `write_memory()` receives new params from extraction | Updated in this phase |
| `memory_curator.py` | Uses old type names for MEMORY.md filtering -- still works | None (update in M6) |
| `personalizer.py` | Searches by museum name text -- still works | Benefits from museum_id filter in M3 |
| Dashboard memory page | Type filter chips show old types only | Phase M6 |
| `args/settings.yaml` | Model changed for extraction | Updated in this phase |

### Risk Areas

1. **#1: Sonnet cost increase.** Extraction switches from Haiku ($0.25/$1.25 per 1M in/out) to Sonnet ($3/$15). Each extraction is ~500 input tokens + ~200 output tokens. At 20 exchanges/day, this adds ~$0.12/day. Over a 30-day campaign: ~$3.60 total. Acceptable given the quality improvement.

2. **#2: JSON schema parsing failure.** If Sonnet returns malformed JSON (unlikely but possible under stress), the extraction crashes. Mitigation: wrap `json.loads()` in try/except, and fall back to saving nothing rather than crashing. Log the raw response for debugging.

### Rollback

1. Revert `session.py` and `settings.yaml` to pre-M2 versions.
2. Old Haiku extraction resumes. New memories already saved with new types remain in DB but cause no harm -- they just show with unfamiliar type labels.

---

## Phase M3: Improved Hybrid Search (RRF + Entity Filtering)

### Goal

Replace the arbitrary 70/30 weighted scoring with Reciprocal Rank Fusion, fix the FTS scoring to use actual BM25 values, add museum_id-filtered search, and fix the session chunk ID type mismatch bug.

### Files to Modify

| File | Function(s) | What Changes |
|------|------------|--------------|
| `tools/memory/memory_db.py` | `hybrid_search()` | Complete rewrite of the scoring section. Accept `museum_id` parameter. |
| `tools/memory/memory_db.py` | `search_memories()` | Accept `museum_id` parameter. Add WHERE clause. Return BM25 rank score. |
| `tools/memory/memory_db.py` | `_vector_search()` | Accept `museum_id` parameter. Add post-filter on results. |
| `tools/memory/memory_db.py` | `_session_fts_search()` | Fix: return BM25 rank value, not ordinal position. |
| `tools/memory/memory_db.py` | `_session_vector_search()` | Fix: session chunk IDs use `"session:N"` string format which collides with integer memory IDs in the merge dict. |
| `tools/memory/memory_db.py` | NEW `_rrf_merge()` | Reciprocal Rank Fusion merging function. |

### What Changes and Why

**Reciprocal Rank Fusion (RRF):** The current scoring on lines 590-612 of memory_db.py uses:
- FTS: ordinal rank position (1st result = 1.0, 2nd = 0.95, etc.) -- this is NOT BM25
- Vector: `(similarity + 1.0) / 2.0` -- a rescaled cosine similarity
- Merge: `0.7 * vec + 0.3 * fts`

The 70/30 weighting is arbitrary and the FTS "score" is meaningless (position 1 vs position 2 tells you nothing about relevance magnitude). RRF fixes this:

```python
def _rrf_merge(ranked_lists: list[list[dict]], k: int = 60) -> list[dict]:
    """Reciprocal Rank Fusion: merge multiple ranked lists into one.
    
    RRF score for document d = sum over lists L of: 1 / (k + rank_L(d))
    where k=60 is the standard constant from Cormack et al. 2009.
    """
    scores = {}   # id -> cumulative RRF score
    docs = {}     # id -> document dict
    
    for ranked_list in ranked_lists:
        for rank, doc in enumerate(ranked_list):
            doc_id = doc["id"]
            rrf_score = 1.0 / (k + rank + 1)  # rank is 0-indexed
            scores[doc_id] = scores.get(doc_id, 0.0) + rrf_score
            if doc_id not in docs:
                docs[doc_id] = doc
    
    result = []
    for doc_id in scores:
        entry = dict(docs[doc_id])
        entry["score"] = round(scores[doc_id], 6)
        result.append(entry)
    
    result.sort(key=lambda x: x["score"], reverse=True)
    return result
```

**Why RRF over 70/30:** RRF is parameter-free (the k=60 constant is stable across domains). It handles the case where a memory ranks #1 in FTS but #50 in vector (or vice versa) gracefully -- the document still gets a reasonable combined score. The 70/30 method would give it a high vec score and zero fts score (or vice versa), losing the signal from one retriever entirely.

**FTS BM25 fix:** SQLite FTS5's `rank` column returns the negative BM25 score (lower = better match). The current code uses it only for ORDER BY, then throws it away and substitutes ordinal position. The fix: use BM25 scores directly in the ranked list (negate them so higher = better), let RRF handle the rank-based merging.

Actually, for RRF the raw scores don't matter -- only the rank ordering matters. So the FTS results just need to be correctly ordered (which `ORDER BY rank` already does). The key change is that we no longer pretend the ordinal position IS the score.

**Museum_id-filtered search:** When the caller knows which museum they're asking about, search should prioritize that museum's memories. Implementation:

```python
def hybrid_search(query, limit=10, include_sessions=True, museum_id=None):
    # ... existing preamble ...
    
    # When museum_id is provided, run two searches:
    # 1. Museum-filtered search (higher priority in RRF)
    # 2. Global search (catches cross-museum strategic insights)
    
    if museum_id:
        museum_fts = search_memories(fts_query, limit=limit*2, museum_id=museum_id)
        museum_vec = _vector_search(query, limit=limit*2, museum_id=museum_id)
        global_fts = search_memories(fts_query, limit=limit)
        global_vec = _vector_search(query, limit=limit)
        
        # RRF with museum-specific results first (they rank higher)
        ranked_lists = [museum_vec, museum_fts, global_vec, global_fts]
    else:
        # ... existing behavior with RRF instead of 70/30 ...
        ranked_lists = [vector_results, fts_results]
    
    if include_sessions:
        ranked_lists.append(session_vec)
        ranked_lists.append(session_fts)
    
    result_list = _rrf_merge(ranked_lists)
```

**Session chunk ID fix:** Session chunks use string IDs like `"session:42"` while memories use integer IDs like `42`. In the current `hybrid_search()`, both are merged into `all_results` dict keyed by `id`. A session chunk with `id="session:42"` and a memory with `id=42` are treated as the same document. Fix: ensure the merge dict handles these correctly. With RRF, this is naturally handled because `doc_id` can be any hashable type.

### Safety Invariants

1. **Search quality must not regress.** RRF should improve or maintain recall/precision. Verify by running the same queries before and after, and checking that the top-5 results are at least as relevant.
2. **The `score` field must still be present in results.** Downstream code checks `r.get("score", 0) < 0.1` to filter low-relevance results (session.py line 228). RRF scores are typically in the 0.001-0.03 range. The threshold check in session.py must be updated to reflect the new score distribution.
3. **MMR and temporal decay must still work.** They operate on the `score` field, which RRF still provides. No changes needed to those functions.
4. **`include_sessions=False` must still work.** The personalizer calls with `include_sessions=True` but other callers may not.

### How to Verify

1. Run `python run.py recall "Joanneum"` -- should return results with RRF scores. Joanneum-tagged memories should rank higher than unrelated ones.
2. Run `python run.py recall "email drafting strategy"` -- should return strategy-type memories from multiple museums.
3. Compare results before/after: save the output of `hybrid_search("Joanneum", limit=10)` before the change, run it after, and verify the top results are the same or better.
4. Check that session chunks and memories don't collide: search for something that appears in both a memory and a session chunk, verify both appear in results with distinct IDs.
5. Programmatic test: `hybrid_search("test", museum_id=1)` returns only museum_id=1 memories in the museum-filtered portion.

### Downstream Impact

| Component | Impact | Action Required |
|-----------|--------|----------------|
| `session.py` `_search_memory_context()` | Score threshold check needs updating (RRF scores are smaller) | Update threshold from 0.1 to 0.005 or remove it |
| `personalizer.py` `_search_museum_memories()` | Score threshold check at 0.1 needs same update | Update threshold |
| `chat_handler.py` | Indirect via `_search_memory_context()` | None directly |
| Dashboard memory search | Uses LIKE, not hybrid_search -- unaffected | None |

### Risk Areas

1. **#1: RRF score scale change breaks downstream filters.** The score threshold `0.1` in `_search_memory_context()` and `personalizer.py` will filter out ALL results because RRF scores are typically 0.001--0.03. This MUST be updated in the same phase.

2. **#2: Museum-filtered search returns too few results.** If a museum has only 2 memories, the museum-filtered search returns only those 2, and the global search may push unrelated results above them in RRF. Mitigation: give museum-filtered results a boost by placing them first in the ranked_lists (RRF naturally weights earlier lists slightly higher since those results tend to rank higher).

### Rollback

1. Revert `memory_db.py` to pre-M3 version.
2. Old 70/30 scoring resumes. Search results may change order but nothing breaks structurally.

---

## Phase M4: Tiered Context Assembly

### Goal

Replace the flat context loading in `session.py` with a 3-tier progressive system that loads the right amount of context based on what the user is doing, and provides loading status messages.

### Files to Modify

| File | Function(s) | What Changes |
|------|------------|--------------|
| `tools/chat/session.py` | `_build_system_prompt()` | Refactor into `_build_tier1_context()`. Always-loaded, lean. |
| `tools/chat/session.py` | NEW `_build_tier2_context(museum_id)` | Museum-specific context: memories, contacts, interaction summary. |
| `tools/chat/session.py` | NEW `_build_tier3_context(museum_id, task_types)` | Full drafting/research context: templates, research doc, detailed history. |
| `tools/chat/session.py` | NEW `_detect_museum(message)` | Fuzzy-match user message against leads.db museum names. Returns museum dict or None. |
| `tools/chat/session.py` | NEW `_count_tokens(text)` | Approximate token count (chars/4) for budget tracking. |
| `tools/chat/session.py` | NEW `_assemble_context(user_message)` | Orchestrator: runs tier detection, assembles tiers, respects token budget, prints loading status. |
| `tools/chat/session.py` | `run_chat()` main loop | Replace inline context assembly with `_assemble_context()` call. |
| `tools/chat/session.py` | `_search_memory_context()` | Accept `museum_id` parameter for filtered search. |
| `tools/chat/session.py` | `_extract_draft_target()` | Refactor to use `_detect_museum()` for consistency. |
| `tools/api/chat_handler.py` | `stream_chat()` `generate()` | Use `_assemble_context()` instead of inline context building. |
| `args/settings.yaml` | `session.context_budget` | Add tier-specific token budgets. |

### What Changes and Why

**Current problem:** `_build_system_prompt()` loads the same context every time: soul.md + USER.md + MEMORY.md + business_context.md + pipeline summary. Then `_search_memory_context()` and `_load_knowledge_for_task()` add more. There's no awareness of:
- Which museum the user is talking about
- Whether the user is drafting (needs templates) or just chatting (doesn't)
- How much token budget has been consumed
- What the user sees while context loads

**Tier 1 (Always Loaded -- ~3K tokens):**
- `soul.md` (identity, principles)
- `memory/USER.md` (Hermann's identity)
- Pipeline summary (compressed one-liner from `pipeline_summary_text()`)
- Top 5 global memories by importance (strategy type, importance >= 8)
- Current date

This replaces the current `_build_system_prompt()`. The key change: MEMORY.md is no longer loaded in full. Instead, the top-5 memories from the DB (by importance) replace the flat file load. MEMORY.md continues to exist for human readability but is no longer injected into the prompt.

**Tier 2 (Museum Detected -- ~2-4K tokens, loaded when user mentions a museum):**
- Museum record from leads.db (name, city, country, stage, tier, score)
- Contact records for that museum
- Museum-specific memories from memory.db (filtered by museum_id)
- Interaction summary (last 3 interactions, not full history)
- Research brief headline (if exists)

Loaded when `_detect_museum()` matches a museum name in the user's message.

**Tier 3 (Drafting/Research -- ~4-8K tokens, loaded when task type detected):**
- Email templates (when drafting)
- Full research document (when researching or drafting)
- Detailed interaction history (when drafting follow-ups)
- Objection handling guide (when scoring responses)
- Personalizer brief (when drafting)

This is essentially the current `_load_knowledge_for_task()` but reorganized and token-budgeted.

**Museum detection:** `_detect_museum()` replaces the current hardcoded `known_museums` dict in `_extract_draft_target()`. Instead, it queries leads.db:

```python
def _detect_museum(message: str) -> dict | None:
    """Fuzzy-match user message against leads.db museum names."""
    try:
        from tools.leads.lead_db import list_museums
        museums = list_museums()  # cached if performance is a concern
        msg_lower = message.lower()
        
        # Check each museum name against the message
        for museum in museums:
            name = museum["name"].lower()
            # Try full name match
            if name in msg_lower:
                return museum
            # Try significant words (skip common words)
            words = [w for w in name.split() if len(w) > 3]
            if words and all(w.lower() in msg_lower for w in words):
                return museum
        
        return None
    except Exception:
        return None
```

**Loading status messages:**

```python
if museum:
    console.print(f"[dim]Loading context for {museum['name']}...[/dim]")
```

This prints to the CLI before the API call, giving Hermann feedback that context is being assembled. For the dashboard, this is emitted as an SSE event.

**Token budget:** Settings.yaml gets new config:

```yaml
session:
  context_budget:
    tier1_max_tokens: 4000
    tier2_max_tokens: 4000
    tier3_max_tokens: 8000
    total_max_tokens: 16000
```

`_count_tokens()` uses `len(text) / 4` as a rough estimate. Each tier truncates its content to fit within its budget. If Tier 2 + Tier 3 would exceed total, Tier 3 is truncated first.

### Safety Invariants

1. **soul.md and USER.md must always be loaded.** They are Tier 1 and non-negotiable.
2. **Business context (business_context.md) must still be loaded.** It moves to Tier 1 as it's always relevant.
3. **The dashboard chat must get the same context as CLI chat.** `_assemble_context()` is called from both `run_chat()` and `chat_handler.py`.
4. **Token counting must be conservative.** Overcount rather than undercount to avoid exceeding API limits.
5. **Museum detection must not produce false positives.** A message like "What museums should I target?" should NOT match a specific museum. The detection requires a specific museum name match, not just the word "museum".

### How to Verify

1. Start chat: `python run.py chat`
2. Say: "What's the status of Joanneum?" -- Should see "[dim]Loading context for Universalmuseum Joanneum...[/dim]" before the response. Response should include museum-specific context.
3. Say: "Draft an email for Georgie Power at SS Great Britain" -- Should load Tier 2 (Great Britain context) + Tier 3 (email templates, personalizer brief).
4. Say: "What's the weather like?" -- Should NOT trigger museum detection. Only Tier 1 loaded.
5. Check token counts: add `print(f"Context: {_count_tokens(system_prompt)} tokens")` temporarily and verify it stays under 16K.

### Downstream Impact

| Component | Impact | Action Required |
|-----------|--------|----------------|
| `chat_handler.py` | Must use new `_assemble_context()` | Updated in this phase |
| `personalizer.py` | `build_context()` still works independently | May benefit from passing museum_id in future |
| `MEMORY.md` | No longer injected into prompt directly; still maintained for human reference | Document in CLAUDE.md |
| `memory_read.py` | `read_memory()` function is no longer called from session.py | Becomes CLI-only utility |

### Risk Areas

1. **#1: Museum detection false positives.** If a museum name is a common word (unlikely but possible), every message could trigger Tier 2 loading. Mitigation: require at least 2 significant words to match, or the full name.

2. **#2: Token budget calculation drift.** The `chars/4` approximation can be off by 20-30%. If the system prompt grows beyond the API's context window, the call fails. Mitigation: set `total_max_tokens` conservatively at 16K (well under the 200K context window). The risk is wasting context space, not overflowing.

### Rollback

1. Revert `session.py` and `chat_handler.py` to pre-M4 versions.
2. Revert `settings.yaml` context_budget changes.
3. Old flat context loading resumes.

---

## Phase M5: Research --> Memory Bridge

### Goal

When the research orchestrator completes, automatically extract key findings and write them as `research`-type memories linked to the museum, so research intelligence is available to hybrid_search and context assembly without loading the full research document.

### Files to Modify

| File | Function(s) | What Changes |
|------|------------|--------------|
| `tools/research/orchestrator.py` | `run_research()` | After `_phase_synthesis()`, call new `_bridge_to_memory()`. |
| `tools/research/orchestrator.py` | NEW `_bridge_to_memory(state)` | Extract key findings from final report, write as memories with type=research and museum_id. |
| `tools/research/orchestrator.py` | NEW `_chunk_research_for_memory(report, museum_id)` | Split research report into memory-sized chunks, each < 500 chars. |
| `tools/outreach/personalizer.py` | `_search_museum_memories()` | Add a direct lookup of research memories by museum_id (in addition to hybrid search). |
| `tools/outreach/personalizer.py` | `build_context()` | Include research memories in the context package. |

### What Changes and Why

**The intelligence silo:** Currently, the research orchestrator writes its final report to:
1. `output/research/YYYYMMDD_slug.md` (markdown file on disk)
2. `leads.db.research` table (insights column, truncated to 10K chars)

Neither of these is searchable by `hybrid_search()`. When Touri assembles context for an email draft, she doesn't find research findings unless the full file is loaded as Tier 3 knowledge. The bridge fixes this by also writing key findings to `memory.db`.

**Implementation:**

```python
def _bridge_to_memory(state: ResearchState) -> None:
    """Extract key findings from research and write to memory.db."""
    if not state.final_report or not state.museum_id:
        return
    
    try:
        from tools.memory.memory_write import write_memory
        from tools.memory.memory_db import _resolve_museum_id
        
        chunks = _chunk_research_for_memory(state.final_report, state.museum_id)
        for chunk in chunks:
            write_memory(
                content=chunk["content"],
                memory_type="research",
                importance=chunk.get("importance", 6),
                museum_id=state.museum_id,
                source="research",
                tags=["research", "auto-bridged"],
            )
        
        _print(f"[{state.session_id}] Bridged {len(chunks)} research findings to memory.db")
    except Exception as e:
        logger.warning("Research->memory bridge failed: %s", e)
```

**Chunking strategy:** The research report is a markdown document typically 2000-5000 chars. Rather than dumping it all as one giant memory, extract the structured sections:

```python
def _chunk_research_for_memory(report: str, museum_id: int) -> list[dict]:
    """Split research report into memory-sized findings."""
    chunks = []
    
    # Strategy 1: Extract bullet-pointed findings
    # Research reports typically have "Key Findings" or "Insights" sections
    # with bullet points. Each bullet becomes one memory.
    
    import re
    bullets = re.findall(r'[-*]\s+(.+)', report)
    for bullet in bullets:
        text = bullet.strip()
        if len(text) > 20 and len(text) < 500:  # skip too-short or too-long
            chunks.append({
                "content": text,
                "importance": 6,
            })
    
    # Strategy 2: If no bullets found, take the first 3 paragraphs
    if not chunks:
        paragraphs = [p.strip() for p in report.split('\n\n') if p.strip() and not p.startswith('#')]
        for p in paragraphs[:5]:
            if len(p) > 30 and len(p) < 500:
                chunks.append({
                    "content": p,
                    "importance": 6,
                })
    
    # Cap at 10 memories per research session to avoid flooding
    return chunks[:10]
```

**Personalizer update:** `_search_museum_memories()` already searches by museum name. After this phase, it will also find `research`-type memories linked by `museum_id`. Additionally, add a direct lookup:

```python
# In _search_museum_memories(), after the existing hybrid searches:
# Direct lookup of research memories for this museum
if museum_name:
    from tools.leads.lead_db import get_museum
    museum = get_museum(museum_name)
    if museum:
        from tools.memory.memory_db import list_memories
        research_mems = list_memories(limit=10, memory_type="research", museum_id=museum["id"])
        for r in research_mems:
            if r["id"] not in seen_ids:
                results.append(r)
                seen_ids.add(r["id"])
```

### Safety Invariants

1. **Research output files must still be written.** The bridge is additive -- it does NOT replace the markdown file or leads.db write.
2. **Bridge failure must not crash research.** The entire `_bridge_to_memory()` is wrapped in try/except. A memory write failure must not affect the research session.
3. **No duplicate memories.** The 0.92 cosine dedup in `add_memory()` prevents duplicate research findings from being saved if research is re-run for the same museum.
4. **Memory flood protection.** Cap at 10 memories per research session. Each memory is < 500 chars.

### How to Verify

1. Run research for a museum: `python run.py chat` then "Research Slot Loevestein" (or via dashboard).
2. After research completes, check: `sqlite3 data/memory.db "SELECT id, type, museum_id, source, content FROM memories WHERE type='research' ORDER BY id DESC LIMIT 10"`
3. Expect: 3-10 research memories with `type=research`, `museum_id` matching Slot Loevestein, `source=research`.
4. In a new chat session: "Draft an email for Nils at Slot Loevestein" -- Touri should reference research findings without needing to load the full research file.
5. Run research again for the same museum -- verify no duplicate memories (dedup should merge similar findings).

### Downstream Impact

| Component | Impact | Action Required |
|-----------|--------|----------------|
| `orchestrator.py` | New code added after synthesis phase | Updated in this phase |
| `personalizer.py` | Now includes research memories | Updated in this phase |
| `memory_db.py` | `list_memories()` needs `museum_id` filter (added in M1) | Already done |
| `session.py` Tier 2 | Research memories appear in museum-specific context automatically | No change needed |

### Risk Areas

1. **#1: Research report format varies.** The chunking relies on bullet points or paragraph structure. If a research report has a non-standard format (tables, code blocks, etc.), the chunking may produce poor results. Mitigation: fall back to paragraph splitting. Accept that some research reports may produce fewer memories.

2. **#2: Memory count explosion.** If research is run frequently for many museums, the memory count could grow rapidly (10 per research * 20 museums = 200 research memories). Mitigation: the dedup check prevents exact duplicates; the 10-per-session cap limits growth; the curator (M6) can expire old research memories when newer research supersedes them.

### Rollback

1. Revert `orchestrator.py` and `personalizer.py` to pre-M5 versions.
2. Research memories already in DB are harmless -- they just won't be created anymore.

---

## Phase M6: Dashboard + Curator Upgrades

### Goal

Update the dashboard UI and API for the new memory schema, fix and activate the curator for auto-expiry and periodic consolidation, and update project documentation.

### Files to Modify

| File | Function(s) | What Changes |
|------|------------|--------------|
| `touri-dashboard/src/lib/types.ts` | `Memory` interface | Add `museum_id`, `tags`, `source` fields. |
| `touri-dashboard/src/lib/db/memory-db.ts` | `getMemories()` | Accept `museum_id` filter parameter. Update SQL to include new columns. |
| `touri-dashboard/src/app/api/memory/route.ts` | `GET` handler | Accept `museum_id` query param. Pass to `getMemories()`. |
| `touri-dashboard/src/app/memory/page.tsx` | Full component | Add museum filter dropdown, new type filter chips, museum name display. |
| `tools/memory/memory_curator.py` | `expire_working_memory()` | Expand to also handle DB-level expiry of low-importance old memories. |
| `tools/memory/memory_curator.py` | NEW `consolidate_memories()` | Merge similar memories (>0.85 cosine) into single entries. |
| `tools/memory/memory_curator.py` | NEW `reclassify_old_types()` | Batch-reclassify old fact/event/insight memories into new type taxonomy. |
| `tools/chat/session.py` | `run_chat()` | Call curator at session start (once per day). |
| `CLAUDE.md` | Project handbook | Update memory system description, new types, new search behavior. |

### What Changes and Why

**Dashboard Memory type update:**

```typescript
// types.ts - UPDATED
export interface Memory {
  id: number;
  content: string;
  type: string;  // now: contact_intel | museum_intel | interaction | strategy | research | general | fact | insight | event | error
  importance: number;
  museum_id: number | null;     // NEW: FK to leads.db museums
  tags: string | null;          // NEW: JSON array string
  source: string | null;        // NEW: extraction | manual | research | cli
  created_at: string;
  updated_at: string;
}
```

**Dashboard memory-db.ts update:**

```typescript
export function getMemories(type?: string, search?: string, museumId?: number): Memory[] {
  // ... existing code ...
  if (museumId) {
    conditions.push('museum_id = ?');
    params.push(String(museumId));
  }
  // ... rest of query ...
}
```

**Dashboard memory page update:**
- Add museum filter dropdown (populated from leads.db museums list)
- Update TYPE_FILTERS to include new types: `contact_intel`, `museum_intel`, `interaction`, `strategy`, `research`, `general`
- Show museum name next to each memory card (when museum_id is set)
- Add source badge (extraction/manual/research/cli)
- Add tags display (parsed from JSON)

**Curator activation:** The curator (`memory_curator.py`) currently only expires entries from MEMORY.md. It has never been called from anywhere. Activate it:

1. **Session-start call:** At the beginning of `run_chat()`, check if the curator has run today. If not, run it.

```python
def _maybe_run_curator():
    """Run curator once per day (check via a simple file timestamp)."""
    flag_path = PROJECT_ROOT / "data" / ".curator_last_run"
    today = datetime.now().strftime("%Y-%m-%d")
    
    if flag_path.exists() and flag_path.read_text().strip() == today:
        return  # already ran today
    
    try:
        from tools.memory.memory_curator import expire_working_memory, consolidate_memories
        expired = expire_working_memory()
        consolidated = consolidate_memories()
        if expired or consolidated:
            logger.info(f"Curator: expired {expired}, consolidated {consolidated}")
        flag_path.write_text(today)
    except Exception as e:
        logger.debug(f"Curator failed: {e}")
```

2. **DB-level expiry:** Extend `expire_working_memory()` to also delete from memory.db memories that are:
   - Older than 90 days (configurable)
   - importance < 5
   - type is `interaction` or `general` (not `strategy` or `museum_intel` which are evergreen)
   - NOT pinned

```python
def expire_db_memories(expiry_days: int = None, min_importance: int = 5) -> int:
    """Delete old low-importance memories from the database."""
    if expiry_days is None:
        expiry_days = _get_expiry_days()
    
    from tools.memory.memory_db import init_db
    conn = init_db()
    try:
        # Only expire interaction and general types; keep strategy and intel
        cursor = conn.execute(
            """DELETE FROM memories 
               WHERE importance < ? 
               AND type IN ('interaction', 'general', 'event')
               AND created_at < datetime('now', ?)
               AND content NOT LIKE '%PINNED:%'""",
            (min_importance, f"-{expiry_days} days"),
        )
        deleted = cursor.rowcount
        conn.commit()
        return deleted
    finally:
        conn.close()
```

3. **Consolidation:** Find memories with cosine similarity > 0.85 and merge them:

```python
def consolidate_memories() -> int:
    """Merge highly similar memories into single entries."""
    from tools.memory.memory_db import init_db, _vector_search, _get_embedding, _cosine_similarity
    
    conn = init_db()
    all_mems = conn.execute(
        "SELECT id, content, type, importance, museum_id FROM memories ORDER BY importance DESC"
    ).fetchall()
    conn.close()
    
    merged = 0
    skip_ids = set()
    
    for i, (id1, content1, type1, imp1, mid1) in enumerate(all_mems):
        if id1 in skip_ids:
            continue
        for j in range(i + 1, len(all_mems)):
            id2, content2, type2, imp2, mid2 = all_mems[j]
            if id2 in skip_ids:
                continue
            if mid1 != mid2:  # only merge within same museum
                continue
            
            # Quick text check before expensive embedding comparison
            if _text_jaccard(content1, content2) < 0.3:
                continue
            
            vec1, _ = _get_embedding(content1)
            vec2, _ = _get_embedding(content2)
            if vec1 and vec2 and _cosine_similarity(vec1, vec2) > 0.85:
                # Keep the higher-importance one, delete the other
                keep_id = id1 if imp1 >= imp2 else id2
                delete_id = id2 if keep_id == id1 else id1
                from tools.memory.memory_db import delete_memory
                delete_memory(delete_id)
                skip_ids.add(delete_id)
                merged += 1
    
    return merged
```

4. **Old type reclassification (optional, manual trigger):** A one-time function to reclassify existing memories with old types into the new taxonomy. This uses a quick LLM call per memory:

```python
def reclassify_old_types() -> int:
    """Reclassify old fact/event/insight/error memories into new type taxonomy.
    
    Called manually: python -c "from tools.memory.memory_curator import reclassify_old_types; print(reclassify_old_types())"
    """
    # Implementation: batch old-type memories, send to Haiku for classification
    # (Haiku is fine here since it's just classification, not extraction)
    pass  # Implement if/when the old types become a problem
```

This is marked as optional. The old types don't break anything; they just show as unfamiliar labels. Over time, new extraction creates only new types, and the old ones fade via expiry.

**CLAUDE.md update:** Update the "Architecture" section to reflect:
- New memory types
- Museum_id linkage
- Sonnet extraction
- Tiered context assembly
- Research bridge

### Safety Invariants

1. **Curator must never delete memories with importance >= 8.** These are high-value facts that should be preserved indefinitely.
2. **Consolidation must only merge within the same museum_id.** Cross-museum merging would lose context.
3. **Dashboard changes must not break if TOURIBOT_HOME is not set.** The memory-db.ts already handles this gracefully.
4. **MEMORY.md must still be maintained.** The curator's expiry of MEMORY.md entries continues to work as before.

### How to Verify

1. **Dashboard:** Start dashboard (`cd touri-dashboard && npm run dev`), navigate to Memory page. Verify:
   - New type filter chips appear (contact_intel, museum_intel, etc.)
   - Museum filter dropdown shows museum list
   - Filtering by museum shows only that museum's memories
   - Memory cards show source badge and tags
2. **Curator:** `python -c "from tools.memory.memory_curator import expire_working_memory, consolidate_memories; print(expire_working_memory()); print(consolidate_memories())"` -- runs without error, returns counts.
3. **Session start:** `python run.py chat`, check that curator runs silently (no error output). Verify `.curator_last_run` file is created.
4. **CLAUDE.md:** Read it and verify it accurately describes the new system.

### Downstream Impact

| Component | Impact | Action Required |
|-----------|--------|----------------|
| All Python memory consumers | No change -- they already handle new columns from M1 | None |
| Dashboard memory page | Complete refresh | Updated in this phase |
| Dashboard API routes | New query params | Updated in this phase |
| Dashboard types.ts | New fields on Memory interface | Updated in this phase |
| CLAUDE.md | Updated description | Updated in this phase |

### Risk Areas

1. **#1: Consolidation is O(n^2) on memory count.** With 200+ memories, the pairwise comparison could be slow (200*200 = 40K comparisons, each requiring an embedding lookup). Mitigation: the embedding cache means most lookups are fast (hash match). Add a progress counter and a max iteration limit (e.g., stop after 1000 comparisons).

2. **#2: Dashboard type rendering for mixed old/new types.** If old memories have type `fact` and new ones have `museum_intel`, the dashboard must handle both. Mitigation: the TYPE_COLORS map includes both old and new types with fallback styling.

### Rollback

1. Revert all dashboard files to pre-M6 versions.
2. Revert `memory_curator.py` and `session.py` curator-call changes.
3. Revert `CLAUDE.md` changes.

---

## Implementation Order and Dependencies

```
Phase M1  ──→  Phase M2  ──→  Phase M3  ──→  Phase M4
(Schema)       (Extraction)    (Search)        (Context)
                                                  │
                                                  ├──→  Phase M5
                                                  │     (Research Bridge)
                                                  │
                                                  └──→  Phase M6
                                                        (Dashboard + Curator)
```

- M1 is a prerequisite for all other phases (new columns must exist).
- M2 depends on M1 (extraction writes museum_id, which must exist in schema).
- M3 depends on M1 (museum_id-filtered search uses the new column).
- M4 depends on M3 (tiered context uses the improved search).
- M5 depends on M1 and M4 (research bridge writes museum_id; personalizer uses tiered context).
- M6 depends on M1 (dashboard reads new columns) and can run in parallel with M4/M5.

**Recommended execution order:** M1 -> M2 -> M3 -> M4 -> M5 -> M6

Each phase is a single commit with the prefix `Memory 2.0 Phase MX:`.

---

## Settings.yaml Changes Summary

All settings.yaml changes across all phases, consolidated:

```yaml
# ── Changes to args/settings.yaml ──

# M2: Switch extraction model to Sonnet
models:
  memory_extraction:
    model: claude-sonnet-4-6     # was: claude-haiku-4-5-20251001
    max_tokens: 1024              # was: 1024 in settings, 512 in code (fix mismatch)
    temperature: 0.2              # was: 0.3

# M3: Search settings (RRF replaces 70/30, these are informational)
search:
  rrf:
    k: 60                         # NEW: RRF constant
  query_expansion:
    enabled: true                 # unchanged
  temporal_decay:
    enabled: true                 # unchanged
    half_life_days: 30            # unchanged
    evergreen_min_importance: 9   # unchanged
  mmr:
    enabled: true                 # unchanged
    lambda: 0.7                   # unchanged

# M4: Tiered context budget
session:
  context_budget:
    tier1_max_tokens: 4000        # NEW
    tier2_max_tokens: 4000        # NEW
    tier3_max_tokens: 8000        # NEW
    total_max_tokens: 16000       # NEW

# M6: Curator settings
memory:
  curator:
    enabled: true                 # NEW
    expire_db_min_importance: 5   # NEW: only expire memories below this
    consolidation_threshold: 0.85 # NEW: cosine similarity for merging
    expire_types:                 # NEW: only these types get expired
      - interaction
      - general
      - event
```

---

## Effort Estimates

| Phase | Estimated Hours | Confidence | Primary Risk |
|-------|----------------|------------|--------------|
| M1: Schema Migration | 3-4h | High | Backfill regex matching |
| M2: Sonnet Extraction | 4-5h | Medium | JSON schema parsing edge cases |
| M3: RRF Search | 3-4h | High | Score threshold downstream updates |
| M4: Tiered Context | 5-7h | Medium | Museum detection accuracy |
| M5: Research Bridge | 2-3h | High | Report chunking quality |
| M6: Dashboard + Curator | 4-6h | Medium | Consolidation performance |
| **Total** | **21-29h** | | |

---

## Open Questions (Decide Before Implementation)

1. **Should old memories be batch-reclassified to new types?** The plan marks this as optional. If Hermann wants a clean type taxonomy from day one, run the reclassifier. If he's OK with old types fading naturally, skip it.

2. **Should the dashboard memory page support editing/deleting memories?** The current plan adds read-only display of new columns. Write operations (delete junk, edit content) would require a new API endpoint on the Python FastAPI server. Defer to a follow-up if needed.

3. **Should the research bridge run automatically or require opt-in?** The plan assumes automatic (every research session bridges to memory). If cost/noise is a concern, add a flag: `python run.py research "query" --bridge-to-memory`.

---

*This document is the implementation blueprint for Memory System 2.0. Each phase is independently verifiable, rollback-safe, and scoped to specific files. When all 6 phases are complete, move this file to `docs_dev/completed/20260409_MEMORY_SYSTEM_2_0.md`.*
