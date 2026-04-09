"""Read emails from Zoho Mail via IMAP.

Phase E1 — Read-only access to hermann@aitourpilot.com inbox.
Credentials come from .env only; this module never sends or modifies emails.

Required .env variables:
    ZOHO_IMAP_HOST      — imap server (default: imappro.zoho.com)
    ZOHO_IMAP_USER      — e.g. hermann@aitourpilot.com
    ZOHO_IMAP_PASSWORD  — App-specific password (NOT the account password)
"""

import email
import email.message
import email.utils
import imaplib
import logging
import os
from datetime import datetime, timedelta
from email.header import decode_header
from pathlib import Path

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def get_recent_emails(days: int = 7, folder: str = "INBOX") -> list[dict]:
    """Fetch recent emails from the configured Zoho inbox.

    Args:
        days:   Look back this many calendar days.
        folder: IMAP folder name (default "INBOX").

    Returns:
        List of dicts: {from_email, from_name, subject, body_preview,
                        date, message_id}
        On error returns a list with a single error dict.
    """
    creds = _get_credentials()
    if "error" in creds:
        return [creds]

    try:
        mail = _connect(creds)
        mail.select(folder)

        since_date = (datetime.now() - timedelta(days=days)).strftime("%d-%b-%Y")
        status, messages = mail.search(None, f"SINCE {since_date}")

        if status != "OK":
            mail.logout()
            return [{"error": "IMAP search failed"}]

        message_ids = messages[0].split()
        results = []

        # Process at most 50 most-recent messages
        for msg_id in reversed(message_ids[-50:]):
            try:
                status, msg_data = mail.fetch(msg_id, "(RFC822)")
                if status != "OK":
                    continue

                msg = email.message_from_bytes(msg_data[0][1])
                from_name, from_email_addr = email.utils.parseaddr(
                    msg.get("From", "")
                )
                results.append(
                    {
                        "from_email": from_email_addr,
                        "from_name": _decode_header_value(from_name),
                        "subject": _decode_header_value(msg.get("Subject", "")),
                        "body_preview": _get_body_preview(msg)[:500],
                        "date": msg.get("Date", ""),
                        "message_id": msg.get("Message-ID", ""),
                    }
                )
            except Exception as exc:
                logger.debug("Error parsing message %s: %s", msg_id, exc)
                continue

        mail.logout()
        return results

    except Exception as exc:
        logger.error("IMAP connection failed: %s", exc)
        return [{"error": f"IMAP connection failed: {exc}"}]


def get_email(message_id: str, folder: str = "INBOX") -> dict:
    """Fetch a single email by Message-ID with the full body.

    Args:
        message_id: The RFC 2822 Message-ID header value.
        folder:     IMAP folder to search.

    Returns:
        Email dict (same fields as get_recent_emails but with full body)
        or {"error": "..."} on failure.
    """
    creds = _get_credentials()
    if "error" in creds:
        return creds

    try:
        mail = _connect(creds)
        mail.select(folder)

        # IMAP HEADER MESSAGEID search
        status, messages = mail.search(None, f'HEADER Message-ID "{message_id}"')

        if status != "OK" or not messages[0]:
            mail.logout()
            return {"error": f"Message not found: {message_id}"}

        msg_id = messages[0].split()[0]
        status, msg_data = mail.fetch(msg_id, "(RFC822)")
        mail.logout()

        if status != "OK":
            return {"error": "Failed to fetch message body"}

        msg = email.message_from_bytes(msg_data[0][1])
        from_name, from_email_addr = email.utils.parseaddr(msg.get("From", ""))
        body = _get_body_text(msg)

        return {
            "from_email": from_email_addr,
            "from_name": _decode_header_value(from_name),
            "subject": _decode_header_value(msg.get("Subject", "")),
            "body": body,
            "date": msg.get("Date", ""),
            "message_id": msg.get("Message-ID", ""),
        }

    except Exception as exc:
        logger.error("get_email failed: %s", exc)
        return {"error": f"IMAP error: {exc}"}


def search_emails(
    query: str, days: int = 30, folder: str = "INBOX"
) -> list[dict]:
    """Search emails by subject or from text within the last N days.

    Args:
        query:  Search string — checked against Subject header.
        days:   Look back this many days.
        folder: IMAP folder.

    Returns:
        List of matching email dicts.
    """
    creds = _get_credentials()
    if "error" in creds:
        return [creds]

    try:
        mail = _connect(creds)
        mail.select(folder)

        since_date = (datetime.now() - timedelta(days=days)).strftime("%d-%b-%Y")

        # IMAP SEARCH supports SUBJECT and FROM criteria
        status, messages = mail.search(
            None,
            f'SINCE {since_date} SUBJECT "{query}"',
        )

        results = []
        if status == "OK" and messages[0]:
            for msg_id in reversed(messages[0].split()[-20:]):  # latest 20
                try:
                    status, msg_data = mail.fetch(msg_id, "(RFC822)")
                    if status != "OK":
                        continue
                    msg = email.message_from_bytes(msg_data[0][1])
                    from_name, from_email_addr = email.utils.parseaddr(
                        msg.get("From", "")
                    )
                    results.append(
                        {
                            "from_email": from_email_addr,
                            "from_name": _decode_header_value(from_name),
                            "subject": _decode_header_value(msg.get("Subject", "")),
                            "body_preview": _get_body_preview(msg)[:500],
                            "date": msg.get("Date", ""),
                            "message_id": msg.get("Message-ID", ""),
                        }
                    )
                except Exception as exc:
                    logger.debug("Error parsing search result: %s", exc)

        mail.logout()
        return results

    except Exception as exc:
        logger.error("search_emails failed: %s", exc)
        return [{"error": f"IMAP search error: {exc}"}]


