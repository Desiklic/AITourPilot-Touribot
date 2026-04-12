"""CRM data tools for TouriBot chat.

Gives Touri direct access to the leads database (museums, contacts,
interactions, pipeline state) during conversations.
"""
from __future__ import annotations

import os
import sqlite3

CRM_TOOLS = [
    {
        "name": "query_contacts",
        "description": (
            "Query the CRM contacts database. Returns contacts with their museum, "
            "stage, email, role, interaction count, and last activity. "
            "Use this when asked about contacts, the contact list, who is in the pipeline, "
            "or anything about specific people or museums."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "search": {
                    "type": "string",
                    "description": "Optional: search by name, email, museum name, or role",
                },
                "source": {
                    "type": "string",
                    "enum": ["hubspot", "mailerlite", "manual"],
                    "description": "Optional: filter by lead source",
                },
                "stage": {
                    "type": "integer",
                    "description": "Optional: filter by pipeline stage (0-10)",
                },
                "limit": {
                    "type": "integer",
                    "description": "Max results to return (default 50)",
                },
            },
        },
    },
    {
        "name": "query_museum",
        "description": (
            "Get detailed information about a specific museum including all contacts, "
            "interaction history, and pipeline stage. Use when discussing a specific museum."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "museum_name": {
                    "type": "string",
                    "description": "Museum name (or partial name) to look up",
                },
            },
            "required": ["museum_name"],
        },
    },
    {
        "name": "query_pipeline",
        "description": (
            "Get a summary of the pipeline: how many museums at each stage, "
            "stale contacts, upcoming follow-ups, overall stats."
        ),
        "input_schema": {
            "type": "object",
            "properties": {},
        },
    },
]


def _get_db():
    db_path = os.path.join(os.environ.get("TOURIBOT_HOME", "."), "data", "leads.db")
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def handle_crm_tool_call(tool_name: str, tool_input: dict) -> str:
    """Execute a CRM query tool."""

    if tool_name == "query_contacts":
        return _query_contacts(tool_input)
    elif tool_name == "query_museum":
        return _query_museum(tool_input)
    elif tool_name == "query_pipeline":
        return _query_pipeline()
    return f"Unknown CRM tool: {tool_name}"


def _query_contacts(inp: dict) -> str:
    try:
        conn = _get_db()
        search = inp.get("search", "")
        source = inp.get("source")
        stage = inp.get("stage")
        limit = inp.get("limit", 50)

        sql = """
            SELECT c.id, c.full_name, c.role, c.email, c.linkedin_url,
                   c.preferred_language, c.is_primary,
                   m.name as museum, m.stage, m.source, m.city, m.country,
                   (SELECT COUNT(*) FROM interactions WHERE museum_id = c.museum_id) as interactions,
                   (SELECT MAX(created_at) FROM interactions WHERE museum_id = c.museum_id) as last_activity
            FROM contacts c
            JOIN museums m ON m.id = c.museum_id
            WHERE 1=1
        """
        params = []

        if search:
            sql += " AND (c.full_name LIKE ? OR c.email LIKE ? OR m.name LIKE ? OR c.role LIKE ?)"
            q = f"%{search}%"
            params.extend([q, q, q, q])
        if source:
            sql += " AND m.source = ?"
            params.append(source)
        if stage is not None:
            sql += " AND m.stage = ?"
            params.append(stage)

        sql += " ORDER BY last_activity DESC NULLS LAST, c.full_name ASC LIMIT ?"
        params.append(limit)

        rows = conn.execute(sql, params).fetchall()
        conn.close()

        if not rows:
            return f"No contacts found" + (f" matching '{search}'" if search else "")

        lines = [f"**{len(rows)} contacts found:**\n"]
        for r in rows:
            stage_names = {
                0: "Identified", 1: "Researched", 2: "Personalized",
                3: "Outreach Sent", 4: "In Sequence", 5: "Responded",
                6: "Demo Scheduled", 7: "Demo Completed",
                8: "Proposal Sent", 9: "Negotiating", 10: "Closed",
            }
            role = f" ({r['role']})" if r['role'] else ""
            email = f" <{r['email']}>" if r['email'] else ""
            location = f", {r['city']}" if r['city'] else ""
            location += f", {r['country']}" if r['country'] else ""
            stage_label = stage_names.get(r['stage'], f"Stage {r['stage']}")
            activity = f", last activity: {r['last_activity'][:10]}" if r['last_activity'] else ", never contacted"
            interactions = f", {r['interactions']} interactions" if r['interactions'] else ""

            lines.append(
                f"- **{r['full_name']}**{role}{email} — {r['museum']}{location} "
                f"[{stage_label}] (source: {r['source']}{interactions}{activity})"
            )

        return "\n".join(lines)
    except Exception as e:
        return f"Error querying contacts: {e}"


