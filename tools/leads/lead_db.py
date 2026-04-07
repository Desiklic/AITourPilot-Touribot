"""Lead Database — SQLite CRUD for museums, contacts, interactions, research.

Schema matches ARCHITECTURE.md Section C1 exactly.
"""

import csv
import logging
import sqlite3
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)

DB_PATH = Path(__file__).parent.parent.parent / "data" / "leads.db"

STAGE_NAMES = {
    0: "Identified",
    1: "Researched",
    2: "Personalized",
    3: "Outreach Sent",
    4: "In Sequence",
    5: "Responded",
    6: "Demo Scheduled",
    7: "Demo Completed",
    8: "Proposal Sent",
    9: "Negotiating",
    10: "Closed",
}


def init_db() -> sqlite3.Connection:
    """Initialize leads database with schema. Idempotent."""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS museums (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            name            TEXT NOT NULL,
            city            TEXT,
            country         TEXT,
            country_code    TEXT,
            website         TEXT,
            annual_visitors INTEGER,
            current_audioguide TEXT,
            digital_maturity TEXT,
            tier            INTEGER DEFAULT 2,
            source          TEXT,
            stage           INTEGER DEFAULT 0,
            stage_updated_at TEXT,
            score           INTEGER,
            notes           TEXT,
            created_at      TEXT DEFAULT (datetime('now')),
            updated_at      TEXT DEFAULT (datetime('now'))
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS contacts (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            museum_id       INTEGER NOT NULL REFERENCES museums(id),
            first_name      TEXT,
            last_name       TEXT,
            full_name       TEXT NOT NULL,
            role            TEXT,
            email           TEXT,
            linkedin_url    TEXT,
            preferred_language TEXT DEFAULT 'en',
            notes           TEXT,
            is_primary      INTEGER DEFAULT 1,
            created_at      TEXT DEFAULT (datetime('now'))
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS interactions (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            museum_id       INTEGER NOT NULL REFERENCES museums(id),
            contact_id      INTEGER REFERENCES contacts(id),
            direction       TEXT NOT NULL,
            channel         TEXT NOT NULL,
            subject         TEXT,
            body            TEXT NOT NULL,
            sequence_step   INTEGER,
            response_score  INTEGER,
            sent_at         TEXT,
            created_at      TEXT DEFAULT (datetime('now')),
            is_draft        INTEGER DEFAULT 1
        )
    """)

    # ── Schema migrations (idempotent ALTER TABLE for existing DBs) ──
    _migrate_interactions(conn)
    _migrate_museums(conn)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS research (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            museum_id       INTEGER NOT NULL REFERENCES museums(id),
            insights        TEXT,
            hypothesis      TEXT,
            hook_line       TEXT,
            conversation_starter TEXT,
            sources         TEXT,
            created_at      TEXT DEFAULT (datetime('now')),
            is_current      INTEGER DEFAULT 1
        )
    """)

    conn.commit()
    return conn


def _migrate_interactions(conn: sqlite3.Connection):
    """Add CRM fields to interactions table if missing."""
    existing = {r[1] for r in conn.execute("PRAGMA table_info(interactions)").fetchall()}
    migrations = [
        ("event_type", "TEXT"),           # email_sent, meeting_scheduled, meeting_noshow, etc.
        ("attachments", "TEXT"),           # JSON array of file paths
        ("outcome", "TEXT"),              # What happened as a result
        ("follow_up_date", "TEXT"),       # ISO date: when to follow up
        ("follow_up_action", "TEXT"),     # What to do on follow-up
    ]
    for col, col_type in migrations:
        if col not in existing:
            conn.execute(f"ALTER TABLE interactions ADD COLUMN {col} {col_type}")
    conn.commit()


def _migrate_museums(conn: sqlite3.Connection):
    """Add source_detail field to museums table if missing."""
    existing = {r[1] for r in conn.execute("PRAGMA table_info(museums)").fetchall()}
    if "source_detail" not in existing:
        conn.execute("ALTER TABLE museums ADD COLUMN source_detail TEXT")
        conn.commit()


# ── Museum CRUD ────────────────────────────────────────────


def add_museum(name: str, city: str = None, country: str = None,
               source: str = "manual", **kwargs) -> dict:
    """Add a museum. Returns the new record."""
    conn = init_db()
    now = datetime.now().isoformat()
    cursor = conn.cursor()
    cursor.execute(
        """INSERT INTO museums (name, city, country, country_code, website,
           annual_visitors, current_audioguide, digital_maturity, tier,
           source, stage, stage_updated_at, notes, source_detail,
           created_at, updated_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0, ?, ?, ?, ?, ?)""",
        (name, city, country, kwargs.get("country_code"),
         kwargs.get("website"), kwargs.get("annual_visitors"),
         kwargs.get("current_audioguide"), kwargs.get("digital_maturity"),
         kwargs.get("tier", 2), source, now, kwargs.get("notes"),
         kwargs.get("source_detail"), now, now),
    )
    conn.commit()
    museum_id = cursor.lastrowid
    conn.close()
    return {"id": museum_id, "name": name, "stage": 0, "source": source}


def get_museum(name: str) -> dict | None:
    """Find a museum by name (case-insensitive partial match)."""
    conn = init_db()
    row = conn.execute(
        "SELECT * FROM museums WHERE LOWER(name) LIKE ? ORDER BY id LIMIT 1",
        (f"%{name.lower()}%",),
    ).fetchone()
    conn.close()
    if not row:
        return None
    cols = ["id", "name", "city", "country", "country_code", "website",
            "annual_visitors", "current_audioguide", "digital_maturity",
            "tier", "source", "stage", "stage_updated_at", "score",
            "notes", "created_at", "updated_at"]
    return dict(zip(cols, row))


def get_museum_by_id(museum_id: int) -> dict | None:
    """Find a museum by ID."""
    conn = init_db()
    row = conn.execute("SELECT * FROM museums WHERE id = ?", (museum_id,)).fetchone()
    conn.close()
    if not row:
        return None
    cols = ["id", "name", "city", "country", "country_code", "website",
            "annual_visitors", "current_audioguide", "digital_maturity",
            "tier", "source", "stage", "stage_updated_at", "score",
            "notes", "created_at", "updated_at"]
    return dict(zip(cols, row))


def list_museums(stage: int = None) -> list[dict]:
    """List all museums, optionally filtered by stage."""
    conn = init_db()
    if stage is not None:
        rows = conn.execute(
            "SELECT id, name, city, country, stage, stage_updated_at, source, score "
            "FROM museums WHERE stage = ? ORDER BY name", (stage,)
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT id, name, city, country, stage, stage_updated_at, source, score "
            "FROM museums ORDER BY stage DESC, name"
        ).fetchall()
    conn.close()
    cols = ["id", "name", "city", "country", "stage", "stage_updated_at", "source", "score"]
    return [dict(zip(cols, r)) for r in rows]


def update_stage(museum_name: str, new_stage: int, force: bool = False) -> dict:
    """Advance a museum's pipeline stage. Only allows forward movement unless force=True."""
    museum = get_museum(museum_name)
    if not museum:
        raise ValueError(f"Museum not found: {museum_name}")

    current = museum["stage"]
    if new_stage <= current and not force:
        raise ValueError(
            f"{museum['name']} is at Stage {current} ({STAGE_NAMES.get(current, '?')}). "
            f"Cannot move backward to Stage {new_stage} without --force."
        )

    now = datetime.now().isoformat()
    conn = init_db()
    conn.execute(
        "UPDATE museums SET stage = ?, stage_updated_at = ?, updated_at = ? WHERE id = ?",
        (new_stage, now, now, museum["id"]),
    )
    # Log stage transition as interaction
    conn.execute(
        """INSERT INTO interactions (museum_id, direction, channel, body, created_at)
           VALUES (?, 'internal', 'system', ?, ?)""",
        (museum["id"],
         f"Stage transition: {current} ({STAGE_NAMES.get(current, '?')}) → {new_stage} ({STAGE_NAMES.get(new_stage, '?')})",
         now),
    )
    conn.commit()
    conn.close()
    return {"museum": museum["name"], "old_stage": current, "new_stage": new_stage,
            "stage_name": STAGE_NAMES.get(new_stage, "?")}


# ── Contact CRUD ───────────────────────────────────────────


def add_contact(museum_id: int, full_name: str, email: str = None,
                **kwargs) -> dict:
    """Add a contact linked to a museum."""
    # Split name into first/last
    parts = full_name.strip().split(None, 1)
    first_name = parts[0] if parts else full_name
    last_name = parts[1] if len(parts) > 1 else None

    conn = init_db()
    cursor = conn.cursor()
    cursor.execute(
        """INSERT INTO contacts (museum_id, first_name, last_name, full_name,
           role, email, linkedin_url, preferred_language, notes, is_primary)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (museum_id, first_name, last_name, full_name,
         kwargs.get("role"), email, kwargs.get("linkedin_url"),
         kwargs.get("preferred_language", "en"), kwargs.get("notes"),
         kwargs.get("is_primary", 1)),
    )
    conn.commit()
    contact_id = cursor.lastrowid
    conn.close()
    return {"id": contact_id, "museum_id": museum_id, "full_name": full_name, "email": email}


def get_contacts(museum_id: int) -> list[dict]:
    """Get all contacts for a museum."""
    conn = init_db()
    rows = conn.execute(
        "SELECT id, full_name, role, email, linkedin_url, preferred_language, is_primary "
        "FROM contacts WHERE museum_id = ? ORDER BY is_primary DESC",
        (museum_id,),
    ).fetchall()
    conn.close()
    cols = ["id", "full_name", "role", "email", "linkedin_url", "preferred_language", "is_primary"]
    return [dict(zip(cols, r)) for r in rows]


def find_contact_by_email(email: str) -> dict | None:
    """Find a contact by email address."""
    conn = init_db()
    row = conn.execute(
        "SELECT id, museum_id, full_name, email FROM contacts WHERE LOWER(email) = ?",
        (email.lower(),),
    ).fetchone()
    conn.close()
    if not row:
        return None
    return {"id": row[0], "museum_id": row[1], "full_name": row[2], "email": row[3]}


# ── Interaction CRUD ───────────────────────────────────────


def add_interaction(museum_id: int, direction: str, channel: str,
                    body: str, **kwargs) -> dict:
    """Log an interaction (email sent, reply received, meeting, note, etc.)."""
    conn = init_db()
    cursor = conn.cursor()
    cursor.execute(
        """INSERT INTO interactions (museum_id, contact_id, direction, channel,
           subject, body, sequence_step, response_score, sent_at, is_draft,
           event_type, attachments, outcome, follow_up_date, follow_up_action)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (museum_id, kwargs.get("contact_id"), direction, channel,
         kwargs.get("subject"), body, kwargs.get("sequence_step"),
         kwargs.get("response_score"), kwargs.get("sent_at"),
         kwargs.get("is_draft", 1),
         kwargs.get("event_type"), kwargs.get("attachments"),
         kwargs.get("outcome"), kwargs.get("follow_up_date"),
         kwargs.get("follow_up_action")),
    )
    conn.commit()
    interaction_id = cursor.lastrowid
    conn.close()
    return {"id": interaction_id, "museum_id": museum_id, "direction": direction}


def get_last_interaction(museum_id: int) -> dict | None:
    """Get the most recent interaction for a museum."""
    conn = init_db()
    row = conn.execute(
        """SELECT id, direction, channel, subject, body, created_at, is_draft
           FROM interactions WHERE museum_id = ?
           ORDER BY created_at DESC LIMIT 1""",
        (museum_id,),
    ).fetchone()
    conn.close()
    if not row:
        return None
    cols = ["id", "direction", "channel", "subject", "body", "created_at", "is_draft"]
    return dict(zip(cols, row))


# ── CSV Import ─────────────────────────────────────────────


def import_csv(filepath: str, source: str = "hubspot") -> dict:
    """Import contacts from a CSV file.

    Supports:
    - HubSpot: semicolon-delimited, columns: First name, Email address, Company name, LinkedIn
    - MailerLite: comma-delimited, columns: Subscriber (email), Location

    Skips rows where the email already exists. Creates museum if company name is new.
    """
    path = Path(filepath)
    if not path.exists():
        raise FileNotFoundError(f"CSV not found: {filepath}")

    imported = 0
    skipped = 0
    museums_created = 0

    if source == "hubspot":
        imported, skipped, museums_created = _import_hubspot(path)
    elif source == "mailerlite":
        imported, skipped, museums_created = _import_mailerlite(path)
    else:
        raise ValueError(f"Unknown source: {source}. Use 'hubspot' or 'mailerlite'.")

    return {"imported": imported, "skipped": skipped, "museums_created": museums_created,
            "source": source}


def _import_hubspot(path: Path) -> tuple[int, int, int]:
    """Import HubSpot CSV (semicolon-delimited)."""
    imported = skipped = museums_created = 0

    # Read with BOM handling
    text = path.read_text(encoding="utf-8-sig")
    reader = csv.DictReader(text.splitlines(), delimiter=";")

    for row in reader:
        email = (row.get("Email address") or "").strip()
        name = (row.get("First name") or "").strip()
        company = (row.get("Company name") or "").strip()
        linkedin = (row.get("LinkedIn Contact Link") or "").strip()

        if not email or not company:
            skipped += 1
            continue

        # Skip if email already exists
        if find_contact_by_email(email):
            skipped += 1
            continue

        # Find or create museum
        museum = get_museum(company)
        if not museum:
            result = add_museum(name=company, source="hubspot")
            museum = get_museum_by_id(result["id"])
            museums_created += 1

        # Add contact
        add_contact(
            museum_id=museum["id"],
            full_name=name or email.split("@")[0],
            email=email,
            linkedin_url=linkedin if linkedin else None,
        )
        imported += 1

    return imported, skipped, museums_created


def _import_mailerlite(path: Path) -> tuple[int, int, int]:
    """Import MailerLite CSV (comma-delimited)."""
    imported = skipped = museums_created = 0

    text = path.read_text(encoding="utf-8-sig")
    reader = csv.DictReader(text.splitlines())

    for row in reader:
        email = (row.get("Subscriber") or "").strip()
        location = (row.get("Location") or "").strip()

        if not email:
            skipped += 1
            continue

        if find_contact_by_email(email):
            skipped += 1
            continue

        # MailerLite has no company name — use email domain as museum placeholder
        domain = email.split("@")[1] if "@" in email else "unknown"
        museum_name = f"MailerLite: {domain}"

        museum = get_museum(museum_name)
        if not museum:
            result = add_museum(name=museum_name, country=location, source="mailerlite")
            museum = get_museum_by_id(result["id"])
            museums_created += 1

        name_from_email = email.split("@")[0].replace(".", " ").replace("_", " ").title()
        add_contact(
            museum_id=museum["id"],
            full_name=name_from_email,
            email=email,
        )
        imported += 1

    return imported, skipped, museums_created


# ── Stats ──────────────────────────────────────────────────


def get_pipeline_stats() -> dict:
    """Get aggregate pipeline statistics."""
    conn = init_db()
    total = conn.execute("SELECT COUNT(*) FROM museums").fetchone()[0]
    by_stage = dict(conn.execute(
        "SELECT stage, COUNT(*) FROM museums GROUP BY stage ORDER BY stage"
    ).fetchall())
    by_source = dict(conn.execute(
        "SELECT source, COUNT(*) FROM museums GROUP BY source"
    ).fetchall())
    conn.close()
    return {"total": total, "by_stage": by_stage, "by_source": by_source}


def get_interaction_history(museum_id: int) -> list[dict]:
    """Get full chronological interaction timeline for a museum."""
    conn = init_db()
    rows = conn.execute(
        """SELECT id, direction, channel, subject, body, created_at, is_draft,
                  event_type, attachments, outcome, follow_up_date, follow_up_action,
                  contact_id, response_score, sent_at
           FROM interactions WHERE museum_id = ?
           ORDER BY created_at ASC""",
        (museum_id,),
    ).fetchall()
    conn.close()
    cols = ["id", "direction", "channel", "subject", "body", "created_at", "is_draft",
            "event_type", "attachments", "outcome", "follow_up_date", "follow_up_action",
            "contact_id", "response_score", "sent_at"]
    return [dict(zip(cols, r)) for r in rows]


def get_due_followups(as_of: str = None) -> list[dict]:
    """Get interactions with follow_up_date <= today (or as_of date)."""
    if as_of is None:
        as_of = datetime.now().strftime("%Y-%m-%d")
    conn = init_db()
    rows = conn.execute(
        """SELECT i.id, i.museum_id, m.name as museum_name, i.follow_up_date,
                  i.follow_up_action, i.event_type, i.body, m.stage
           FROM interactions i
           JOIN museums m ON m.id = i.museum_id
           WHERE i.follow_up_date IS NOT NULL AND i.follow_up_date <= ?
           ORDER BY i.follow_up_date ASC""",
        (as_of,),
    ).fetchall()
    conn.close()
    cols = ["id", "museum_id", "museum_name", "follow_up_date",
            "follow_up_action", "event_type", "body", "stage"]
    return [dict(zip(cols, r)) for r in rows]


def get_stale_museums(days: int = 5) -> list[dict]:
    """Find museums where the last activity is older than N days."""
    conn = init_db()
    # Museums at stages 1-9 (not 0=just identified, not 10=closed)
    # with stage_updated_at older than N days ago
    rows = conn.execute(
        """SELECT m.id, m.name, m.stage, m.stage_updated_at,
                  (julianday('now') - julianday(COALESCE(m.stage_updated_at, m.created_at))) as days_idle
           FROM museums m
           WHERE m.stage BETWEEN 1 AND 9
             AND (julianday('now') - julianday(COALESCE(m.stage_updated_at, m.created_at))) > ?
           ORDER BY days_idle DESC""",
        (days,),
    ).fetchall()
    conn.close()
    return [{"id": r[0], "name": r[1], "stage": r[2],
             "stage_updated_at": r[3], "days_idle": int(r[4])} for r in rows]
