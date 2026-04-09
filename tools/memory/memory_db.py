#!/usr/bin/env python3
"""
Memory Database - CRUD operations for persistent memory

Usage:
    python memory_db.py --action add --content "text" [--type fact] [--importance 5]
    python memory_db.py --action search --query "keyword"
    python memory_db.py --action list [--limit 20]
    python memory_db.py --action delete --id 123
    python memory_db.py --action stats

Arguments:
    --action: Operation to perform (add, search, list, delete, stats)
    --content: Text content for add operation
    --query: Search query for search operation
    --type: Memory type (event, fact, insight, error) - default: fact
    --importance: Importance score 1-10 - default: 5
    --limit: Max results for list/search - default: 20
    --id: Memory ID for delete operation
"""

import argparse
import json
import logging
import re
import sqlite3
import struct
import sys
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)

# Database path — relative to project root
DB_PATH = Path(__file__).parent.parent.parent / "data" / "memory.db"

# Leads database path (separate SQLite file for museum pipeline data)
LEADS_DB_PATH = Path(__file__).parent.parent.parent / "data" / "leads.db"

# Vector dimension for vec0 tables (all-MiniLM-L6-v2 outputs 384-dim)
_VEC_DIM = 384
# Module-level flag: migration runs once per process lifetime
_vec_migration_done = False
# Settings cache: loaded once from settings.yaml
_search_settings_cache = None

# ── English stop words for query expansion ───────
_STOP_WORDS = frozenset({
    "a", "an", "the", "and", "or", "but", "in", "on", "at", "to", "for",
    "of", "with", "by", "from", "is", "was", "are", "were", "be", "been",
    "being", "have", "has", "had", "do", "does", "did", "that", "this",
    "it", "we", "you", "he", "she", "they", "me", "my", "your", "his",
    "her", "our", "their", "what", "which", "who", "when", "where", "how",
    "why", "about", "not", "no", "so", "if", "then", "than", "up", "out",
    "as", "into", "during", "before", "after", "above", "below", "between",
    "each", "more", "most", "some", "can", "could", "would", "should",
    "may", "might", "will", "also", "just", "very", "like", "please",
    "tell", "its", "any", "all", "there", "here",
})

# ── Privacy redaction patterns ───────────────────────────────────────
_PRIVACY_PATTERNS = [
    re.compile(r'\b(sk|pk|rk|ek|ak)-[A-Za-z0-9_-]{20,}\b'),       # API keys (sk-..., pk-...)
    re.compile(r'\bxox[bpoa]-[A-Za-z0-9_-]+'),                      # Slack tokens
    re.compile(r'\bghp_[A-Za-z0-9]{36}\b'),                         # GitHub PATs
    re.compile(r'\bey[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+'),  # JWTs
    re.compile(r'(?i)(?:password|passwd|pwd|secret|api[_-]?key|auth[_-]?token)\s*[=:]\s*\S+'),
]


def _privacy_redact(text: str) -> str:
    """Strip common sensitive patterns (API keys, tokens)."""
    for pat in _PRIVACY_PATTERNS:
        text = pat.sub('[REDACTED]', text)
    return text


def _try_load_vec(conn: sqlite3.Connection) -> bool:
    """Load sqlite-vec extension into an open connection. Returns True if successful."""
    try:
        import sqlite_vec
        conn.enable_load_extension(True)
        sqlite_vec.load(conn)
        conn.enable_load_extension(False)
        return True
    except Exception:
        return False


