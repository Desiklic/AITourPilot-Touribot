"""Google Calendar provider for TouriBot — adapted from HenryBot's google_provider.py.

Provides simple functions for reading upcoming events, checking free/busy, and
creating events/reminders. All functions handle the "not configured" case
gracefully — they return empty results rather than crashing.

Authentication uses OAuth2 with a local token cache. On first use, a
browser-based consent flow runs automatically.

Required environment variables (set in .env — never in settings.yaml or code):
  GOOGLE_CALENDAR_CLIENT_ID      — OAuth client ID from Google Cloud Console
  GOOGLE_CALENDAR_CLIENT_SECRET  — OAuth client secret

Optional:
  GOOGLE_CALENDAR_TOKEN_FILE     — Token cache path (default: ~/.touribot/google_token.json)

Install dependencies (one-time):
  pip install google-api-python-client google-auth-oauthlib google-auth-httplib2
"""
from __future__ import annotations

import logging
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Optional

logger = logging.getLogger(__name__)

_SCOPES = ["https://www.googleapis.com/auth/calendar"]
_DEFAULT_TOKEN = Path.home() / ".touribot" / "google_token.json"


def _get_credentials_config() -> tuple[str, str, Path]:
    """Read credentials from environment. Returns (client_id, client_secret, token_file)."""
    client_id = os.environ.get("GOOGLE_CALENDAR_CLIENT_ID", "")
    client_secret = os.environ.get("GOOGLE_CALENDAR_CLIENT_SECRET", "")
    token_file = Path(
        os.environ.get("GOOGLE_CALENDAR_TOKEN_FILE", str(_DEFAULT_TOKEN))
    )
    return client_id, client_secret, token_file


def _is_configured() -> bool:
    """Return True if credentials are set in the environment."""
    client_id, client_secret, _ = _get_credentials_config()
    return bool(client_id and client_secret)


# Module-level cached service to avoid re-authenticating on every call.
_service = None


def _get_service():
    """Return authenticated Google Calendar API service, or None if not configured."""
    global _service
    if _service is not None:
        return _service

    client_id, client_secret, token_file = _get_credentials_config()

    if not client_id or not client_secret:
        logger.warning(
            "Google Calendar not configured — set GOOGLE_CALENDAR_CLIENT_ID "
            "and GOOGLE_CALENDAR_CLIENT_SECRET in .env"
        )
        return None

    try:
        from google.oauth2.credentials import Credentials
        from google_auth_oauthlib.flow import InstalledAppFlow
        from google.auth.transport.requests import Request
        from googleapiclient.discovery import build
    except ImportError:
        logger.error(
            "Google Calendar dependencies not installed. "
            "Run: pip install google-api-python-client google-auth-oauthlib google-auth-httplib2"
        )
        return None

    try:
        creds = None
        if token_file.exists():
            creds = Credentials.from_authorized_user_file(str(token_file), _SCOPES)

        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                client_config = {
                    "installed": {
                        "client_id":     client_id,
                        "client_secret": client_secret,
                        "redirect_uris": ["urn:ietf:wg:oauth:2.0:oob", "http://localhost"],
                        "auth_uri":      "https://accounts.google.com/o/oauth2/auth",
                        "token_uri":     "https://oauth2.googleapis.com/token",
                    }
                }
                flow = InstalledAppFlow.from_client_config(client_config, _SCOPES)
                creds = flow.run_local_server(port=0)

            # Persist token for future runs
            token_file.parent.mkdir(parents=True, exist_ok=True)
            token_file.write_text(creds.to_json())

        _service = build("calendar", "v3", credentials=creds, cache_discovery=False)
        return _service

    except Exception as exc:
        logger.error("Failed to authenticate with Google Calendar: %s", exc)
        return None


def _rfc3339(iso_str: str) -> str:
    """Ensure an ISO datetime string ends with Z (RFC 3339 — required by Google API)."""
    s = iso_str.strip()
    if s.endswith("Z") or "+" in s[-6:]:
        return s
    return s + "Z"


def _event_to_dict(item: dict) -> dict:
    """Convert a raw Google Calendar API event dict to a simplified TouriBot dict."""
    start_raw = item.get("start", {})
    end_raw = item.get("end", {})
    is_all_day = "date" in start_raw and "dateTime" not in start_raw
    return {
        "id":          item.get("id", ""),
        "title":       item.get("summary", "(no title)"),
        "start":       start_raw.get("dateTime") or start_raw.get("date", ""),
        "end":         end_raw.get("dateTime")   or end_raw.get("date", ""),
        "location":    item.get("location", ""),
        "description": item.get("description", ""),
        "attendees":   [a.get("email", "") for a in item.get("attendees", []) if a.get("email")],
        "is_all_day":  is_all_day,
        "status":      item.get("status", "confirmed"),
    }


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def authenticate() -> bool:
    """Run OAuth2 consent flow if no valid token exists.

    Returns True if authentication succeeds (or is already valid).
    Opens a browser window on first run to complete Google's consent flow.
    """
    svc = _get_service()
    return svc is not None


