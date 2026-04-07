#!/usr/bin/env python3
"""TouriBot — AITourPilot Outreach Co-Pilot

Entry point for all TouriBot commands.

Usage:
    python run.py chat                              # Start interactive chat
    python run.py draft "<name>, <institution>"     # Draft an outreach email
    python run.py draft --follow-up "<institution>" # Draft a follow-up email
    python run.py log-response "<institution>"      # Score an inbound reply
    python run.py pipeline                          # Show pipeline overview
    python run.py pipeline --stage 3                # Filter by stage
    python run.py status                            # Quick briefing
    python run.py add-lead                          # Add a museum interactively
    python run.py update-lead "<museum>" --stage N  # Update pipeline stage
    python run.py log-email "<museum>"              # Mark email as sent
    python run.py import-leads <csv> --source X     # Bulk import (hubspot|mailerlite)
    python run.py recall "<query>"                  # Search memory
    python run.py remember "<fact>"                 # Save a fact to memory
    python run.py ingest                            # Process knowledge base
"""

import os
import sys
from datetime import datetime
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


def cmd_pipeline(args: list[str]):
    """Show pipeline overview."""
    from tools.leads.pipeline import pipeline_table

    stage_filter = None
    i = 0
    while i < len(args):
        if args[i] == "--stage" and i + 1 < len(args):
            i += 1
            try:
                stage_filter = int(args[i])
            except ValueError:
                print(f"Invalid stage: {args[i]}")
                return
        i += 1

    pipeline_table(stage_filter=stage_filter)


def cmd_status():
    """Quick pipeline briefing."""
    from tools.leads.pipeline import show_status
    show_status()


def cmd_add_lead():
    """Interactively add a museum and contact."""
    from rich.console import Console
    from tools.leads.lead_db import add_museum, add_contact

    console = Console()
    console.print("\n[bold cyan]Add New Lead[/bold cyan]\n")

    name = input("Museum name: ").strip()
    if not name:
        console.print("[yellow]Cancelled[/yellow]")
        return

    city = input("City (optional): ").strip() or None
    country = input("Country (optional): ").strip() or None

    result = add_museum(name=name, city=city, country=country, source="manual")
    museum_id = result["id"]
    console.print(f"[green]Created museum:[/green] {name} (ID: {museum_id})")

    contact_name = input("Contact name (optional): ").strip()
    if contact_name:
        email = input("Contact email (optional): ").strip() or None
        role = input("Contact role (optional): ").strip() or None
        add_contact(museum_id=museum_id, full_name=contact_name, email=email, role=role)
        console.print(f"[green]Added contact:[/green] {contact_name}")

    console.print()


def cmd_update_lead(args: list[str]):
    """Update a museum's pipeline stage."""
    from rich.console import Console
    from tools.leads.lead_db import update_stage, STAGE_NAMES

    console = Console()

    museum_name = ""
    new_stage = None
    force = False
    i = 0
    while i < len(args):
        if args[i] == "--stage" and i + 1 < len(args):
            i += 1
            try:
                new_stage = int(args[i])
            except ValueError:
                console.print(f"[red]Invalid stage: {args[i]}[/red]")
                return
        elif args[i] == "--force":
            force = True
        else:
            museum_name = (museum_name + " " + args[i]).strip()
        i += 1

    if not museum_name or new_stage is None:
        console.print("[red]Usage:[/red] python run.py update-lead \"Museum Name\" --stage N")
        return

    try:
        result = update_stage(museum_name, new_stage, force=force)
        stage_name = STAGE_NAMES.get(new_stage, "?")
        console.print(f"[green]{result['museum']}[/green] moved to Stage {new_stage} ({stage_name})")
    except ValueError as e:
        console.print(f"[red]Error:[/red] {e}")


def cmd_log_email(args: list[str]):
    """Mark an email as sent, advance museum to Stage 3."""
    from rich.console import Console
    from tools.leads.lead_db import get_museum, update_stage, add_interaction, STAGE_NAMES

    console = Console()

    museum_name = " ".join(args) if args else ""
    if not museum_name:
        console.print("[red]Usage:[/red] python run.py log-email \"Museum Name\"")
        return

    museum = get_museum(museum_name)
    if not museum:
        console.print(f"[red]Museum not found:[/red] {museum_name}")
        return

    # Log the interaction
    add_interaction(
        museum_id=museum["id"],
        direction="outbound",
        channel="email",
        body="Email sent (logged via CLI)",
        sent_at=datetime.now().isoformat(),
        is_draft=0,
    )

    # Advance to stage 3 if currently below
    if museum["stage"] < 3:
        update_stage(museum["name"], 3)
        console.print(f"[green]{museum['name']}[/green] — email logged, moved to Stage 3 (Outreach Sent)")
    else:
        console.print(f"[green]{museum['name']}[/green] — email logged (already at Stage {museum['stage']})")


def cmd_import_leads(args: list[str]):
    """Bulk import contacts from CSV."""
    from rich.console import Console
    from tools.leads.lead_db import import_csv

    console = Console()

    filepath = ""
    source = "hubspot"
    i = 0
    while i < len(args):
        if args[i] == "--source" and i + 1 < len(args):
            i += 1
            source = args[i]
        else:
            filepath = args[i]
        i += 1

    if not filepath:
        console.print("[red]Usage:[/red] python run.py import-leads <csv> --source hubspot|mailerlite")
        return

    try:
        result = import_csv(filepath, source)
        console.print(f"[green]Imported {result['imported']} contacts[/green] from {source}")
        console.print(f"  Museums created: {result['museums_created']}")
        console.print(f"  Skipped (duplicates/empty): {result['skipped']}")
    except (FileNotFoundError, ValueError) as e:
        console.print(f"[red]Error:[/red] {e}")


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
    elif command == "pipeline":
        cmd_pipeline(sys.argv[2:])
    elif command == "status":
        cmd_status()
    elif command in ("add-lead", "add_lead"):
        cmd_add_lead()
    elif command in ("update-lead", "update_lead"):
        cmd_update_lead(sys.argv[2:])
    elif command in ("log-email", "log_email"):
        cmd_log_email(sys.argv[2:])
    elif command in ("import-leads", "import_leads"):
        cmd_import_leads(sys.argv[2:])
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
        print("Available: chat, draft, log-response, pipeline, status,")
        print("          add-lead, update-lead, log-email, import-leads,")
        print("          recall, remember, ingest")
        sys.exit(1)


if __name__ == "__main__":
    main()
