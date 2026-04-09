"""Email tool definitions and handlers for TouriBot chat (Phase E3).

Defines the Anthropic tool-use spec for the `check_email` tool, plus the
handler that executes it.  Wired into tool_registry.py so the chat handler
can dispatch to it via the agentic tool-use loop.

Only read operations are exposed.  No send or draft capability is wired here.
"""

from __future__ import annotations

import json
import logging

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Tool definitions (Anthropic tool-use schema)
# ---------------------------------------------------------------------------

EMAIL_TOOLS: list[dict] = [
    {
        "name": "check_email",
        "description": (
            "Check Hermann's Zoho inbox (hermann@aitourpilot.com) for recent "
            "emails from museum contacts. Returns a list of emails from the last "
            "N days, including sender, subject, date, and a short body preview. "
            "By default only shows emails from known leads. Use this when Hermann "
            "asks 'any new emails?', 'did anyone reply?', or wants to know what's "
            "in his inbox."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "days_back": {
                    "type": "integer",
                    "description": "How many days back to look (default 7, max 30).",
                    "default": 7,
                },
                "contacts_only": {
                    "type": "boolean",
                    "description": (
                        "Only show emails from known museum contacts in the CRM. "
                        "Set to false to see all inbox emails (default true)."
                    ),
                    "default": True,
                },
            },
            "required": [],
        },
    },
]

_EMAIL_TOOL_NAMES = {"check_email"}


# ---------------------------------------------------------------------------
# Handler
# ---------------------------------------------------------------------------


def handle_email_tool_call(tool_name: str, tool_input: dict) -> str:
    """Execute an email tool call and return a plain-text result string.

    Args:
        tool_name:  Name of the email tool.
        tool_input: Input dict from the Anthropic tool_use content block.

    Returns:
        Plain-text result string suitable for passing back as tool_result content.
    """
    if tool_name == "check_email":
        return _handle_check_email(tool_input)
    return f"Unknown email tool: {tool_name}"


def _handle_check_email(tool_input: dict) -> str:
    """Fetch recent inbox emails and format as plain text."""
    days_back = int(tool_input.get("days_back", 7))
    days_back = min(days_back, 30)  # cap at 30 days
    contacts_only = bool(tool_input.get("contacts_only", True))

    try:
        from tools.email.zoho_reader import check_inbox

        result = check_inbox(days_back=days_back, from_contacts_only=contacts_only)
    except Exception as exc:
        logger.error("check_email tool failed: %s", exc)
        return f"Email check failed: {exc}"

    if "error" in result:
        return f"Could not access inbox: {result['error']}"

    emails = result.get("emails", [])
    total = result.get("total", len(emails))

    if not emails:
        scope = "from known contacts " if contacts_only else ""
        return (
            f"No emails {scope}found in the last {days_back} day(s)."
        )

    lines = [
        f"Found {total} email(s) in the last {days_back} day(s)"
        + (" from known contacts" if contacts_only else "")
        + ":\n"
    ]

    for i, e in enumerate(emails, 1):
        from_part = e.get("from_name") or e.get("from_email", "Unknown")
        if e.get("from_name") and e.get("from_email"):
            from_part = f"{e['from_name']} <{e['from_email']}>"
        lines.append(
            f"{i}. From: {from_part}\n"
            f"   Subject: {e.get('subject', '(no subject)')}\n"
            f"   Date: {e.get('date', 'unknown')}\n"
            f"   Preview: {e.get('body_preview', '')[:200]}\n"
        )

    return "\n".join(lines)
