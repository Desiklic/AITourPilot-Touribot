"""Pipeline — Stage queries, stale detection, summary, and formatted output."""

from datetime import datetime

from rich.console import Console
from rich.table import Table
from rich.panel import Panel

from tools.leads.lead_db import (
    STAGE_NAMES, list_museums, get_pipeline_stats, get_stale_museums,
    get_contacts, get_last_interaction, get_museum, get_interaction_history,
    get_due_followups,
)

console = Console()


def pipeline_summary_text() -> str:
    """Return a one-line pipeline summary for injection into chat context."""
    stats = get_pipeline_stats()
    total = stats["total"]
    if total == 0:
        return "Pipeline: empty (no museums imported yet)"

    parts = [f"Pipeline: {total} museums total"]
    for stage in sorted(stats["by_stage"].keys()):
        count = stats["by_stage"][stage]
        name = STAGE_NAMES.get(stage, f"Stage {stage}")
        parts.append(f"Stage {stage} ({name}): {count}")

    stale = get_stale_museums(days=5)
    if stale:
        stale_names = [f"{s['name']} ({s['days_idle']}d)" for s in stale[:3]]
        parts.append(f"Stale: {', '.join(stale_names)}")

    followups = get_due_followups()
    if followups:
        parts.append(f"Follow-ups due today: {len(followups)}")

    return ". ".join(parts)


def pipeline_table(stage_filter: int = None):
    """Display the pipeline as a formatted rich table."""
    museums = list_museums(stage=stage_filter)

    if not museums:
        if stage_filter is not None:
            console.print(f"[dim]No museums at Stage {stage_filter} ({STAGE_NAMES.get(stage_filter, '?')})[/dim]")
        else:
            console.print("[dim]No museums in pipeline. Run: python run.py import-leads <csv> --source hubspot[/dim]")
        return

    title = "Museum Pipeline"
    if stage_filter is not None:
        title += f" — Stage {stage_filter}: {STAGE_NAMES.get(stage_filter, '?')}"

    table = Table(title=title, show_lines=False, padding=(0, 1), expand=True)
    table.add_column("#", style="dim", width=4, no_wrap=True)
    table.add_column("Museum", style="bold white", ratio=3)
    table.add_column("Country", style="white", ratio=1)
    table.add_column("Stage", style="cyan", width=20, no_wrap=True)
    table.add_column("Source", style="dim", width=10, no_wrap=True)
    table.add_column("Updated", style="dim", width=10, no_wrap=True)

    for m in museums:
        stage = m["stage"]
        stage_label = f"{stage} {STAGE_NAMES.get(stage, '?')}"
        updated = (m.get("stage_updated_at") or "")[:10]

        # Color code by stage
        if stage >= 6:
            style = "green"
        elif stage >= 3:
            style = "cyan"
        elif stage >= 1:
            style = "yellow"
        else:
            style = "dim"

        table.add_row(
            str(m["id"]),
            m["name"],
            m.get("country") or "",
            f"[{style}]{stage_label}[/{style}]",
            m.get("source") or "",
            updated,
        )

    console.print()
    console.print(table)

    # Summary footer
    stats = get_pipeline_stats()
    console.print(f"\n[dim]{stats['total']} museums total[/dim]")


def show_status():
    """Quick briefing: pipeline stats + stale contacts + next actions."""
    stats = get_pipeline_stats()
    total = stats["total"]

    console.print()
    console.print(Panel("[bold cyan]TouriBot Status Briefing[/bold cyan]", border_style="cyan"))

    if total == 0:
        console.print("[dim]Pipeline is empty. Import leads first:[/dim]")
        console.print("  python run.py import-leads leads/hubspot_export.csv --source hubspot")
        return

    # Stage breakdown
    console.print("\n[bold]Pipeline Overview[/bold]")
    for stage in sorted(stats["by_stage"].keys()):
        count = stats["by_stage"][stage]
        name = STAGE_NAMES.get(stage, "?")
        bar = "█" * count
        console.print(f"  Stage {stage:2d} ({name:16s}): {count:3d} {bar}")

    console.print(f"\n  [bold]Total: {total} museums[/bold]")

    # Source breakdown
    if stats["by_source"]:
        sources = ", ".join(f"{k}: {v}" for k, v in stats["by_source"].items())
        console.print(f"  Sources: {sources}")

    # Follow-ups due
    followups = get_due_followups()
    if followups:
        console.print(f"\n[bold red]Follow-ups Due Today ({len(followups)})[/bold red]")
        for f in followups:
            stage_name = STAGE_NAMES.get(f["stage"], "?")
            action = f.get("follow_up_action") or "follow up"
            console.print(f"  [red]![/red] {f['museum_name']} (Stage {f['stage']}, {stage_name}) — {action} [dim](due {f['follow_up_date']})[/dim]")
    else:
        console.print("\n[green]No follow-ups due today[/green]")

    # Stale contacts
    stale = get_stale_museums(days=5)
    if stale:
        console.print(f"\n[bold yellow]Stale Contacts ({len(stale)} museums idle >5 days)[/bold yellow]")
        for s in stale[:5]:
            stage_name = STAGE_NAMES.get(s["stage"], "?")
            console.print(f"  {s['name']} — Stage {s['stage']} ({stage_name}), {s['days_idle']} days idle")
    else:
        console.print("\n[green]No stale contacts[/green]")

    # Next actions
    console.print(f"\n[bold]Suggested Next Actions[/bold]")
    actions = next_actions()
    if actions:
        for a in actions[:5]:
            console.print(f"  → {a}")
    else:
        console.print("  [dim]No pending actions[/dim]")

    console.print()