def init_db():
    """Initialize database with schema if needed, including FTS5 full-text index."""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS memories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            content TEXT NOT NULL,
            type TEXT DEFAULT 'fact',
            importance INTEGER DEFAULT 5,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_type ON memories(type)
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_importance ON memories(importance DESC)
    """)

    # FTS5 virtual table for full-text search
    cursor.execute("""
        CREATE VIRTUAL TABLE IF NOT EXISTS memories_fts
        USING fts5(content, content=memories, content_rowid=id)
    """)

    # Embeddings table for vector search
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS memory_embeddings (
            memory_id INTEGER PRIMARY KEY,
            embedding BLOB NOT NULL,
            dim INTEGER NOT NULL,
            model TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Triggers to keep FTS in sync with memories table
    cursor.execute("""
        CREATE TRIGGER IF NOT EXISTS memories_ai AFTER INSERT ON memories BEGIN
            INSERT INTO memories_fts(rowid, content) VALUES (new.id, new.content);
        END
    """)
    cursor.execute("""
        CREATE TRIGGER IF NOT EXISTS memories_au AFTER UPDATE ON memories BEGIN
            DELETE FROM memories_fts WHERE rowid = old.id;
            INSERT INTO memories_fts(rowid, content) VALUES (new.id, new.content);
        END
    """)
    cursor.execute("""
        CREATE TRIGGER IF NOT EXISTS memories_ad AFTER DELETE ON memories BEGIN
            DELETE FROM memories_fts WHERE rowid = old.id;
        END
    """)

    # Session transcript chunks for cross-session search
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS session_chunks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL,
            chunk_index INTEGER NOT NULL,
            content TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_session_chunks_session
        ON session_chunks (session_id)
    """)

    # FTS5 for session chunks
    cursor.execute("""
        CREATE VIRTUAL TABLE IF NOT EXISTS session_chunks_fts
        USING fts5(content, content=session_chunks, content_rowid=id)
    """)

    # Triggers to keep session chunk FTS in sync
    cursor.execute("""
        CREATE TRIGGER IF NOT EXISTS session_chunks_ai AFTER INSERT ON session_chunks BEGIN
            INSERT INTO session_chunks_fts(rowid, content) VALUES (new.id, new.content);
        END
    """)
    cursor.execute("""
        CREATE TRIGGER IF NOT EXISTS session_chunks_ad AFTER DELETE ON session_chunks BEGIN
            DELETE FROM session_chunks_fts WHERE rowid = old.id;
        END
    """)

    # Embeddings for session chunks
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS session_chunk_embeddings (
            chunk_id INTEGER PRIMARY KEY,
            embedding BLOB NOT NULL,
            dim INTEGER NOT NULL,
            model TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Embedding cache: avoid re-computing embeddings for identical text
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS embedding_cache (
            model TEXT NOT NULL,
            content_hash TEXT NOT NULL,
            embedding BLOB NOT NULL,
            dim INTEGER NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (model, content_hash)
        )
    """)

    # sqlite-vec accelerated vector search (vec0 virtual tables)
    if _try_load_vec(conn):
        try:
            cursor.execute(f"""
                CREATE VIRTUAL TABLE IF NOT EXISTS vec_memories
                USING vec0(memory_id INTEGER PRIMARY KEY, embedding FLOAT[{_VEC_DIM}])
            """)
            cursor.execute(f"""
                CREATE VIRTUAL TABLE IF NOT EXISTS vec_session_chunks
                USING vec0(chunk_id INTEGER PRIMARY KEY, embedding FLOAT[{_VEC_DIM}])
            """)
            _migrate_once(conn)
        except Exception as e:
            logger.debug(f"vec0 table setup failed (falling back to blob search): {e}")

    # ── Phase M1: add museum_id, tags, source columns (idempotent) ────────
    for sql in [
        "ALTER TABLE memories ADD COLUMN museum_id INTEGER",
        "ALTER TABLE memories ADD COLUMN tags TEXT",
        "ALTER TABLE memories ADD COLUMN source TEXT",
    ]:
        try:
            cursor.execute(sql)
        except Exception:
            pass  # column already exists on subsequent runs

    try:
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_memories_museum_id ON memories(museum_id)"
        )
    except Exception:
        pass

    conn.commit()

    # Backfill museum_id from [MUSEUM: X] text tags (idempotent)
    _migrate_memories_v2(conn)

    return conn


def _resolve_museum_id(name: str):
    """Resolve a museum name to its integer ID in leads.db.

    Opens a READ-ONLY connection to leads.db and does a case-insensitive
    LIKE match against museums.name.

    Returns int museum_id or None if:
    - leads.db does not exist
    - no match is found
    (multiple matches: first row by ID is used)
    """
    try:
        if not LEADS_DB_PATH.exists():
            return None
        conn = sqlite3.connect(f"file:{LEADS_DB_PATH}?mode=ro", uri=True)
        row = conn.execute(
            "SELECT id FROM museums WHERE LOWER(name) LIKE ? ORDER BY id ASC LIMIT 1",
            (f"%{name.lower()}%",),
        ).fetchone()
        conn.close()
        return int(row[0]) if row else None
    except Exception:
        return None


def _migrate_memories_v2(conn: sqlite3.Connection):
    """Idempotent backfill: set museum_id from [MUSEUM: X] text tags.

    Only processes rows where museum_id IS NULL and content contains a
    [MUSEUM: ...] tag.  Logs any memories where the tag was found but no
    matching museum exists in leads.db.
    """
    try:
        rows = conn.execute(
            "SELECT id, content FROM memories WHERE museum_id IS NULL AND content LIKE '%[MUSEUM:%'"
        ).fetchall()
    except Exception as e:
        logger.debug(f"_migrate_memories_v2 query failed: {e}")
        return

    pattern = re.compile(r'\[MUSEUM:\s*(.+?)\]')
    updated = 0
    unmatched = []

    for mem_id, content in rows:
        match = pattern.search(content)
        if not match:
            continue
        museum_name = match.group(1).strip()
        museum_id = _resolve_museum_id(museum_name)
        if museum_id is not None:
            try:
                conn.execute(
                    "UPDATE memories SET museum_id = ? WHERE id = ?",
                    (museum_id, mem_id),
                )
                updated += 1
            except Exception as e:
                logger.debug(f"Failed to update museum_id for memory {mem_id}: {e}")
        else:
            unmatched.append((mem_id, museum_name))

    if updated:
        conn.commit()
        logger.info(f"_migrate_memories_v2: backfilled museum_id for {updated} memories")

    for mem_id, museum_name in unmatched:
        logger.debug(
            f"_migrate_memories_v2: memory {mem_id} has [MUSEUM: {museum_name}] but no match in leads.db"
        )


def _migrate_once(conn: sqlite3.Connection):
    """Migrate existing blob embeddings into vec0 tables. Runs once per process."""
    global _vec_migration_done
    if _vec_migration_done:
        return
    _vec_migration_done = True

    try:
        rows = conn.execute("""
            SELECT e.memory_id, e.embedding FROM memory_embeddings e
            LEFT JOIN vec_memories v ON v.memory_id = e.memory_id
            WHERE v.memory_id IS NULL AND e.dim = ?
        """, (_VEC_DIM,)).fetchall()
        for memory_id, emb_blob in rows:
            try:
                conn.execute(
                    "INSERT INTO vec_memories(memory_id, embedding) VALUES (?, ?)",
                    (memory_id, emb_blob),
                )
            except Exception:
                pass
        if rows:
            logger.debug(f"Migrated {len(rows)} memory embeddings to vec0")
    except Exception as e:
        logger.debug(f"Memory vec0 migration failed: {e}")

    try:
        rows = conn.execute("""
            SELECT e.chunk_id, e.embedding FROM session_chunk_embeddings e
            LEFT JOIN vec_session_chunks v ON v.chunk_id = e.chunk_id
            WHERE v.chunk_id IS NULL AND e.dim = ?
        """, (_VEC_DIM,)).fetchall()
        for chunk_id, emb_blob in rows:
            try:
                conn.execute(
                    "INSERT INTO vec_session_chunks(chunk_id, embedding) VALUES (?, ?)",
                    (chunk_id, emb_blob),
                )
            except Exception:
                pass
        if rows:
            logger.debug(f"Migrated {len(rows)} session chunk embeddings to vec0")
    except Exception as e:
        logger.debug(f"Session chunk vec0 migration failed: {e}")


def migrate_to_vec():
    """Public: migrate all existing blob embeddings to vec0 tables."""
    global _vec_migration_done
    _vec_migration_done = False
    conn = init_db()
    conn.commit()
    conn.close()
    logger.info("migrate_to_vec: complete")


def rebuild_fts():
    """Rebuild FTS5 index from memories table."""
    conn = init_db()
    conn.execute("INSERT INTO memories_fts(memories_fts) VALUES('rebuild')")
    conn.commit()
    conn.close()


# ── Embedding & Vector Search ──────────────────

# Lazy-loaded embedding model singleton
_embedding_model = None
_embedding_model_name = None
_embedding_tried_init = False


def _init_embedding_model():
    """Initialize embedding model: local sentence-transformers preferred."""
    global _embedding_model, _embedding_model_name, _embedding_tried_init
    if _embedding_tried_init:
        return
    _embedding_tried_init = True

    try:
        from sentence_transformers import SentenceTransformer
        _embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        _embedding_model_name = 'all-MiniLM-L6-v2'
        logger.info("Embedding model loaded: all-MiniLM-L6-v2 (local)")
        return
    except ImportError:
        logger.debug("sentence-transformers not available")
    except Exception as e:
        logger.debug(f"sentence-transformers load failed: {e}")

    _embedding_model_name = None


def _get_embedding(text: str):
    """Generate embedding vector. Returns (list_of_floats, model_name) or (None, None)."""
    import hashlib
    content_hash = hashlib.sha256(text.encode()).hexdigest()

    # Check embedding cache first
    try:
        conn = sqlite3.connect(DB_PATH)
        row = conn.execute(
            "SELECT embedding, dim, model FROM embedding_cache WHERE content_hash = ?",
            (content_hash,),
        ).fetchone()
        conn.close()
        if row:
            emb_blob, dim, model_name = row
            return _deserialize_embedding(emb_blob, dim), model_name
    except Exception:
        pass

    # Generate embedding
    _init_embedding_model()

    vec, model_name = None, None
    if _embedding_model is not None:
        vec = _embedding_model.encode(text).tolist()
        model_name = _embedding_model_name

    if vec and model_name:
        try:
            blob = _serialize_embedding(vec)
            conn = sqlite3.connect(DB_PATH)
            conn.execute(
                "INSERT OR REPLACE INTO embedding_cache "
                "(model, content_hash, embedding, dim, created_at) VALUES (?, ?, ?, ?, ?)",
                (model_name, content_hash, blob, len(vec), datetime.now().isoformat()),
            )
            conn.commit()
            conn.close()
        except Exception:
            pass

    return vec, model_name


def _serialize_embedding(vec: list) -> bytes:
    """Serialize float list to compact binary format."""
    return struct.pack(f'{len(vec)}f', *vec)


def _deserialize_embedding(blob: bytes, dim: int) -> list:
    """Deserialize binary embedding back to float list."""
    return list(struct.unpack(f'{dim}f', blob))


def _cosine_similarity(a: list, b: list) -> float:
    """Pure Python cosine similarity (no numpy required)."""
    if len(a) != len(b):
        return 0.0
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = sum(x * x for x in a) ** 0.5
    norm_b = sum(x * x for x in b) ** 0.5
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


def _save_embedding(memory_id: int, embedding: list, model_name: str):
    """Store embedding for a memory. Upserts if already exists."""
    conn = init_db()
    blob = _serialize_embedding(embedding)
    conn.execute(
        "INSERT OR REPLACE INTO memory_embeddings (memory_id, embedding, dim, model, created_at) "
        "VALUES (?, ?, ?, ?, ?)",
        (memory_id, blob, len(embedding), model_name, datetime.now().isoformat()),
    )
    if len(embedding) == _VEC_DIM:
        try:
            conn.execute("DELETE FROM vec_memories WHERE memory_id = ?", (memory_id,))
            conn.execute(
                "INSERT INTO vec_memories(memory_id, embedding) VALUES (?, ?)",
                (memory_id, blob),
            )
        except Exception as e:
            logger.debug(f"vec0 upsert failed for memory {memory_id}: {e}")
    conn.commit()
    conn.close()


def _embed_on_write(memory_id: int, content: str):
    """Generate and store embedding for a newly written memory. Silent on failure."""
    try:
        vec, model_name = _get_embedding(content)
        if vec:
            _save_embedding(memory_id, vec, model_name)
    except Exception as e:
        logger.debug(f"Embedding generation skipped for memory {memory_id}: {e}")


def _vector_search(query: str, limit: int = 20, museum_id: int = None) -> list:
    """Find memories by vector similarity. Uses sqlite-vec vec0 if available, else blob loop.

    Args:
        query: Search query string.
        limit: Maximum number of results to return.
        museum_id: Optional post-filter — only keep results whose museum_id matches.
                   The vec0 KNN query does not support WHERE on non-embedding columns,
                   so filtering is done in Python after retrieval.
    """
    query_vec, _ = _get_embedding(query)
    if query_vec is None:
        return []

    # Fetch more rows than needed so post-filtering still returns enough results
    fetch_limit = limit * 3 if museum_id is not None else limit

    conn = init_db()

    # Try sqlite-vec accelerated search
    if len(query_vec) == _VEC_DIM:
        try:
            query_blob = _serialize_embedding(query_vec)
            rows = conn.execute("""
                SELECT v.memory_id, v.distance, m.content, m.type, m.importance, m.created_at,
                       m.museum_id, m.tags, m.source
                FROM vec_memories v
                JOIN memories m ON m.id = v.memory_id
                WHERE v.embedding MATCH ? AND k = ?
                ORDER BY v.distance
            """, (query_blob, fetch_limit)).fetchall()
            conn.close()
            results = []
            for mem_id, distance, content, mtype, importance, created_at, mid, tags, src in rows:
                similarity = max(0.0, 1.0 - (distance * distance) / 2.0)
                results.append({
                    "id": mem_id, "content": content, "type": mtype,
                    "importance": importance, "created_at": created_at,
                    "museum_id": mid, "tags": tags, "source": src,
                    "similarity": similarity,
                })
            if museum_id is not None:
                results = [r for r in results if r.get("museum_id") == museum_id]
            return results[:limit]
        except Exception as e:
            logger.debug(f"vec0 memory search fell back to blob loop: {e}")

    # Fallback: Python cosine loop over all stored blobs
    cursor = conn.cursor()
    cursor.execute("""
        SELECT e.memory_id, e.embedding, e.dim, m.content, m.type, m.importance, m.created_at,
               m.museum_id, m.tags, m.source
        FROM memory_embeddings e
        JOIN memories m ON m.id = e.memory_id
    """)
    results = []
    for row in cursor.fetchall():
        mem_id, emb_blob, dim, content, mtype, importance, created_at, mid, tags, src = row
        stored_vec = _deserialize_embedding(emb_blob, dim)
        similarity = _cosine_similarity(query_vec, stored_vec)
        results.append({
            "id": mem_id, "content": content, "type": mtype,
            "importance": importance, "created_at": created_at,
            "museum_id": mid, "tags": tags, "source": src,
            "similarity": similarity,
        })
    conn.close()
    results.sort(key=lambda x: x["similarity"], reverse=True)
    if museum_id is not None:
        results = [r for r in results if r.get("museum_id") == museum_id]
    return results[:limit]


def _get_search_settings() -> dict:
    """Return the `search:` section from settings.yaml (cached after first load)."""
    global _search_settings_cache
    if _search_settings_cache is not None:
        return _search_settings_cache
    try:
        import yaml
        settings_path = Path(__file__).parent.parent.parent / "args" / "settings.yaml"
        with open(settings_path) as f:
            full = yaml.safe_load(f)
        _search_settings_cache = full.get("search", {}) if full else {}
    except Exception:
        _search_settings_cache = {}
    return _search_settings_cache


def _expand_query(query: str) -> str:
    """Extract meaningful keywords and OR-join them for broader FTS5 matching."""
    q = query.strip()
    q_upper = f" {q.upper()} "
    if '"' in q or '*' in q or any(f" {kw} " in q_upper for kw in ("AND", "OR", "NOT")):
        return q

    tokens = [t.strip(".,!?;:'-\"") for t in q.lower().split()]
    keywords = [t for t in tokens if t and len(t) >= 3 and t not in _STOP_WORDS]

    if len(keywords) >= 2:
        return " OR ".join(keywords)
    return q


def _text_jaccard(text1: str, text2: str) -> float:
    """Jaccard word-set similarity between two text strings."""
    w1 = set(text1.lower().split())
    w2 = set(text2.lower().split())
    if not w1 or not w2:
        return 0.0
    return len(w1 & w2) / len(w1 | w2)


def _apply_temporal_decay(results: list, half_life_days: int, evergreen_min_importance: int) -> list:
    """Multiply each result's score by an exponential decay factor based on age."""
    import math
    if half_life_days <= 0:
        return results

    lam = math.log(2) / half_life_days
    now = datetime.now()
    decayed = []
    for r in results:
        if r.get("importance", 5) >= evergreen_min_importance:
            decayed.append(r)
            continue
        try:
            raw_ts = r.get("created_at", "")
            ts = datetime.fromisoformat(raw_ts.replace("Z", "+00:00")).replace(tzinfo=None)
            age_days = max(0, (now - ts).days)
            factor = math.exp(-lam * age_days)
            entry = dict(r)
            entry["score"] = round(r.get("score", 0.0) * factor, 4)
            decayed.append(entry)
        except Exception:
            decayed.append(r)

    decayed.sort(key=lambda x: x.get("score", 0.0), reverse=True)
    return decayed


def _apply_mmr(scored: list, mmr_lambda: float, limit: int) -> list:
    """Maximal Marginal Relevance re-ranking."""
    if len(scored) <= limit:
        return scored

    remaining = list(scored)
    selected = []

    while len(selected) < limit and remaining:
        if not selected:
            best = max(remaining, key=lambda r: r.get("score", 0.0))
        else:
            best, best_mmr = None, float("-inf")
            for r in remaining:
                rel = r.get("score", 0.0)
                max_sim = max(_text_jaccard(r["content"], s["content"]) for s in selected)
                mmr_score = mmr_lambda * rel - (1.0 - mmr_lambda) * max_sim
                if mmr_score > best_mmr:
                    best_mmr, best = mmr_score, r
        selected.append(best)
        remaining.remove(best)

    return selected


def _rrf_merge(ranked_lists: list, k: int = 60) -> list:
    """Reciprocal Rank Fusion: merge multiple ranked lists into one.

    RRF score for document d = sum over lists L of: 1 / (k + rank_L(d))
    where k=60 is the standard constant from Cormack et al. 2009.

    Each ranked_list must be a list of dicts with an "id" key.
    The id can be any hashable type (int for memories, str like "session:N" for chunks).
    """
    scores: dict = {}   # id -> cumulative RRF score
    docs: dict = {}     # id -> document dict

    for ranked_list in ranked_lists:
        for rank, doc in enumerate(ranked_list):
            doc_id = doc["id"]
            rrf_score = 1.0 / (k + rank + 1)  # rank is 0-indexed
            scores[doc_id] = scores.get(doc_id, 0.0) + rrf_score
            if doc_id not in docs:
                docs[doc_id] = doc

    result = []
    for doc_id, cumulative_score in scores.items():
        entry = dict(docs[doc_id])
        entry["score"] = round(cumulative_score, 6)
        result.append(entry)

    result.sort(key=lambda x: x["score"], reverse=True)
    return result


def hybrid_search(query: str, limit: int = 10, include_sessions: bool = True,
                  museum_id: int = None) -> list:
    """Hybrid search using Reciprocal Rank Fusion (RRF) over vector + FTS5 results.

    Merges ranked lists from multiple retrievers (vector search, FTS5, session chunks)
    using RRF instead of a fixed 70/30 weighted score. RRF scores are in the range
    ~0.001–0.03 (much smaller than the old 0–1 range).

    When museum_id is provided, runs two parallel searches:
      - Museum-filtered search (higher priority by appearing first in ranked_lists)
      - Global search (catches cross-museum strategic insights)

    Args:
        query: Search query string.
        limit: Maximum number of results (default 10).
        include_sessions: Include session transcript chunks (default True).
        museum_id: Optional — prioritise memories for this museum.
    """
    settings = _get_search_settings()

    qe_cfg = settings.get("query_expansion", {})
    fts_query = _expand_query(query) if qe_cfg.get("enabled", False) else query

    # ── Build ranked lists for RRF ────────────────────────────────────────
    ranked_lists: list = []

    if museum_id is not None:
        # Museum-specific lists first (RRF naturally boosts docs that appear
        # in multiple lists; placing museum lists first gives them a slight edge
        # when there is a tie in rank position)
        museum_vec = _vector_search(query, limit=limit * 2, museum_id=museum_id)
        museum_fts = search_memories(fts_query, limit=limit * 2, museum_id=museum_id)
        global_vec = _vector_search(query, limit=limit)
        global_fts = search_memories(fts_query, limit=limit)
        for r in museum_vec + museum_fts + global_vec + global_fts:
            r.setdefault("source", "memory")
        ranked_lists = [museum_vec, museum_fts, global_vec, global_fts]
    else:
        vec_results = _vector_search(query, limit=limit * 2)
        fts_results = search_memories(fts_query, limit=limit * 2)
        for r in vec_results + fts_results:
            r.setdefault("source", "memory")
        ranked_lists = [vec_results, fts_results]

    if include_sessions:
        session_vec = _session_vector_search(query, limit=limit)
        session_fts = _session_fts_search(fts_query, limit=limit)
        for r in session_vec + session_fts:
            r.setdefault("source", "session")
        ranked_lists.append(session_vec)
        ranked_lists.append(session_fts)

    # ── RRF merge ─────────────────────────────────────────────────────────
    result_list = _rrf_merge(ranked_lists)

    # ── Post-processing (temporal decay, MMR) — operate on score field ────
    td_cfg = settings.get("temporal_decay", {})
    if td_cfg.get("enabled", False):
        result_list = _apply_temporal_decay(
            result_list,
            half_life_days=td_cfg.get("half_life_days", 30),
            evergreen_min_importance=td_cfg.get("evergreen_min_importance", 9),
        )

    mmr_cfg = settings.get("mmr", {})
    if mmr_cfg.get("enabled", False):
        result_list = _apply_mmr(result_list, mmr_lambda=mmr_cfg.get("lambda", 0.7), limit=limit)

    return result_list[:limit]


def get_memory_stats() -> dict:
    """Return a stats summary of the memory database."""
    conn = init_db()
    try:
        total = conn.execute("SELECT COUNT(*) FROM memories").fetchone()[0]
        avg_imp = conn.execute("SELECT AVG(importance) FROM memories").fetchone()[0]
        by_type = dict(conn.execute(
            "SELECT type, COUNT(*) FROM memories GROUP BY type"
        ).fetchall())
        stale = conn.execute(
            "SELECT COUNT(*) FROM memories "
            "WHERE importance < 5 AND created_at < datetime('now', '-90 days')"
        ).fetchone()[0]
        sessions = conn.execute(
            "SELECT COUNT(DISTINCT session_id) FROM session_chunks"
        ).fetchone()[0]
        chunks = conn.execute("SELECT COUNT(*) FROM session_chunks").fetchone()[0]
        cached_embeddings = conn.execute("SELECT COUNT(*) FROM embedding_cache").fetchone()[0]
    finally:
        conn.close()

    return {
        "total_memories": total,
        "avg_importance": round(avg_imp, 2) if avg_imp else 0.0,
        "by_type": by_type,
        "stale_memories": stale,
        "indexed_sessions": sessions,
        "session_chunks": chunks,
        "cached_embeddings": cached_embeddings,
    }


def rebuild_embeddings():
    """Generate embeddings for all memories that don't have one yet."""
    conn = init_db()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT m.id, m.content FROM memories m
        LEFT JOIN memory_embeddings e ON e.memory_id = m.id
        WHERE e.memory_id IS NULL
    """)
    rows = cursor.fetchall()
    conn.close()

    if not rows:
        return

    for mem_id, content in rows:
        _embed_on_write(mem_id, content)

    logger.info(f"Rebuilt embeddings for {len(rows)} memories")


# ── Session Transcript Indexing ─────────────────

def index_session(session_id: str, messages: list, chunk_tokens: int = 400):
    """Index a session's messages as searchable chunks."""
    if not messages:
        return

    conn = init_db()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM session_chunks WHERE session_id = ?", (session_id,))
    if cursor.fetchone()[0] > 0:
        conn.close()
        return

    transcript_parts = []
    for msg in messages:
        role = msg[1].title()
        content = _privacy_redact(msg[2][:500])
        transcript_parts.append(f"{role}: {content}")
    full_transcript = "\n".join(transcript_parts)

    chunk_chars = chunk_tokens * 4
    overlap_chars = 80 * 4
    chunks = []
    start = 0
    while start < len(full_transcript):
        end = min(start + chunk_chars, len(full_transcript))
        chunk_text = full_transcript[start:end]
        if chunk_text.strip():
            chunks.append(chunk_text)
        start = end - overlap_chars if end < len(full_transcript) else end

    now = datetime.now().isoformat()
    for i, chunk_text in enumerate(chunks):
        cursor.execute(
            "INSERT INTO session_chunks (session_id, chunk_index, content, created_at) VALUES (?, ?, ?, ?)",
            (session_id, i, chunk_text, now),
        )
        chunk_id = cursor.lastrowid

        try:
            vec, model_name = _get_embedding(chunk_text[:512])
            if vec:
                blob = _serialize_embedding(vec)
                cursor.execute(
                    "INSERT INTO session_chunk_embeddings (chunk_id, embedding, dim, model, created_at) VALUES (?, ?, ?, ?, ?)",
                    (chunk_id, blob, len(vec), model_name, now),
                )
                if len(vec) == _VEC_DIM:
                    try:
                        cursor.execute(
                            "INSERT INTO vec_session_chunks(chunk_id, embedding) VALUES (?, ?)",
                            (chunk_id, blob),
                        )
                    except Exception:
                        pass
        except Exception:
            pass

    conn.commit()
    conn.close()
    logger.info(f"Indexed session {session_id}: {len(messages)} messages -> {len(chunks)} chunks")


def _session_vector_search(query: str, limit: int = 10) -> list:
    """Search session chunks by vector similarity."""
    query_vec, _ = _get_embedding(query)
    if query_vec is None:
        return []

    conn = init_db()

    if len(query_vec) == _VEC_DIM:
        try:
            query_blob = _serialize_embedding(query_vec)
            rows = conn.execute("""
                SELECT v.chunk_id, v.distance, c.content, c.session_id, c.created_at
                FROM vec_session_chunks v
                JOIN session_chunks c ON c.id = v.chunk_id
                WHERE v.embedding MATCH ? AND k = ?
                ORDER BY v.distance
            """, (query_blob, limit)).fetchall()
            conn.close()
            results = []
            for chunk_id, distance, content, session_id, created_at in rows:
                similarity = max(0.0, 1.0 - (distance * distance) / 2.0)
                results.append({
                    "id": f"session:{chunk_id}",
                    "content": content[:300],
                    "type": "session",
                    "importance": 5,
                    "created_at": created_at,
                    "session_id": session_id,
                    "similarity": similarity,
                })
            return results
        except Exception as e:
            logger.debug(f"vec0 session search fell back to blob loop: {e}")

    cursor = conn.cursor()
    cursor.execute("""
        SELECT e.chunk_id, e.embedding, e.dim, c.content, c.session_id, c.created_at
        FROM session_chunk_embeddings e
        JOIN session_chunks c ON c.id = e.chunk_id
    """)
    results = []
    for row in cursor.fetchall():
        chunk_id, emb_blob, dim, content, session_id, created_at = row
        stored_vec = _deserialize_embedding(emb_blob, dim)
        similarity = _cosine_similarity(query_vec, stored_vec)
        results.append({
            "id": f"session:{chunk_id}",
            "content": content[:300],
            "type": "session",
            "importance": 5,
            "created_at": created_at,
            "session_id": session_id,
            "similarity": similarity,
        })
    conn.close()
    results.sort(key=lambda x: x["similarity"], reverse=True)
    return results[:limit]


def _session_fts_search(query: str, limit: int = 10) -> list:
    """Search session chunks using FTS5."""
    conn = init_db()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            SELECT c.id, c.content, c.session_id, c.created_at
            FROM session_chunks_fts f
            JOIN session_chunks c ON c.id = f.rowid
            WHERE session_chunks_fts MATCH ?
            ORDER BY f.rank
            LIMIT ?
        """, (query, limit))
        results = [{
            "id": f"session:{r[0]}",
            "content": r[1][:300],
            "type": "session",
            "importance": 5,
            "created_at": r[3],
            "session_id": r[2],
        } for r in cursor.fetchall()]
        conn.close()
        return results
    except Exception:
        conn.close()
        return []


def prune_old_session_chunks(retention_days: int = 30):
    """Delete session chunks older than retention_days."""
    conn = init_db()
    try:
        conn.execute("""
            DELETE FROM session_chunk_embeddings WHERE chunk_id IN (
                SELECT id FROM session_chunks WHERE created_at < datetime('now', ?)
            )
        """, (f"-{retention_days} days",))
        result = conn.execute(
            "DELETE FROM session_chunks WHERE created_at < datetime('now', ?)",
            (f"-{retention_days} days",),
        )
        deleted = result.rowcount
        conn.commit()
        if deleted > 0:
            logger.info(f"Pruned {deleted} old session chunks (>{retention_days} days)")
    except Exception as e:
        logger.debug(f"Session chunk pruning failed: {e}")
    finally:
        conn.close()


_SEMANTIC_DEDUP_THRESHOLD = 0.92


def add_memory(content: str, memory_type: str = "fact", importance: int = 5,
               museum_id: int = None, tags=None, source: str = None):
    """Add a new memory entry with semantic deduplication.

    Args:
        content: Text content of the memory.
        memory_type: One of fact/event/insight/error (default: fact).
        importance: Score 1-10 (default: 5).
        museum_id: Optional FK to leads.db museums.id (logical FK, not enforced).
        tags: Optional list or JSON string of tag labels (e.g. ["outreach", "pricing"]).
        source: Optional provenance string: "extraction", "manual", "research", "cli".
    """
    # Normalise tags to JSON string
    tags_json: str | None = None
    if tags is not None:
        if isinstance(tags, list):
            tags_json = json.dumps(tags)
        else:
            tags_json = str(tags)

    similar = _vector_search(content, limit=3)
    if similar and similar[0].get("similarity", 0.0) >= _SEMANTIC_DEDUP_THRESHOLD:
        existing_id = similar[0]["id"]
        logger.debug(
            "Semantic duplicate detected (similarity=%.3f), updating id=%d",
            similar[0]["similarity"], existing_id,
        )
        conn = init_db()
        conn.execute(
            "UPDATE memories SET content = ?, importance = ?, updated_at = ? WHERE id = ?",
            (content, importance, datetime.now().isoformat(), existing_id),
        )
        conn.commit()
        conn.close()
        _embed_on_write(existing_id, content)
        return {"id": existing_id, "content": content, "type": memory_type, "importance": importance,
                "museum_id": museum_id, "tags": tags_json, "source": source}

    conn = init_db()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO memories (content, type, importance, museum_id, tags, source, created_at) "
        "VALUES (?, ?, ?, ?, ?, ?, ?)",
        (content, memory_type, importance, museum_id, tags_json, source, datetime.now().isoformat()),
    )
    conn.commit()
    memory_id = cursor.lastrowid
    conn.close()

    _embed_on_write(memory_id, content)
    return {"id": memory_id, "content": content, "type": memory_type, "importance": importance,
            "museum_id": museum_id, "tags": tags_json, "source": source}


def search_memories(query: str, limit: int = 20, museum_id: int = None):
    """Search memories using FTS5 full-text search with LIKE fallback.

    Args:
        query: Search query string.
        limit: Maximum number of results (default 20).
        museum_id: Optional filter — only return memories for this museum.
    """
    conn = init_db()
    cursor = conn.cursor()

    try:
        if museum_id is not None:
            cursor.execute(
                """
                SELECT m.id, m.content, m.type, m.importance, m.created_at,
                       m.museum_id, m.tags, m.source
                FROM memories_fts f
                JOIN memories m ON m.id = f.rowid
                WHERE memories_fts MATCH ? AND m.museum_id = ?
                ORDER BY f.rank, m.importance DESC
                LIMIT ?
                """,
                (query, museum_id, limit)
            )
        else:
            cursor.execute(
                """
                SELECT m.id, m.content, m.type, m.importance, m.created_at,
                       m.museum_id, m.tags, m.source
                FROM memories_fts f
                JOIN memories m ON m.id = f.rowid
                WHERE memories_fts MATCH ?
                ORDER BY f.rank, m.importance DESC
                LIMIT ?
                """,
                (query, limit)
            )
        results = [
            {"id": r[0], "content": r[1], "type": r[2], "importance": r[3], "created_at": r[4],
             "museum_id": r[5], "tags": r[6], "source": r[7]}
            for r in cursor.fetchall()
        ]
        if results:
            conn.close()
            return results
    except Exception:
        pass

    if museum_id is not None:
        cursor.execute(
            """
            SELECT id, content, type, importance, created_at, museum_id, tags, source
            FROM memories
            WHERE content LIKE ? AND museum_id = ?
            ORDER BY importance DESC, created_at DESC
            LIMIT ?
            """,
            (f"%{query}%", museum_id, limit)
        )
    else:
        cursor.execute(
            """
            SELECT id, content, type, importance, created_at, museum_id, tags, source
            FROM memories
            WHERE content LIKE ?
            ORDER BY importance DESC, created_at DESC
            LIMIT ?
            """,
            (f"%{query}%", limit)
        )
    results = [
        {"id": r[0], "content": r[1], "type": r[2], "importance": r[3], "created_at": r[4],
         "museum_id": r[5], "tags": r[6], "source": r[7]}
        for r in cursor.fetchall()
    ]

    conn.close()
    return results


def list_memories(limit: int = 20, memory_type: str = None, museum_id: int = None):
    """List recent memories.

    Args:
        limit: Maximum number of results (default 20).
        memory_type: Optional filter by memory type.
        museum_id: Optional filter — only return memories for this museum.
    """
    conn = init_db()
    cursor = conn.cursor()

    base_select = (
        "SELECT id, content, type, importance, created_at, museum_id, tags, source "
        "FROM memories"
    )

    conditions = []
    params = []
    if memory_type:
        conditions.append("type = ?")
        params.append(memory_type)
    if museum_id is not None:
        conditions.append("museum_id = ?")
        params.append(museum_id)

    where = (" WHERE " + " AND ".join(conditions)) if conditions else ""
    sql = base_select + where + " ORDER BY created_at DESC LIMIT ?"
    params.append(limit)

    cursor.execute(sql, params)
    results = [
        {"id": r[0], "content": r[1], "type": r[2], "importance": r[3], "created_at": r[4],
         "museum_id": r[5], "tags": r[6], "source": r[7]}
        for r in cursor.fetchall()
    ]
    conn.close()
    return results


def delete_memory(memory_id: int):
    """Delete a memory by ID, cleaning up orphaned embeddings first."""
    conn = init_db()
    cursor = conn.cursor()
    # Clean up embeddings before removing the parent row (FTS trigger handles memories_fts)
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


def main():
    parser = argparse.ArgumentParser(description='Memory database operations')
    parser.add_argument('--action', required=True,
                       choices=['add', 'search', 'list', 'delete', 'stats'],
                       help='Operation to perform')
    parser.add_argument('--content', help='Content for add operation')
    parser.add_argument('--query', help='Search query')
    parser.add_argument('--type', default='fact',
                       choices=['event', 'fact', 'insight', 'error'],
                       help='Memory type')
    parser.add_argument('--importance', type=int, default=5,
                       help='Importance score 1-10')
    parser.add_argument('--limit', type=int, default=20,
                       help='Max results for list/search')
    parser.add_argument('--id', type=int, help='Memory ID for delete')

    args = parser.parse_args()

    try:
        if args.action == 'add':
            if not args.content:
                print("Error: --content required for add action", file=sys.stderr)
                sys.exit(1)
            result = add_memory(args.content, args.type, args.importance)
        elif args.action == 'search':
            if not args.query:
                print("Error: --query required for search action", file=sys.stderr)
                sys.exit(1)
            result = hybrid_search(args.query, args.limit)
        elif args.action == 'list':
            result = list_memories(args.limit, args.type if args.type != 'fact' else None)
        elif args.action == 'delete':
            if not args.id:
                print("Error: --id required for delete action", file=sys.stderr)
                sys.exit(1)
            result = delete_memory(args.id)
        elif args.action == 'stats':
            result = get_memory_stats()

        print(json.dumps(result, indent=2))

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