def check_inbox(days_back: int = 7, from_contacts_only: bool = True) -> dict:
    """High-level inbox check — convenience wrapper used by the email chat tool.

    Args:
        days_back:          Days to look back.
        from_contacts_only: If True, filter results to known leads.db contacts.

    Returns:
        {"emails": [...], "total": N}  or  {"error": "..."}
    """
    emails = get_recent_emails(days=days_back)

    # Propagate errors
    if emails and "error" in emails[0]:
        return emails[0]

    if from_contacts_only:
        emails = _filter_to_contacts(emails)

    return {"emails": emails, "total": len(emails)}


# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------


def _get_credentials() -> dict:
    """Read IMAP credentials from environment. Returns error dict if missing."""
    # Load .env if not already loaded
    try:
        from dotenv import load_dotenv

        load_dotenv(Path(__file__).parent.parent.parent / ".env")
    except ImportError:
        pass

    host = os.environ.get("ZOHO_IMAP_HOST", "imappro.zoho.com")
    user = os.environ.get("ZOHO_IMAP_USER", "")
    password = os.environ.get("ZOHO_IMAP_PASSWORD", "")

    if not user or not password:
        return {
            "error": (
                "Zoho IMAP credentials not configured. "
                "Set ZOHO_IMAP_USER and ZOHO_IMAP_PASSWORD in .env"
            )
        }

    return {"host": host, "user": user, "password": password}


def _connect(creds: dict) -> imaplib.IMAP4_SSL:
    """Open an authenticated IMAP4_SSL connection."""
    mail = imaplib.IMAP4_SSL(creds["host"], 993)
    mail.login(creds["user"], creds["password"])
    return mail


def _decode_header_value(value: str) -> str:
    """Decode a (possibly encoded) email header value to a plain string."""
    if not value:
        return ""
    try:
        decoded = decode_header(value)
        parts = []
        for text, charset in decoded:
            if isinstance(text, bytes):
                parts.append(text.decode(charset or "utf-8", errors="replace"))
            else:
                parts.append(text)
        return " ".join(parts)
    except Exception:
        return value


def _get_body_preview(msg: email.message.Message) -> str:
    """Extract first 500 chars of plain-text body (non-destructive)."""
    return _get_body_text(msg)[:500]


def _get_body_text(msg: email.message.Message) -> str:
    """Extract full plain-text body from a MIME message.

    Prefers text/plain; falls back to converting text/html via html2text.
    """
    plain_parts = []
    html_parts = []

    if msg.is_multipart():
        for part in msg.walk():
            ctype = part.get_content_type()
            if ctype == "text/plain":
                payload = part.get_payload(decode=True)
                if payload:
                    charset = part.get_content_charset() or "utf-8"
                    plain_parts.append(payload.decode(charset, errors="replace"))
            elif ctype == "text/html":
                payload = part.get_payload(decode=True)
                if payload:
                    charset = part.get_content_charset() or "utf-8"
                    html_parts.append(payload.decode(charset, errors="replace"))
    else:
        payload = msg.get_payload(decode=True)
        if payload:
            charset = msg.get_content_charset() or "utf-8"
            text = payload.decode(charset, errors="replace")
            if msg.get_content_type() == "text/plain":
                plain_parts.append(text)
            else:
                html_parts.append(text)

    if plain_parts:
        return "\n".join(plain_parts)

    if html_parts:
        try:
            import html2text

            h = html2text.HTML2Text()
            h.ignore_links = False
            return h.handle("\n".join(html_parts))
        except ImportError:
            # html2text not installed — strip tags crudely
            import re

            return re.sub(r"<[^>]+>", " ", "\n".join(html_parts))

    return ""


def _filter_to_contacts(emails: list[dict]) -> list[dict]:
    """Filter to emails whose sender is a known contact in leads.db."""
    try:
        from tools.leads.lead_db import DB_PATH

        import sqlite3

        conn = sqlite3.connect(str(DB_PATH))
        rows = conn.execute(
            "SELECT email FROM contacts WHERE email IS NOT NULL"
        ).fetchall()
        conn.close()

        known_emails = {r[0].lower() for r in rows if r[0]}
        return [e for e in emails if e.get("from_email", "").lower() in known_emails]
    except Exception as exc:
        logger.debug("Contact filter failed (returning all): %s", exc)
        return emails
