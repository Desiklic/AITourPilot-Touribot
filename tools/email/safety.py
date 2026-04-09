"""Email safety guardrails — kill switch, rate limits, dedup, audit log.

Phase E2 — Safety infrastructure that must exist before any send capability
is ever built.  Every safety control is enforced at the system level (config
files, database checks, code-level guards) — NEVER as conversational
instructions that could be lost to context compaction (the OpenClaw lesson).

CRITICAL RULES (enforced in code, not config):
1.  .com account NEVER gets automated send capability (hard check in queue_email).
2.  Kill switch (automated_send_enabled: false) is read from settings.yaml at
    execution time — it is NOT cached or stored in LLM context.
3.  Rate limits are HARDCODED minimums; config can only make them stricter.
4.  Every email action (queue, approve, send, cancel, block) is written to the
    email_audit_log table — this log is append-only.
5.  Content hash dedup prevents the same email from being queued twice within
    30 days.
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
import sqlite3
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Database setup
# ---------------------------------------------------------------------------

_PROJECT_ROOT = Path(__file__).parent.parent.parent


def _get_db() -> sqlite3.Connection:
    """Open leads.db and ensure email safety tables exist."""
    db_path = _PROJECT_ROOT / "data" / "leads.db"
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    _ensure_schema(conn)
    return conn


def _ensure_schema(conn: sqlite3.Connection) -> None:
    """Create email_queue and email_audit_log tables if they don't exist."""
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS email_queue (
            id               INTEGER PRIMARY KEY AUTOINCREMENT,
            museum_id        INTEGER NOT NULL,
            contact_id       INTEGER,
            from_account     TEXT NOT NULL CHECK(from_account IN ('com', 'co')),
            subject          TEXT NOT NULL,
            body             TEXT NOT NULL,
            draft_file_path  TEXT,
            status           TEXT DEFAULT 'PENDING_APPROVAL'
                             CHECK(status IN (
                                 'PENDING_APPROVAL',
                                 'APPROVED',
                                 'SENDING',
                                 'SENT',
                                 'FAILED',
                                 'CANCELLED'
                             )),
            approved_at      TEXT,
            sent_at          TEXT,
            error_message    TEXT,
            content_hash     TEXT,
            created_at       TEXT DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS email_audit_log (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            queue_id   INTEGER REFERENCES email_queue(id),
            action     TEXT NOT NULL,
            actor      TEXT,
            details    TEXT,
            created_at TEXT DEFAULT (datetime('now'))
        );

        CREATE INDEX IF NOT EXISTS idx_email_queue_status
            ON email_queue(status);
        CREATE INDEX IF NOT EXISTS idx_email_queue_from_account
            ON email_queue(from_account, created_at);
        CREATE INDEX IF NOT EXISTS idx_email_audit_queue_id
            ON email_audit_log(queue_id);
        CREATE INDEX IF NOT EXISTS idx_email_audit_action
            ON email_audit_log(action);
    """)
    conn.commit()


# ---------------------------------------------------------------------------
# Kill switch
# ---------------------------------------------------------------------------


def is_send_enabled() -> bool:
    """Check if automated email sending is enabled (the kill switch).

    Reads settings.yaml at call time — NOT cached, NOT from LLM context.
    Returns False (disabled) on any read error, so failure is safe.
    """
    try:
        import yaml  # PyYAML is in requirements

        settings_path = _PROJECT_ROOT / "args" / "settings.yaml"
        with open(settings_path) as f:
            settings = yaml.safe_load(f) or {}
        return bool(settings.get("email", {}).get("automated_send_enabled", False))
    except Exception as exc:
        logger.warning("Could not read kill switch from settings.yaml: %s", exc)
        return False  # Fail closed


# ---------------------------------------------------------------------------
# Rate limiting
# ---------------------------------------------------------------------------

# HARDCODED floors — code enforces max(hardcoded_limit, config_limit)
_HARDCODED_LIMITS = {"com": 3, "co": 20}


def check_rate_limit(from_account: str) -> dict:
    """Check whether the daily send limit has been reached for this account.

    Args:
        from_account: "com" or "co"

    Returns:
        {
            "allowed": bool,
            "sent_today": int,
            "limit": int,
            "account": str,
        }
    """
    hardcoded = _HARDCODED_LIMITS.get(from_account, 3)

    # Also read config limit (config can only restrict, not relax below hardcoded)
    config_limit = _read_config_limit(from_account)
    effective_limit = max(hardcoded, config_limit)

    conn = _get_db()
    today = datetime.now().strftime("%Y-%m-%d")
    try:
        sent_today = conn.execute(
            """SELECT COUNT(*) FROM email_queue
               WHERE from_account = ?
                 AND date(sent_at) = ?
                 AND status = 'SENT'""",
            (from_account, today),
        ).fetchone()[0]
    finally:
        conn.close()

    return {
        "allowed": sent_today < effective_limit,
        "sent_today": sent_today,
        "limit": effective_limit,
        "account": from_account,
    }


def _read_config_limit(from_account: str) -> int:
    """Read per-account daily limit from settings.yaml. Returns hardcoded floor on failure."""
    try:
        import yaml

        settings_path = _PROJECT_ROOT / "args" / "settings.yaml"
        with open(settings_path) as f:
            settings = yaml.safe_load(f) or {}
        email_cfg = settings.get("email", {})
        if from_account == "com":
            return int(email_cfg.get("daily_limit_com", _HARDCODED_LIMITS["com"]))
        elif from_account == "co":
            return int(email_cfg.get("daily_limit_co", _HARDCODED_LIMITS["co"]))
    except Exception:
        pass
    return _HARDCODED_LIMITS.get(from_account, 3)


# ---------------------------------------------------------------------------
# Duplicate detection
# ---------------------------------------------------------------------------


def check_duplicate(
    contact_email: str, subject: str, body: str
) -> dict:
    """Check for duplicate sends: same recipient (7 days) or same content hash (30 days).

    Args:
        contact_email: Recipient email address.
        subject:       Email subject line.
        body:          Email body text.

    Returns:
        {"duplicate": False, "content_hash": "..."} if clean.
        {"duplicate": True, "reason": "..."} if duplicate detected.
    """
    content_hash = _make_hash(contact_email, subject, body)

    conn = _get_db()
    try:
        # Recipient dedup: any queued/sent email to this address in the last 7 days
        recent = conn.execute(
            """SELECT COUNT(*) FROM email_queue eq
               JOIN contacts c ON c.id = eq.contact_id
               WHERE LOWER(c.email) = LOWER(?)
                 AND eq.status IN ('PENDING_APPROVAL', 'APPROVED', 'SENDING', 'SENT')
                 AND eq.created_at > datetime('now', '-7 days')""",
            (contact_email,),
        ).fetchone()[0]

        if recent > 0:
            return {
                "duplicate": True,
                "reason": f"Already emailed {contact_email} within the last 7 days",
            }

        # Content fingerprint dedup: same hash in last 30 days
        hash_match = conn.execute(
            """SELECT COUNT(*) FROM email_queue
               WHERE content_hash = ?
                 AND created_at > datetime('now', '-30 days')""",
            (content_hash,),
        ).fetchone()[0]

        if hash_match > 0:
            return {
                "duplicate": True,
                "reason": "Identical content hash found within the last 30 days",
            }

    finally:
        conn.close()

    return {"duplicate": False, "content_hash": content_hash}


def _make_hash(contact_email: str, subject: str, body: str) -> str:
    """SHA-256 fingerprint of contact + subject + first 100 chars of body."""
    fingerprint = f"{contact_email.lower()}|{subject}|{body[:100]}"
    return hashlib.sha256(fingerprint.encode("utf-8")).hexdigest()


# ---------------------------------------------------------------------------
# Queue management
# ---------------------------------------------------------------------------


def queue_email(
    museum_id: int,
    contact_id: int | None,
    from_account: str,
    subject: str,
    body: str,
    draft_path: str | None = None,
) -> dict:
    """Add an email to the approval queue.

    HARD CONSTRAINT: .com account always starts as PENDING_APPROVAL and
    can NEVER be auto-approved by any path through this code.

    Args:
        museum_id:    ID of the museum this email targets.
        contact_id:   ID of the contact (may be None if unknown).
        from_account: "com" or "co".
        subject:      Email subject.
        body:         Email body text.
        draft_path:   Path to saved draft file (optional).

    Returns:
        {"queue_id": int, "status": "PENDING_APPROVAL"}
    """
    if from_account not in ("com", "co"):
        raise ValueError(f"from_account must be 'com' or 'co', got: {from_account!r}")

    # .com is ALWAYS manual — this is a code-level constraint, not config
    # (even if someone sets automated_send_enabled=true, .com stays manual)
    status = "PENDING_APPROVAL"

    content_hash = _make_hash(
        str(contact_id or museum_id), subject, body
    )

    conn = _get_db()
    try:
        cursor = conn.execute(
            """INSERT INTO email_queue
               (museum_id, contact_id, from_account, subject, body,
                draft_file_path, status, content_hash, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))""",
            (
                museum_id,
                contact_id,
                from_account,
                subject,
                body,
                draft_path,
                status,
                content_hash,
            ),
        )
        queue_id = cursor.lastrowid

        # Audit log — immutable append
        conn.execute(
            """INSERT INTO email_audit_log (queue_id, action, actor, details)
               VALUES (?, 'QUEUED', 'touri', ?)""",
            (
                queue_id,
                json.dumps(
                    {
                        "from_account": from_account,
                        "subject": subject,
                        "museum_id": museum_id,
                        "contact_id": contact_id,
                    }
                ),
            ),
        )
        conn.commit()
    finally:
        conn.close()

    return {"queue_id": queue_id, "status": status}


def get_queue(status: str | None = None, limit: int = 50) -> list[dict]:
    """Return queued emails, optionally filtered by status.

    Args:
        status: Filter to this status string (e.g. 'PENDING_APPROVAL').
        limit:  Maximum rows to return.

    Returns:
        List of queue row dicts.
    """
    conn = _get_db()
    try:
        if status:
            rows = conn.execute(
                """SELECT id, museum_id, contact_id, from_account, subject,
                          body, draft_file_path, status, approved_at, sent_at,
                          error_message, content_hash, created_at
                   FROM email_queue
                   WHERE status = ?
                   ORDER BY created_at DESC
                   LIMIT ?""",
                (status, limit),
            ).fetchall()
        else:
            rows = conn.execute(
                """SELECT id, museum_id, contact_id, from_account, subject,
                          body, draft_file_path, status, approved_at, sent_at,
                          error_message, content_hash, created_at
                   FROM email_queue
                   ORDER BY created_at DESC
                   LIMIT ?""",
                (limit,),
            ).fetchall()

        cols = [
            "id", "museum_id", "contact_id", "from_account", "subject",
            "body", "draft_file_path", "status", "approved_at", "sent_at",
            "error_message", "content_hash", "created_at",
        ]
        return [dict(zip(cols, r)) for r in rows]
    finally:
        conn.close()


def update_queue_status(
    queue_id: int,
    new_status: str,
    actor: str = "system",
    error_message: str | None = None,
) -> dict:
    """Update the status of a queued email.

    Args:
        queue_id:      Row ID in email_queue.
        new_status:    Target status (APPROVED, CANCELLED, SENT, FAILED, etc.).
        actor:         Who made the change ("hermann", "system", "touri").
        error_message: Optional error detail (for FAILED status).

    Returns:
        {"queue_id": int, "status": new_status}
    """
    valid_statuses = {
        "PENDING_APPROVAL", "APPROVED", "SENDING", "SENT", "FAILED", "CANCELLED"
    }
    if new_status not in valid_statuses:
        raise ValueError(f"Invalid status: {new_status!r}")

    now = datetime.now().isoformat()
    conn = _get_db()
    try:
        # Update timestamp fields depending on transition
        if new_status == "APPROVED":
            conn.execute(
                "UPDATE email_queue SET status = ?, approved_at = ? WHERE id = ?",
                (new_status, now, queue_id),
            )
        elif new_status == "SENT":
            conn.execute(
                "UPDATE email_queue SET status = ?, sent_at = ? WHERE id = ?",
                (new_status, now, queue_id),
            )
        elif new_status == "FAILED" and error_message:
            conn.execute(
                "UPDATE email_queue SET status = ?, error_message = ? WHERE id = ?",
                (new_status, error_message, queue_id),
            )
        else:
            conn.execute(
                "UPDATE email_queue SET status = ? WHERE id = ?",
                (new_status, queue_id),
            )

        # Audit log
        conn.execute(
            """INSERT INTO email_audit_log (queue_id, action, actor, details)
               VALUES (?, ?, ?, ?)""",
            (
                queue_id,
                new_status,
                actor,
                json.dumps({"error_message": error_message}) if error_message else None,
            ),
        )
        conn.commit()
    finally:
        conn.close()

    return {"queue_id": queue_id, "status": new_status}


# ---------------------------------------------------------------------------
# Audit log
# ---------------------------------------------------------------------------


def audit_log(
    queue_id: int | None,
    action: str,
    actor: str = "system",
    details: dict | None = None,
) -> None:
    """Append an entry to the email audit log.

    This is the append-only audit trail.  Every email-related action should
    call this function so there is a complete history of what happened and why.

    Args:
        queue_id: Related email_queue row (None for system-level events).
        action:   Short action label (QUEUED, APPROVED, SENT, CANCELLED, etc.).
        actor:    Who performed the action.
        details:  Optional JSON-serialisable dict with extra context.
    """
    conn = _get_db()
    try:
        conn.execute(
            """INSERT INTO email_audit_log (queue_id, action, actor, details)
               VALUES (?, ?, ?, ?)""",
            (
                queue_id,
                action,
                actor,
                json.dumps(details) if details else None,
            ),
        )
        conn.commit()
    finally:
        conn.close()


def get_audit_log(queue_id: int | None = None, limit: int = 100) -> list[dict]:
    """Return audit log entries, optionally filtered by queue_id.

    Args:
        queue_id: If provided, only return entries for this email.
        limit:    Maximum rows to return.

    Returns:
        List of audit log dicts.
    """
    conn = _get_db()
    try:
        if queue_id is not None:
            rows = conn.execute(
                """SELECT id, queue_id, action, actor, details, created_at
                   FROM email_audit_log
                   WHERE queue_id = ?
                   ORDER BY id DESC
                   LIMIT ?""",
                (queue_id, limit),
            ).fetchall()
        else:
            rows = conn.execute(
                """SELECT id, queue_id, action, actor, details, created_at
                   FROM email_audit_log
                   ORDER BY id DESC
                   LIMIT ?""",
                (limit,),
            ).fetchall()

        cols = ["id", "queue_id", "action", "actor", "details", "created_at"]
        return [dict(zip(cols, r)) for r in rows]
    finally:
        conn.close()
