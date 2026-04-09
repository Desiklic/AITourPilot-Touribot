"""Calendar tool definitions and handlers for TouriBot chat integration.

This module defines CALENDAR_TOOLS (Anthropic tool-use specs) and the
dispatch function handle_calendar_tool_call() that executes them.

These are NOT yet wired into chat_handler.py — that happens in T2 (Browser Access)
when the full tool-use streaming pattern is implemented. This file just makes
the tool specs and handlers ready for that wiring.

Usage (once T2 tool-use pattern is in place):
    from tools.api.calendar_tools import CALENDAR_TOOLS, handle_calendar_tool_call
    # Pass CALENDAR_TOOLS to client.messages.create(tools=...)
    # Call handle_calendar_tool_call(tool_name, tool_input) when a tool_use block arrives
"""
from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Tool specifications (Anthropic tool-use format)
# ---------------------------------------------------------------------------

CALENDAR_TOOLS: list[dict[str, Any]] = [
    {
        "name": "check_calendar",
        "description": (
            "Check Hermann's Google Calendar for upcoming events or availability. "
            "Use 'upcoming' to list events in the next N days. "
            "Use 'availability' to find free/busy slots in a specific time range."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "enum": ["upcoming", "availability"],
                    "description": (
                        "'upcoming' — list events in the next N days. "
                        "'availability' — check free/busy for a specific range."
                    ),
                },
                "days": {
                    "type": "integer",
                    "description": "Days ahead to check for 'upcoming' action (default 14).",
                },
                "start": {
                    "type": "string",
                    "description": (
                        "ISO 8601 datetime string for availability check range start. "
                        "Required when action='availability'."
                    ),
                },
                "end": {
                    "type": "string",
                    "description": (
                        "ISO 8601 datetime string for availability check range end. "
                        "Required when action='availability'."
                    ),
                },
            },
            "required": ["action"],
        },
    },
    {
        "name": "schedule_event",
        "description": (
            "Create a calendar event on Hermann's Google Calendar. "
            "Use type='demo' for a timed meeting with a museum contact (requires start and end). "
            "Use type='reminder' for an all-day follow-up reminder (only start date required)."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "title": {
                    "type": "string",
                    "description": "Event title (e.g. 'Demo call — SS Great Britain' or 'Follow up with Joanneum').",
                },
                "start": {
                    "type": "string",
                    "description": (
                        "ISO 8601 datetime for the event start (e.g. '2026-04-15T14:00:00'). "
                        "For reminders, a date string (YYYY-MM-DD) is sufficient."
                    ),
                },
                "end": {
                    "type": "string",
                    "description": (
                        "ISO 8601 datetime for the event end. "
                        "Required for type='demo', omit for type='reminder'."
                    ),
                },
                "type": {
                    "type": "string",
                    "enum": ["demo", "reminder"],
                    "description": "'demo' creates a timed event; 'reminder' creates an all-day event.",
                },
                "description": {
                    "type": "string",
                    "description": "Optional event notes or agenda.",
                },
                "attendee_email": {
                    "type": "string",
                    "description": "Optional email address of the museum contact to invite.",
                },
            },
            "required": ["title", "start", "type"],
        },
    },
]


# ---------------------------------------------------------------------------
# Tool handler dispatch
# ---------------------------------------------------------------------------


def handle_calendar_tool_call(tool_name: str, tool_input: dict[str, Any]) -> str:
    """Execute a calendar tool call and return a plain-text result string.

    Called by the chat handler when Claude emits a tool_use block with a
    calendar tool name. Returns a human-readable string that becomes the
    tool_result content passed back to Claude.

    Handles the 'not configured' case gracefully — returns an informative
    message rather than raising.

    Args:
        tool_name:  One of the tool names defined in CALENDAR_TOOLS.
        tool_input: The input dict from the tool_use block.

    Returns:
        Plain-text string summarising the result (for Claude to synthesise).
    """
    try:
        if tool_name == "check_calendar":
            return _handle_check_calendar(tool_input)
        elif tool_name == "schedule_event":
            return _handle_schedule_event(tool_input)
        else:
            return f"Unknown calendar tool: {tool_name}"
    except Exception as exc:
        logger.error("calendar tool '%s' raised: %s", tool_name, exc)
        return f"Calendar tool error ({tool_name}): {exc}"


def _handle_check_calendar(tool_input: dict[str, Any]) -> str:
    """Handler for the check_calendar tool."""
    from tools.calendar.google_calendar import get_upcoming_events, get_free_busy

    action = tool_input.get("action", "upcoming")

    if action == "upcoming":
        days = int(tool_input.get("days", 14))
        events = get_upcoming_events(days=days)
        if not events:
            return f"No events found in the next {days} days (or Google Calendar is not configured)."
        lines = [f"Upcoming events (next {days} days):"]
        for ev in events:
            lines.append(
                f"  - {ev['title']} | {ev['start']} — {ev['end']}"
                + (f" | {ev['location']}" if ev.get("location") else "")
            )
        return "\n".join(lines)

    elif action == "availability":
        start = tool_input.get("start", "")
        end = tool_input.get("end", "")
        if not start or not end:
            return "Error: 'start' and 'end' are required for availability check."
        busy_slots = get_free_busy(start_iso=start, end_iso=end)
        if not busy_slots:
            return f"No busy slots found between {start} and {end} — Hermann appears free during this range (or Google Calendar is not configured)."
        lines = [f"Busy slots between {start} and {end}:"]
        for slot in busy_slots:
            lines.append(f"  - {slot['start']} — {slot['end']}")
        return "\n".join(lines)

    else:
        return f"Unknown action '{action}'. Use 'upcoming' or 'availability'."


def _handle_schedule_event(tool_input: dict[str, Any]) -> str:
    """Handler for the schedule_event tool."""
    from tools.calendar.google_calendar import create_event, create_reminder

    title = tool_input.get("title", "")
    start = tool_input.get("start", "")
    end = tool_input.get("end")
    event_type = tool_input.get("type", "demo")
    description = tool_input.get("description")
    attendee_email = tool_input.get("attendee_email")

    if not title or not start:
        return "Error: 'title' and 'start' are required to schedule an event."

    if event_type == "reminder":
        result = create_reminder(title=title, date_iso=start, notes=description)
        if result is None:
            return "Failed to create reminder — Google Calendar may not be configured."
        return (
            f"Reminder created: '{result['title']}' on {result['start']} "
            f"(Google Calendar event ID: {result['id']})"
        )

    else:  # demo (timed event)
        if not end:
            return "Error: 'end' datetime is required for a demo event."
        attendees = [attendee_email] if attendee_email else None
        result = create_event(
            title=title,
            start_iso=start,
            end_iso=end,
            description=description,
            attendees=attendees,
        )
        if result is None:
            return "Failed to create event — Google Calendar may not be configured."
        attendee_note = f" | Invited: {attendee_email}" if attendee_email else ""
        return (
            f"Event created: '{result['title']}' from {result['start']} to {result['end']}"
            f"{attendee_note} (Google Calendar event ID: {result['id']})"
        )
