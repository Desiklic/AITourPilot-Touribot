#!/usr/bin/env python3
"""
Memory Write - Write to logs and optionally update MEMORY.md

Usage:
    python memory_write.py --content "text" [--type event] [--importance 5]
    python memory_write.py --content "text" --update-memory
"""

import argparse
import re
import sys
from datetime import datetime
from pathlib import Path

# Paths — relative to project root
PROJECT_ROOT = Path(__file__).parent.parent.parent
MEMORY_DIR = PROJECT_ROOT / "memory"
LOGS_DIR = MEMORY_DIR / "logs"
MEMORY_MD = MEMORY_DIR / "MEMORY.md"

# Import memory_db for database storage
try:
    from tools.memory.memory_db import add_memory
except ImportError:
    add_memory = None


def ensure_dirs():
    """Ensure memory directories exist."""
    LOGS_DIR.mkdir(parents=True, exist_ok=True)


def get_today_log_path() -> Path:
    """Get today's log file path."""
    return LOGS_DIR / f"{datetime.now().strftime('%Y-%m-%d')}.md"


def append_to_log(content: str, memory_type: str, importance: int):
    """Append entry to today's log file."""
    ensure_dirs()
    log_path = get_today_log_path()

    timestamp = datetime.now().strftime("%H:%M:%S")
    type_marker = {
        "fact": "📌", "event": "📅", "insight": "💡", "error": "⚠️",
        "contact_intel": "👤", "museum_intel": "🏛️", "interaction": "💬",
        "strategy": "🎯", "research": "🔬", "general": "📝"
    }.get(memory_type, "📝")

    if not log_path.exists():
        header = f"# Daily Log - {datetime.now().strftime('%Y-%m-%d')}\n\n"
        log_path.write_text(header)

    entry = f"{timestamp} {type_marker} (imp:{importance}) {content}\n"

    with open(log_path, "a") as f:
        f.write(entry)

    return log_path


# TouriBot topic routes — adapted from HenryBot
_TOPIC_ROUTES = {
    "leads": {
        "keywords": [
            "museum", "gallery", "heritage", "contact", "lead", "prospect",
            "institution", "visitor", "director", "curator", "head of digital",
            "meeting", "demo", "call", "response", "reply",
        ],
        "types": {"fact", "event", "insight"},
    },
    "emails": {
        "keywords": [
            "email", "draft", "outreach", "subject line", "follow-up",
            "sequence", "message", "sent", "replied", "opened",
        ],
        "types": {"event", "insight"},
    },
    "campaign": {
        "keywords": [
            "campaign", "strategy", "pipeline", "stage", "conversion",
            "timing", "budget", "quarter", "window", "summit",
        ],
        "types": {"fact", "insight"},
    },
    "product": {
        "keywords": [
            "aitourpilot", "product", "pilot", "pricing", "feature",
            "audioguide", "ai guide", "case study", "pedrera", "competitor",
            "smartify", "gesso", "cuseum",
        ],
        "types": {"fact", "insight"},
    },
    "museums": {
        "keywords": [
            "joanneum", "great britain", "loevestein", "cap sciences",
            "geneva", "pedrera", "hubspot", "mailerlite",
        ],
        "types": {"fact", "event", "insight"},
    },
}


def _route_to_topic_file(content: str, memory_type: str):
    """Append content to the matching topic file.

    Returns the path written to, or None if no route matched.
    """
    content_lower = content.lower()
    for topic, cfg in _TOPIC_ROUTES.items():
        if memory_type not in cfg["types"]:
            continue
        if any(re.search(r'\b' + re.escape(kw) + r'\b', content_lower) for kw in cfg["keywords"]):
            topic_path = MEMORY_DIR / f"{topic}.md"
            timestamp = datetime.now().strftime("%Y-%m-%d")
            entry = f"- [{timestamp}] {content}\n"
            if not topic_path.exists():
                topic_path.write_text(f"# {topic.capitalize()} Memory\n\n> Auto-curated from TouriBot\n\n")
            with open(topic_path, "a") as f:
                f.write(entry)
            return topic_path
    return None


