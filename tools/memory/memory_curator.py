"""Memory curator: daily expiry of old episodic entries from MEMORY.md, and batch reclassification.

Entries older than `expiry_days` that are NOT pinned are removed from MEMORY.md.
They remain safely in memory.db -- nothing is lost.

Pinned entries: importance=10 or containing 'PINNED:' in the text.
"""
import json
import logging
import os
import re
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path

logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).parent.parent.parent
MEMORY_MD = PROJECT_ROOT / "memory" / "MEMORY.md"
SECTION_HEADER = "## Auto-Promoted"

_DATE_RE = re.compile(r"^\- \[(\d{4}-\d{2}-\d{2})\]")


def _get_expiry_days() -> int:
    """Return configured expiry days (default 90)."""
    try:
        import yaml
        settings_path = PROJECT_ROOT / "args" / "settings.yaml"
        with open(settings_path) as f:
            full = yaml.safe_load(f)
        return int(full.get("memory", {}).get("episodic_expiry_days", 90))
    except Exception:
        return 90


def _is_pinned(entry: str) -> bool:
    """Return True if this entry should never expire or be evicted."""
    return "PINNED:" in entry


def expire_working_memory(expiry_days: int | None = None) -> int:
    """Remove old non-pinned entries from MEMORY.md's Auto-Promoted section.

    Returns:
        Number of entries expired (removed from MEMORY.md).
    """
    if expiry_days is None:
        expiry_days = _get_expiry_days()

    if not MEMORY_MD.exists():
        return 0

    cutoff = datetime.now() - timedelta(days=expiry_days)
    text = MEMORY_MD.read_text()

    if SECTION_HEADER not in text:
        return 0

    before, after_header = text.split(SECTION_HEADER, 1)

    lines_after = after_header.split("\n")
    entries = []
    rest_lines = []
    in_section = True
    for line in lines_after:
        if in_section:
            if line.startswith("- ["):
                entries.append(line)
            elif line.strip() == "":
                continue
            elif entries:
                in_section = False
                rest_lines.append(line)
        else:
            rest_lines.append(line)

    expired_count = 0
    kept = []
    for entry in entries:
        if _is_pinned(entry):
            kept.append(entry)
            continue
        m = _DATE_RE.match(entry)
        if m:
            try:
                entry_date = datetime.strptime(m.group(1), "%Y-%m-%d")
                if entry_date < cutoff:
                    expired_count += 1
                    logger.info("Expired MEMORY.md entry from %s: %s", m.group(1), entry[:80])
                    continue
            except ValueError:
                pass
        kept.append(entry)

    if expired_count == 0:
        return 0

    rebuilt = before + SECTION_HEADER + "\n\n" + "\n".join(kept) + "\n"
    if rest_lines:
        rebuilt += "\n" + "\n".join(rest_lines)

    MEMORY_MD.write_text(rebuilt)
    logger.info("Memory curator: expired %d old entries from MEMORY.md", expired_count)
    return expired_count


# ---------------------------------------------------------------------------
# DB-level expiry
# ---------------------------------------------------------------------------


def expire_db_memories(expiry_days: int | None = None, min_importance: int = 5) -> int:
    """Delete old low-importance memories from memory.db.

    Only removes interaction, general, and event types older than expiry_days
    with importance < min_importance.  Pinned memories (containing 'PINNED:')
    and memories with importance >= 8 are always preserved.

    Returns:
        Number of memories deleted.
    """
    if expiry_days is None:
        expiry_days = _get_expiry_days()

    db_path = PROJECT_ROOT / "data" / "memory.db"
    if not db_path.exists():
        return 0

    from tools.memory.memory_db import init_db
    conn = init_db()
    try:
        cursor = conn.execute(
            """DELETE FROM memories
               WHERE importance < ?
               AND importance < 8
               AND type IN ('interaction', 'general', 'event')
               AND created_at < datetime('now', ?)
               AND content NOT LIKE '%PINNED:%'""",
            (min_importance, f"-{expiry_days} days"),
        )
        deleted = cursor.rowcount
        conn.commit()
        if deleted:
            logger.info("Memory curator: expired %d old low-importance DB memories", deleted)
        return deleted
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Consolidation
# ---------------------------------------------------------------------------


