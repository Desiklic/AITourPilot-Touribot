"""Memory curator: daily expiry of old episodic entries from MEMORY.md.

Entries older than `expiry_days` that are NOT pinned are removed from MEMORY.md.
They remain safely in memory.db -- nothing is lost.

Pinned entries: importance=10 or containing 'PINNED:' in the text.
"""
import logging
import re
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
