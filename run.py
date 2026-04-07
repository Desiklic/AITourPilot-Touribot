#!/usr/bin/env python3
"""TouriBot — AITourPilot Outreach Co-Pilot

Entry point for all TouriBot commands.

Usage:
    python run.py chat                    # Start interactive chat
    python run.py recall "<query>"        # Search memory
    python run.py remember "<fact>"       # Save a fact to memory
"""

import os
import sys
from pathlib import Path

# Ensure project root is on sys.path for imports
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

# Suppress tokenizer parallelism warnings before any imports
os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")


def cmd_chat():
    """Start interactive chat session."""
    from tools.chat.session import run_chat
    run_chat()


def cmd_recall(query: str):
    """Search memory for relevant context."""
    from rich.console import Console
    from rich.table import Table

    # Load .env
    try:
        from dotenv import load_dotenv
        load_dotenv(PROJECT_ROOT / ".env")
    except ImportError:
        pass

    from tools.memory.memory_db import hybrid_search

    console = Console()
    results = hybrid_search(query, limit=10, include_sessions=True)

    if not results:
        console.print(f"[dim]No memories found for: {query}[/dim]")
        return

    table = Table(title=f"Memory Search: \"{query}\"", show_lines=True)
    table.add_column("Score", style="cyan", width=6)
    table.add_column("Type", style="green", width=8)
    table.add_column("Source", style="yellow", width=8)
    table.add_column("Content", style="white")
    table.add_column("Date", style="dim", width=12)

    for r in results:
        score = f"{r.get('score', 0.0):.2f}"
        mtype = r.get("type", "?")
        source = r.get("source", "memory")
        content = r.get("content", "")[:200]
        created = r.get("created_at", "")[:10]
        table.add_row(score, mtype, source, content, created)

    console.print(table)


def cmd_remember(fact: str):
    """Save a fact to memory."""
    from rich.console import Console

    # Load .env
    try:
        from dotenv import load_dotenv
        load_dotenv(PROJECT_ROOT / ".env")
    except ImportError:
        pass

    from tools.memory.memory_write import write_memory

    console = Console()
    results = write_memory(content=fact, memory_type="fact", importance=7, update_memory=True)

    console.print(f"[green]Remembered:[/green] {fact}")
    if isinstance(results.get("db"), dict):
        console.print(f"[dim]  DB ID: {results['db'].get('id')}[/dim]")
    console.print(f"[dim]  Log: {results.get('log', 'n/a')}[/dim]")


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(0)

    command = sys.argv[1].lower()

    if command == "chat":
        cmd_chat()
    elif command == "recall":
        if len(sys.argv) < 3:
            print("Usage: python run.py recall \"<query>\"")
            sys.exit(1)
        cmd_recall(" ".join(sys.argv[2:]))
    elif command == "remember":
        if len(sys.argv) < 3:
            print("Usage: python run.py remember \"<fact>\"")
            sys.exit(1)
        cmd_remember(" ".join(sys.argv[2:]))
    else:
        print(f"Unknown command: {command}")
        print("Available: chat, recall, remember")
        sys.exit(1)


if __name__ == "__main__":
    main()