def next_actions() -> list[str]:
    """Suggest what Hermann should do next based on pipeline state."""
    actions = []
    museums = list_museums()

    stage_0 = [m for m in museums if m["stage"] == 0 and m.get("source") == "hubspot"]
    if stage_0:
        actions.append(f"Research {min(len(stage_0), 3)} Stage 0 museums: {', '.join(m['name'] for m in stage_0[:3])}")

    stage_2 = [m for m in museums if m["stage"] == 2]
    if stage_2:
        actions.append(f"Draft emails for {len(stage_2)} personalized leads: {', '.join(m['name'] for m in stage_2[:3])}")

    stage_3 = [m for m in museums if m["stage"] == 3]
    if stage_3:
        actions.append(f"Check for replies from {len(stage_3)} Stage 3 (Outreach Sent) museums")

    stale = get_stale_museums(days=5)
    if stale:
        actions.append(f"Follow up with {len(stale)} stale contacts (>5 days idle)")

    stage_5 = [m for m in museums if m["stage"] == 5]
    if stage_5:
        actions.append(f"Act on {len(stage_5)} responded leads: {', '.join(m['name'] for m in stage_5[:3])}")

    if not actions:
        stage_counts = {}
        for m in museums:
            stage_counts[m["stage"]] = stage_counts.get(m["stage"], 0) + 1
        if stage_counts.get(0, 0) > 0:
            actions.append("Start researching Stage 0 leads to build pipeline momentum")

    return actions


# ── Event type display labels ──────────────────────────────

_EVENT_ICONS = {
    "email_sent": "📤",
    "email_received": "📥",
    "meeting_scheduled": "📅",
    "meeting_held": "🤝",
    "meeting_noshow": "❌",
    "linkedin_connection": "🔗",
    "linkedin_message": "💬",
    "phone_call": "📞",
    "referral": "🔀",
    "note": "📝",
    "prep": "📋",
}


def show_history(museum_name: str):
    """Display full chronological interaction timeline for a museum."""
    museum = get_museum(museum_name)
    if not museum:
        console.print(f"[red]Museum not found:[/red] {museum_name}")
        return

    contacts = get_contacts(museum["id"])
    history = get_interaction_history(museum["id"])

    # Header
    stage = museum["stage"]
    stage_label = f"Stage {stage}: {STAGE_NAMES.get(stage, '?')}"
    console.print()
    console.print(Panel(
        f"[bold]{museum['name']}[/bold]\n"
        f"{museum.get('city') or ''} {museum.get('country') or ''}  |  {stage_label}  |  Source: {museum.get('source', '?')}"
        + (f"\nSource detail: {museum['source_detail']}" if museum.get('source_detail') else ""),
        border_style="cyan",
    ))

    # Contacts
    if contacts:
        console.print("[bold]Contacts:[/bold]")
        for c in contacts:
            primary = " [yellow](primary)[/yellow]" if c.get("is_primary") else ""
            role = f" — {c['role']}" if c.get("role") else ""
            email = f" ({c['email']})" if c.get("email") else ""
            console.print(f"  {c['full_name']}{role}{email}{primary}")
        console.print()

    # Timeline
    if not history:
        console.print("[dim]No interactions recorded yet.[/dim]\n")
        return

    console.print("[bold]Timeline:[/bold]\n")
    for event in history:
        ts = (event.get("created_at") or "")[:16].replace("T", " ")
        event_type = event.get("event_type") or event.get("channel") or "?"
        icon = _EVENT_ICONS.get(event_type, "•")
        direction = event.get("direction", "")

        # Build the display label
        if event_type in _EVENT_ICONS:
            label = event_type.replace("_", " ").upper()
        else:
            label = f"{direction.upper()} ({event.get('channel', '?')})"

        body = (event.get("body") or "").strip()
        # Truncate long bodies for display
        if len(body) > 200:
            body = body[:200] + "..."

        console.print(f"  [dim]{ts}[/dim]  {icon} [bold]{label}[/bold]")
        if body:
            # Indent body lines
            for line in body.split("\n")[:5]:
                console.print(f"    {line}")

        if event.get("outcome"):
            console.print(f"    [green]Outcome:[/green] {event['outcome']}")
        if event.get("follow_up_date"):
            console.print(f"    [yellow]Follow-up {event['follow_up_date']}:[/yellow] {event.get('follow_up_action', '')}")
        if event.get("attachments"):
            console.print(f"    [dim]Attachments: {event['attachments']}[/dim]")

        console.print()

    console.print(f"[dim]{len(history)} events total[/dim]\n")