def _get_working_tier_max_chars() -> int:
    """Return the configured max chars for the Auto-Promoted section (default 5000)."""
    try:
        import yaml
        settings_path = PROJECT_ROOT / "args" / "settings.yaml"
        with open(settings_path) as f:
            full = yaml.safe_load(f)
        return int(full.get("memory", {}).get("working_tier_max_chars", 5000))
    except Exception:
        return 5000


def _is_pinned(entry: str) -> bool:
    """Return True if this entry should never be evicted."""
    return "PINNED:" in entry


def append_to_memory_md(content: str, memory_type: str = "fact"):
    """Append curated fact to MEMORY.md under ## Auto-Promoted, with size guard."""
    ensure_dirs()

    _route_to_topic_file(content, memory_type)

    timestamp = datetime.now().strftime("%Y-%m-%d")
    entry = f"- [{timestamp}] {content}"
    section_header = "## Auto-Promoted"
    max_entries = 50

    if not MEMORY_MD.exists():
        header = f"""# TouriBot Memory

> Curated facts and learnings

---

## Facts

{section_header}

{entry}
"""
        MEMORY_MD.write_text(header)
        return MEMORY_MD

    text = MEMORY_MD.read_text()

    if section_header not in text:
        text = text.rstrip() + f"\n\n{section_header}\n\n{entry}\n"
        MEMORY_MD.write_text(text)
        return MEMORY_MD

    before, after_header = text.split(section_header, 1)

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

    if any(content in e for e in entries):
        return MEMORY_MD

    entries.append(entry)
    if len(entries) > max_entries:
        entries = entries[-max_entries:]

    max_chars = _get_working_tier_max_chars()
    while len("\n".join(entries)) > max_chars and len(entries) > 1:
        dropped = False
        for i, e in enumerate(entries):
            if not _is_pinned(e):
                entries.pop(i)
                dropped = True
                break
        if not dropped:
            break

    rebuilt = before + section_header + "\n\n" + "\n".join(entries) + "\n"
    if rest_lines:
        rebuilt += "\n" + "\n".join(rest_lines)

    MEMORY_MD.write_text(rebuilt)
    return MEMORY_MD


def write_memory(content: str, memory_type: str = "event",
                 importance: int = 5, update_memory: bool = False,
                 museum_id: int = None, tags=None, source: str = None):
    """Write memory to all relevant locations.

    Args:
        content: Text content to store.
        memory_type: One of fact/event/insight/error (default: event).
        importance: Score 1-10 (default: 5).
        update_memory: Also append to MEMORY.md (default: False).
        museum_id: Optional FK to leads.db museums.id.
        tags: Optional list or JSON string of tag labels.
        source: Optional provenance string (extraction/manual/research/cli).
    """
    results = {}

    log_path = append_to_log(content, memory_type, importance)
    results["log"] = str(log_path)

    if add_memory:
        db_result = add_memory(content, memory_type, importance,
                               museum_id=museum_id, tags=tags, source=source)
        results["db"] = db_result
    else:
        results["db"] = "skipped (memory_db not available)"

    if update_memory:
        memory_path = append_to_memory_md(content, memory_type)
        results["memory_md"] = str(memory_path)

    return results


def main():
    parser = argparse.ArgumentParser(description='Write to memory system')
    parser.add_argument('--content', required=True, help='Content to write')
    parser.add_argument('--type', default='event',
                       choices=[
                           'event', 'fact', 'insight', 'error',
                           'contact_intel', 'museum_intel', 'interaction',
                           'strategy', 'research', 'general',
                       ],
                       help='Memory type')
    parser.add_argument('--importance', type=int, default=5,
                       help='Importance score 1-10')
    parser.add_argument('--update-memory', action='store_true',
                       help='Also append to MEMORY.md')

    args = parser.parse_args()

    if not 1 <= args.importance <= 10:
        print("Error: importance must be between 1 and 10", file=sys.stderr)
        sys.exit(1)

    try:
        results = write_memory(
            content=args.content,
            memory_type=args.type,
            importance=args.importance,
            update_memory=args.update_memory
        )

        print("Memory written successfully:")
        print(f"  Log: {results['log']}")
        if 'memory_md' in results:
            print(f"  MEMORY.md: {results['memory_md']}")
        if isinstance(results['db'], dict):
            print(f"  DB ID: {results['db'].get('id')}")

    except Exception as e:
        print(f"Error writing memory: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
