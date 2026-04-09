"""FastAPI calendar routes for TouriBot.

Exposes Google Calendar operations as REST endpoints for the dashboard.
All endpoints gracefully return 503 when Google Calendar is not configured
(no OAuth token or missing credentials) — they never crash.

Endpoints:
  GET  /api/calendar/events?days=14       — upcoming events
  GET  /api/calendar/availability?start=...&end=...  — free/busy slots
  POST /api/calendar/events               — create event or reminder
"""
from __future__ import annotations

import logging
import os

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import Optional

logger = logging.getLogger(__name__)

router = APIRouter()


def _load_env() -> None:
    """Load .env if dotenv is available (idempotent)."""
    try:
        from pathlib import Path
        from dotenv import load_dotenv
        project_root = Path(__file__).parent.parent.parent
        load_dotenv(project_root / ".env")
    except ImportError:
        pass


def _calendar_available() -> bool:
    """Return True if Google Calendar credentials are present in the environment."""
    _load_env()
    return bool(
        os.environ.get("GOOGLE_CALENDAR_CLIENT_ID")
        and os.environ.get("GOOGLE_CALENDAR_CLIENT_SECRET")
    )


def _require_calendar():
    """Raise 503 if Google Calendar is not configured."""
    if not _calendar_available():
        raise HTTPException(
            status_code=503,
            detail=(
                "Google Calendar not configured. "
                "Set GOOGLE_CALENDAR_CLIENT_ID and GOOGLE_CALENDAR_CLIENT_SECRET in .env, "
                "then run the OAuth flow: python -c \"from tools.calendar.google_calendar import authenticate; authenticate()\""
            ),
        )


# ---------------------------------------------------------------------------
# Request models
# ---------------------------------------------------------------------------


class CreateEventRequest(BaseModel):
    title: str
    start: str                          # ISO datetime (for timed events)
    end: Optional[str] = None           # ISO datetime; omit for all-day reminders
    type: str = "event"                 # "event" | "reminder"
    description: Optional[str] = None
    attendee_email: Optional[str] = None


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.get("/events")
def get_upcoming_events(days: int = Query(14, ge=1, le=90, description="Days ahead to fetch")):
    """Return upcoming calendar events for the next N days.

    Returns 503 if Google Calendar is not configured (no OAuth token).
    """
    _require_calendar()
    _load_env()

    from tools.calendar.google_calendar import get_upcoming_events
    events = get_upcoming_events(days=days)
    return {"events": events, "count": len(events), "days": days}


@router.get("/availability")
def get_availability(
    start: str = Query(..., description="Range start (ISO 8601 datetime)"),
    end: str = Query(..., description="Range end (ISO 8601 datetime)"),
):
    """Return busy intervals in the given time range.

    Useful for checking Hermann's availability before scheduling a demo.
    Returns 503 if Google Calendar is not configured.
    """
    _require_calendar()
    _load_env()

    from tools.calendar.google_calendar import get_free_busy
    busy_slots = get_free_busy(start_iso=start, end_iso=end)
    return {
        "busy": busy_slots,
        "count": len(busy_slots),
        "range": {"start": start, "end": end},
    }


@router.post("/events")
def create_calendar_event(req: CreateEventRequest):
    """Create a calendar event or all-day reminder.

    Body:
      - type="event"    — timed event (requires start + end)
      - type="reminder" — all-day reminder (only start/date required)

    Returns 503 if Google Calendar is not configured.
    Returns 422 if required fields are missing.
    """
    _require_calendar()
    _load_env()

    from tools.calendar.google_calendar import create_event, create_reminder

    if req.type == "reminder":
        result = create_reminder(
            title=req.title,
            date_iso=req.start,
            notes=req.description,
        )
        if result is None:
            raise HTTPException(
                status_code=500,
                detail="Failed to create reminder — check server logs for details",
            )
        return {"created": True, "event": result, "type": "reminder"}

    else:
        # Timed event — end is required
        if not req.end:
            raise HTTPException(
                status_code=422,
                detail="end datetime is required for type='event'",
            )
        attendees = [req.attendee_email] if req.attendee_email else None
        result = create_event(
            title=req.title,
            start_iso=req.start,
            end_iso=req.end,
            description=req.description,
            attendees=attendees,
        )
        if result is None:
            raise HTTPException(
                status_code=500,
                detail="Failed to create event — check server logs for details",
            )
        return {"created": True, "event": result, "type": "event"}