def consolidate_memories() -> int:
    """Merge highly similar memories (cosine > 0.85) within the same museum.

    Compares memories pairwise (limited scope for performance), keeps the
    higher-importance one, and deletes the near-duplicate.  Only merges
    memories sharing the same museum_id.  Memories with importance >= 8
    are never deleted by consolidation.

    Returns:
        Number of duplicates removed.
    """
    db_path = PROJECT_ROOT / "data" / "memory.db"
    if not db_path.exists():
        return 0

    try:
        from tools.memory.memory_db import init_db, _get_embedding, _cosine_similarity, _text_jaccard, delete_memory
    except ImportError as e:
        logger.warning("consolidate_memories: import failed: %s", e)
        return 0

    conn = init_db()
    all_mems = conn.execute(
        "SELECT id, content, type, importance, museum_id FROM memories ORDER BY importance DESC"
    ).fetchall()
    conn.close()

    merged = 0
    skip_ids: set[int] = set()
    comparisons = 0
    MAX_COMPARISONS = 1000  # Guard against O(n^2) explosion

    for i, row_i in enumerate(all_mems):
        if row_i[0] in skip_ids:
            continue
        for j in range(i + 1, min(i + 50, len(all_mems))):
            if comparisons >= MAX_COMPARISONS:
                break
            row_j = all_mems[j]
            if row_j[0] in skip_ids:
                continue
            # Only merge within same museum
            if row_i[4] != row_j[4]:
                continue
            # Quick text pre-filter before expensive embedding call
            if _text_jaccard(row_i[1], row_j[1]) < 0.3:
                continue

            vec_i, _ = _get_embedding(row_i[1])
            vec_j, _ = _get_embedding(row_j[1])
            comparisons += 1

            if vec_i and vec_j and _cosine_similarity(vec_i, vec_j) > 0.85:
                # Keep higher-importance; never delete importance >= 8
                keep_id = row_i[0] if row_i[3] >= row_j[3] else row_j[0]
                del_id = row_j[0] if keep_id == row_i[0] else row_i[0]
                del_importance = row_j[3] if keep_id == row_i[0] else row_i[3]

                if del_importance >= 8:
                    continue  # Safety: never auto-delete high-value memories

                delete_memory(del_id)
                skip_ids.add(del_id)
                merged += 1
                logger.debug("Consolidated memory %d (duplicate of %d)", del_id, keep_id)

        if comparisons >= MAX_COMPARISONS:
            logger.info("consolidate_memories: hit comparison limit (%d)", MAX_COMPARISONS)
            break

    if merged:
        logger.info("Memory curator: consolidated %d duplicate memories", merged)
    return merged


# ---------------------------------------------------------------------------
# Batch reclassify old memories into new taxonomy
# ---------------------------------------------------------------------------

_OLD_TYPES = ("fact", "event", "insight", "error")

_RECLASSIFY_SYSTEM = """You are a memory classifier for TouriBot, an AI museum outreach assistant.

Classify each memory into exactly one of these types:
- contact_intel: Information about a specific person (name, role, preferences, response style)
- museum_intel: Information about a museum (visitors, tech stack, budget, org structure)
- interaction: A specific dated interaction (email sent, meeting, demo, response received)
- strategy: Campaign-level learnings (angles that work, timing, template performance)
- general: Anything else (product facts, tool info, Hermann's preferences, misc)

Rules:
- Return a JSON array, one object per memory, same order as input.
- Each object: {"id": <int>, "type": "<new_type>"}
- No explanation, no markdown, pure JSON array only."""


def reclassify_old_types(batch_size: int = 8) -> int:
    """Batch reclassify old fact/event/insight/error memories into new taxonomy.

    Fetches all memories with legacy types from memory.db, sends them to
    claude-haiku-4-5-20251001 in batches, and UPDATEs the type column in place.

    Returns:
        Total count of memories reclassified.
    """
    try:
        from dotenv import load_dotenv
        load_dotenv(PROJECT_ROOT / ".env")
    except ImportError:
        pass

    import anthropic

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise RuntimeError("ANTHROPIC_API_KEY not set")

    client = anthropic.Anthropic(api_key=api_key)

    db_path = PROJECT_ROOT / "data" / "memory.db"
    if not db_path.exists():
        logger.info("memory.db not found, nothing to reclassify")
        return 0

    conn = sqlite3.connect(db_path)
    try:
        placeholders = ",".join("?" * len(_OLD_TYPES))
        rows = conn.execute(
            f"SELECT id, content FROM memories WHERE type IN ({placeholders}) ORDER BY id ASC",
            _OLD_TYPES,
        ).fetchall()
    finally:
        # Keep conn open for updates below
        pass

    if not rows:
        conn.close()
        logger.info("No legacy-typed memories to reclassify")
        return 0

    logger.info("Reclassifying %d memories with old types...", len(rows))
    total_reclassified = 0

    # Process in batches
    for start in range(0, len(rows), batch_size):
        batch = rows[start : start + batch_size]
        items = [{"id": r[0], "content": r[1][:200]} for r in batch]
        prompt = (
            "Classify each of these memories.\n\n"
            + json.dumps(items, indent=2)
        )

        try:
            response = client.messages.create(
                model="claude-haiku-4-5-20251001",
                max_tokens=512,
                temperature=0.0,
                system=_RECLASSIFY_SYSTEM,
                messages=[{"role": "user", "content": prompt}],
            )
            text = response.content[0].text.strip()
            if text.startswith("```"):
                text = text.split("\n", 1)[1].rsplit("```", 1)[0].strip()

            classifications = json.loads(text)
            for item in classifications:
                mem_id = item.get("id")
                new_type = item.get("type", "general")
                valid_types = {"contact_intel", "museum_intel", "interaction", "strategy", "general"}
                if new_type not in valid_types:
                    new_type = "general"
                conn.execute(
                    "UPDATE memories SET type = ? WHERE id = ?",
                    (new_type, mem_id),
                )
                total_reclassified += 1

            conn.commit()
            logger.info(
                "Reclassified batch %d-%d (%d memories)",
                start + 1, start + len(batch), len(classifications)
            )

        except Exception as e:
            logger.warning("Batch reclassification failed for batch starting at %d: %s", start, e)
            continue

    conn.close()
    logger.info("Reclassification complete: %d memories updated", total_reclassified)
    return total_reclassified
