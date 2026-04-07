#!/usr/bin/env python3
"""TouriBot — AITourPilot Outreach Co-Pilot

Entry point for all TouriBot commands.

Usage:
    python run.py chat                              # Start interactive chat
    python run.py draft "<name>, <institution>"     # Draft an outreach email
    python run.py draft --follow-up "<institution>" # Draft a follow-up email
    python run.py log-response "<institution>"      # Score an inbound reply
    python run.py recall "<query>"                  # Search memory
    python run.py remember "<fact>"                 # Save a fact to memory
    python run.py ingest                            # Process knowledge base
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

    _load_env()
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

    _load_env()
    from tools.memory.memory_write import write_memory

    console = Console()
    results = write_memory(content=fact, memory_type="fact", importance=7, update_memory=True)

    console.print(f"[green]Remembered:[/green] {fact}")
    if isinstance(results.get("db"), dict):
        console.print(f"[dim]  DB ID: {results['db'].get('id')}[/dim]")
    console.print(f"[dim]  Log: {results.get('log', 'n/a')}[/dim]")


def cmd_draft(args: list[str]):
    """Draft a personalized outreach email."""
    from rich.console import Console

    _load_env()

    console = Console()

    # Parse arguments
    message_type = "initial"
    extra_context = ""
    target = ""

    i = 0
    while i < len(args):
        if args[i] == "--follow-up":
            message_type = "follow-up"
        elif args[i] == "--response":
            message_type = "response"
        elif args[i] == "--context":
            if i + 1 < len(args):
                i += 1
                extra_context = args[i]
        else:
            if target:
                target += " " + args[i]
            else:
                target = args[i]
        i += 1

    if not target:
        console.print("[red]Usage:[/red] python run.py draft \"Name, Institution\"")
        console.print("       python run.py draft --follow-up \"Institution\"")
        return

    # Parse "Name, Institution" or just "Institution"
    contact_name = ""
    museum_name = target
    if "," in target:
        parts = target.split(",", 1)
        contact_name = parts[0].strip()
        museum_name = parts[1].strip()

    console.print(f"\n[bold cyan]Drafting {message_type} email[/bold cyan]")
    console.print(f"  Museum: {museum_name}")
    if contact_name:
        console.print(f"  Contact: {contact_name}")
    console.print()

    from tools.outreach.drafter import draft_email
    result = draft_email(
        museum_name=museum_name,
        contact_name=contact_name,
        message_type=message_type,
        extra_context=extra_context,
    )


def cmd_log_response(args: list[str]):
    """Score an inbound reply from a museum contact."""
    from rich.console import Console

    _load_env()

    console = Console()

    museum_name = " ".join(args) if args else ""
    if not museum_name:
        console.print("[red]Usage:[/red] python run.py log-response \"Museum Name\"")
        return

    console.print(f"\n[bold cyan]Scoring response from {museum_name}[/bold cyan]")
    console.print("Paste the reply text below, then press Enter twice (empty line) to submit:\n")

    # Read multiline input
    lines = []
    while True:
        try:
            line = input()
            if line == "" and lines:
                break
            lines.append(line)
        except EOFError:
            break

    reply_text = "\n".join(lines).strip()
    if not reply_text:
        console.print("[yellow]No reply text provided. Aborting.[/yellow]")
        return

    from tools.outreach.scorer import score_response
    result = score_response(museum_name=museum_name, reply_text=reply_text)


def cmd_ingest():
    """Process knowledge base from source documents."""
    from tools.knowledge.ingest import run_ingest
    run_ingest()


def _load_env():
    """Load .env file."""
    try:
        from dotenv import load_dotenv
        load_dotenv(PROJECT_ROOT / ".env")
    except ImportError:
        pass


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(0)

    command = sys.argv[1].lower()

    if command == "chat":
        cmd_chat()
    elif command == "draft":
        cmd_draft(sys.argv[2:])
    elif command in ("log-response", "log_response"):
        cmd_log_response(sys.argv[2:])
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
    elif command == "ingest":
        cmd_ingest()
    else:
        print(f"Unknown command: {command}")
        print("Available: chat, draft, log-response, recall, remember, ingest")
        sys.exit(1)


if __name__ == "__main__":
    main()