def _query_museum(inp: dict) -> str:
    try:
        conn = _get_db()
        name = inp.get("museum_name", "")

        museum = conn.execute(
            "SELECT * FROM museums WHERE LOWER(name) LIKE ? ORDER BY id LIMIT 1",
            (f"%{name.lower()}%",),
        ).fetchone()

        if not museum:
            return f"No museum found matching '{name}'"

        mid = museum["id"]
        stage_names = {
            0: "Identified", 1: "Researched", 2: "Personalized",
            3: "Outreach Sent", 4: "In Sequence", 5: "Responded",
            6: "Demo Scheduled", 7: "Demo Completed",
            8: "Proposal Sent", 9: "Negotiating", 10: "Closed",
        }

        lines = [f"## {museum['name']}"]
        lines.append(f"Stage: {museum['stage']} — {stage_names.get(museum['stage'], '?')}")
        if museum["city"]:
            lines.append(f"Location: {museum['city']}, {museum['country'] or ''}")
        lines.append(f"Source: {museum['source'] or 'unknown'}")
        if museum["tier"]:
            lines.append(f"Tier: {museum['tier']}")
        if museum["website"]:
            lines.append(f"Website: {museum['website']}")
        if museum["notes"]:
            lines.append(f"Notes: {museum['notes']}")

        # Contacts
        contacts = conn.execute(
            "SELECT * FROM contacts WHERE museum_id = ? ORDER BY is_primary DESC, full_name",
            (mid,),
        ).fetchall()
        if contacts:
            lines.append(f"\n**Contacts ({len(contacts)}):**")
            for c in contacts:
                role = f" — {c['role']}" if c['role'] else ""
                email = f" <{c['email']}>" if c['email'] else ""
                primary = " (primary)" if c['is_primary'] else ""
                lines.append(f"- {c['full_name']}{role}{email}{primary}")

        # Interactions
        interactions = conn.execute(
            "SELECT * FROM interactions WHERE museum_id = ? ORDER BY created_at DESC LIMIT 10",
            (mid,),
        ).fetchall()
        if interactions:
            lines.append(f"\n**Interactions ({len(interactions)}):**")
            for i in interactions:
                direction = i['direction']
                event = f" ({i['event_type']})" if i['event_type'] else ""
                subject = f": {i['subject']}" if i['subject'] else ""
                date = i['created_at'][:10] if i['created_at'] else "?"
                body_preview = i['body'][:100] if i['body'] else ""
                lines.append(f"- [{date}] {direction}{event}{subject} — {body_preview}")
                if i['follow_up_date']:
                    lines.append(f"  ↳ Follow-up: {i['follow_up_date']} — {i['follow_up_action'] or ''}")

        conn.close()
        return "\n".join(lines)
    except Exception as e:
        return f"Error querying museum: {e}"


def _query_pipeline() -> str:
    try:
        conn = _get_db()
        stage_names = {
            0: "Identified", 1: "Researched", 2: "Personalized",
            3: "Outreach Sent", 4: "In Sequence", 5: "Responded",
            6: "Demo Scheduled", 7: "Demo Completed",
            8: "Proposal Sent", 9: "Negotiating", 10: "Closed",
        }

        total = conn.execute("SELECT COUNT(*) FROM museums").fetchone()[0]
        contact_count = conn.execute("SELECT COUNT(*) FROM contacts").fetchone()[0]
        interaction_count = conn.execute("SELECT COUNT(*) FROM interactions").fetchone()[0]

        stages = conn.execute(
            "SELECT stage, COUNT(*) as cnt FROM museums GROUP BY stage ORDER BY stage"
        ).fetchall()

        # Stale museums (no interaction in 5+ days for museums at stage 3+)
        stale = conn.execute("""
            SELECT m.name, m.stage,
                   julianday('now') - julianday(MAX(i.created_at)) as days_idle
            FROM museums m
            LEFT JOIN interactions i ON i.museum_id = m.id
            WHERE m.stage >= 3
            GROUP BY m.id
            HAVING days_idle > 5 OR days_idle IS NULL
            ORDER BY days_idle DESC
        """).fetchall()

        # Due follow-ups
        followups = conn.execute("""
            SELECT m.name, i.follow_up_date, i.follow_up_action
            FROM interactions i
            JOIN museums m ON m.id = i.museum_id
            WHERE i.follow_up_date IS NOT NULL
              AND i.follow_up_date <= date('now')
            ORDER BY i.follow_up_date
        """).fetchall()

        conn.close()

        lines = [f"## Pipeline Overview"]
        lines.append(f"**{total} museums** with **{contact_count} contacts** and **{interaction_count} interactions**\n")

        lines.append("**By stage:**")
        for s in stages:
            lines.append(f"- Stage {s['stage']} ({stage_names.get(s['stage'], '?')}): {s['cnt']}")

        if stale:
            lines.append(f"\n**Stale contacts ({len(stale)}):**")
            for s in stale:
                days = f"{int(s['days_idle'])}d idle" if s['days_idle'] else "never contacted"
                lines.append(f"- {s['name']} [{stage_names.get(s['stage'], '?')}] — {days}")

        if followups:
            lines.append(f"\n**Overdue follow-ups ({len(followups)}):**")
            for f in followups:
                lines.append(f"- {f['name']}: {f['follow_up_date']} — {f['follow_up_action'] or 'no action specified'}")

        return "\n".join(lines)
    except Exception as e:
        return f"Error querying pipeline: {e}"
