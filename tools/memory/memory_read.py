#!/usr/bin/env python3
"""
Memory Read - Load memory at session start

Usage:
    python memory_read.py              # Read today's context
    python memory_read.py --yesterday  # Include yesterday's log
    python memory_read.py --all        # Read all memory sources
"""

import argparse
import sys
from datetime import datetime, timedelta
from pathlib import Path

# Paths — relative to project root
PROJECT_ROOT = Path(__file__).parent.parent.parent
MEMORY_DIR = PROJECT_ROOT / "memory"
LOGS_DIR = MEMORY_DIR / "logs"
MEMORY_MD = MEMORY_DIR / "MEMORY.md"

# TouriBot topic files
TOPIC_FILES = {
    "leads": MEMORY_DIR / "leads.md",
    "emails": MEMORY_DIR / "emails.md",
    "campaign": MEMORY_DIR / "campaign.md",
    "product": MEMORY_DIR / "product.md",
    "museums": MEMORY_DIR / "museums.md",
}


def read_file_if_exists(path: Path, label: str = None):
    """Read a file if it exists, return content or None."""
    if path.exists():
        content = path.read_text()
        if label:
            return f"\n### {label}\n\n{content}"
        return content
    return None


def get_log_path(date: datetime) -> Path:
    """Get the log file path for a given date."""
    return LOGS_DIR / f"{date.strftime('%Y-%m-%d')}.md"


def read_topic_file(topic: str) -> str:
    """Read a named topic memory file."""
    topic_lower = topic.lower().rstrip(".md")
    path = TOPIC_FILES.get(topic_lower)
    if path is None:
        available = ", ".join(TOPIC_FILES.keys())
        return f"Unknown topic '{topic}'. Available: {available}"
    if not path.exists():
        return f"No topic file found for '{topic}' (not yet created)."
    return path.read_text()


def read_memory(include_yesterday: bool = False, read_all: bool = False, topic: str = None):
    """Read memory from various sources."""
    if topic:
        return read_topic_file(topic)

    output = []
    today = datetime.now()
    yesterday = today - timedelta(days=1)

    output.append(f"# Memory Load - {today.strftime('%Y-%m-%d %H:%M')}\n")

    # Read MEMORY.md (curated facts)
    memory_content = read_file_if_exists(MEMORY_MD, "MEMORY.md (Curated Facts)")
    if memory_content:
        output.append(memory_content)

    # Read today's log
    today_log = read_file_if_exists(get_log_path(today), f"Today's Log ({today.strftime('%Y-%m-%d')})")
    if today_log:
        output.append(today_log)

    # Read yesterday's log if requested
    if include_yesterday or read_all:
        yesterday_log = read_file_if_exists(
            get_log_path(yesterday),
            f"Yesterday's Log ({yesterday.strftime('%Y-%m-%d')})"
        )
        if yesterday_log:
            output.append(yesterday_log)

    # Read recent DB entries if --all
    if read_all:
        try:
            import sqlite3
            db_path = PROJECT_ROOT / "data" / "memory.db"
            if db_path.exists():
                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT content, type, importance, created_at
                    FROM memories
                    ORDER BY importance DESC, created_at DESC
                    LIMIT 10
                """)
                rows = cursor.fetchall()
                conn.close()

                if rows:
                    output.append("\n### Recent High-Importance Memories (DB)\n")
                    for row in rows:
                        output.append(f"- [{row[1]}] (imp:{row[2]}) {row[0][:200]}")
        except Exception as e:
            output.append(f"\n*Note: Could not read memory DB: {e}*")

    if len(output) == 1:
        output.append("\n*No memory files found. This may be the first session.*")
        output.append(f"\nExpected locations:")
        output.append(f"- {MEMORY_MD}")
        output.append(f"- {get_log_path(today)}")

    return "\n".join(output)


def main():
    parser = argparse.ArgumentParser(description='Load memory at session start')
    parser.add_argument('--yesterday', action='store_true',
                       help="Also read yesterday's log")
    parser.add_argument('--all', action='store_true',
                       help='Read all memory sources')
    parser.add_argument('--topic', metavar='NAME',
                       help='Read a specific topic file (leads, emails, campaign, product, museums)')

    args = parser.parse_args()

    try:
        result = read_memory(
            include_yesterday=args.yesterday,
            read_all=args.all,
            topic=args.topic,
        )
        print(result)
    except Exception as e:
        print(f"Error reading memory: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