def get_upcoming_events(days: int = 14) -> list[dict]:
    """Return events in the next N days from the primary calendar.

    Returns an empty list if Google Calendar is not configured or
    authentication fails — never raises.

    Args:
        days: Number of days ahead to fetch (default 14).

    Returns:
        List of event dicts: {id, title, start, end, location, description,
        attendees, is_all_day, status}
    """
    svc = _get_service()
    if svc is None:
        return []

    try:
        now = datetime.now(timezone.utc)
        time_min = now.isoformat()
        time_max = (now + timedelta(days=days)).isoformat()

        result = svc.events().list(
            calendarId="primary",
            timeMin=_rfc3339(time_min),
            timeMax=_rfc3339(time_max),
            singleEvents=True,
            orderBy="startTime",
            maxResults=100,
        ).execute()

        return [_event_to_dict(item) for item in result.get("items", [])]

    except Exception as exc:
        logger.error("get_upcoming_events failed: %s", exc)
        return []


def get_free_busy(start_iso: str, end_iso: str) -> list[dict]:
    """Return busy intervals in the given time range across all calendars.

    Returns an empty list if not configured or on error.

    Args:
        start_iso: Range start (ISO 8601 datetime string).
        end_iso:   Range end (ISO 8601 datetime string).

    Returns:
        List of busy-interval dicts: {start, end}
    """
    svc = _get_service()
    if svc is None:
        return []

    try:
        # Query across all calendars (up to 10)
        cal_result = svc.calendarList().list().execute()
        cal_ids = [c["id"] for c in cal_result.get("items", [])[:10]]
        if not cal_ids:
            cal_ids = ["primary"]

        body = {
            "timeMin": _rfc3339(start_iso),
            "timeMax": _rfc3339(end_iso),
            "items":   [{"id": cid} for cid in cal_ids],
        }
        result = svc.freebusy().query(body=body).execute()

        blocks: list[dict] = []
        for cal_busy in result.get("calendars", {}).values():
            for blk in cal_busy.get("busy", []):
                blocks.append({"start": blk["start"], "end": blk["end"]})

        # Sort by start time for convenience
        blocks.sort(key=lambda b: b["start"])
        return blocks

    except Exception as exc:
        logger.error("get_free_busy failed: %s", exc)
        return []


def create_event(
    title: str,
    start_iso: str,
    end_iso: str,
    description: Optional[str] = None,
    attendees: Optional[list[str]] = None,
) -> Optional[dict]:
    """Create a calendar event on the primary calendar.

    Returns the created event dict on success, or None if not configured / failed.

    Args:
        title:       Event title/summary.
        start_iso:   Start datetime (ISO 8601).
        end_iso:     End datetime (ISO 8601).
        description: Optional event description / notes.
        attendees:   Optional list of attendee email addresses.

    Returns:
        Created event dict: {id, title, start, end, ...} or None on failure.
    """
    svc = _get_service()
    if svc is None:
        logger.warning("create_event: Google Calendar not configured")
        return None

    try:
        body: dict[str, Any] = {
            "summary": title,
            "start":   {"dateTime": _rfc3339(start_iso), "timeZone": "UTC"},
            "end":     {"dateTime": _rfc3339(end_iso),   "timeZone": "UTC"},
        }
        if description:
            body["description"] = description
        if attendees:
            body["attendees"] = [{"email": email} for email in attendees]

        created = svc.events().insert(calendarId="primary", body=body).execute()
        logger.info("Created calendar event: %s (id=%s)", title, created.get("id"))
        return _event_to_dict(created)

    except Exception as exc:
        logger.error("create_event failed: %s", exc)
        return None


def create_reminder(
    title: str,
    date_iso: str,
    notes: Optional[str] = None,
) -> Optional[dict]:
    """Create an all-day reminder event on the primary calendar.

    Useful for follow-up reminders (e.g. "Follow up with Joanneum").
    All-day events only require a date (YYYY-MM-DD), not a full datetime.

    Returns the created event dict on success, or None if not configured / failed.

    Args:
        title:    Event title (e.g. "Follow up with Joanneum Museum").
        date_iso: Date for the reminder (ISO date: YYYY-MM-DD or full datetime).
        notes:    Optional notes / description.

    Returns:
        Created event dict or None on failure.
    """
    svc = _get_service()
    if svc is None:
        logger.warning("create_reminder: Google Calendar not configured")
        return None

    try:
        # Normalise: extract date portion if a full datetime string was passed
        date_str = date_iso.strip()
        if "T" in date_str:
            date_str = date_str.split("T")[0]
        if date_str.endswith("Z"):
            date_str = date_str[:-1]

        body: dict[str, Any] = {
            "summary": title,
            "start":   {"date": date_str},
            "end":     {"date": date_str},
        }
        if notes:
            body["description"] = notes

        created = svc.events().insert(calendarId="primary", body=body).execute()
        logger.info("Created reminder: %s on %s (id=%s)", title, date_str, created.get("id"))
        return _event_to_dict(created)

    except Exception as exc:
        logger.error("create_reminder failed: %s", exc)
        return None


def delete_event(event_id: str) -> bool:
    """Delete a calendar event by its Google Calendar event ID.

    Returns True on success, False if not configured or if deletion fails.

    Args:
        event_id: Google Calendar event ID (from the 'id' field of an event dict).

    Returns:
        True on success, False on failure.
    """
    svc = _get_service()
    if svc is None:
        logger.warning("delete_event: Google Calendar not configured")
        return False

    try:
        svc.events().delete(calendarId="primary", eventId=event_id).execute()
        logger.info("Deleted calendar event: %s", event_id)
        return True
    except Exception as exc:
        logger.warning("delete_event failed for %s: %s", event_id, exc)
        return False
