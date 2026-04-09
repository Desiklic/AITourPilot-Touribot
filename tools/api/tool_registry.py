"""Unified tool registry for TouriBot chat.

Aggregates all Anthropic tool-use specs and provides a single dispatch
function for the chat handler's tool-use agentic loop.

Tools available:
  - browse_url      — fetch any web page via Jina Reader
  - web_search      — search the web via Tavily/Serper
  - check_calendar  — read Hermann's Google Calendar
  - schedule_event  — create demo events / follow-up reminders
  - check_email     — read Zoho inbox for museum contact replies (read-only)
"""
from __future__ import annotations

from tools.api.browse_tools import BROWSE_TOOLS, handle_browse_tool_call
from tools.api.calendar_tools import CALENDAR_TOOLS, handle_calendar_tool_call
from tools.api.email_tools import EMAIL_TOOLS, handle_email_tool_call

# Combined list passed to client.messages.stream(tools=ALL_TOOLS)
ALL_TOOLS: list[dict] = BROWSE_TOOLS + CALENDAR_TOOLS + EMAIL_TOOLS

_BROWSE_TOOL_NAMES = {"browse_url", "web_search"}
_CALENDAR_TOOL_NAMES = {"check_calendar", "schedule_event"}
_EMAIL_TOOL_NAMES = {"check_email"}


def handle_tool_call(tool_name: str, tool_input: dict) -> str:
    """Route a tool call to the appropriate handler.

    Args:
        tool_name:  Name of the tool (from the tool_use content block).
        tool_input: Input dict from the tool_use content block.

    Returns:
        Plain-text string result to pass back as tool_result content.
    """
    if tool_name in _BROWSE_TOOL_NAMES:
        return handle_browse_tool_call(tool_name, tool_input)
    elif tool_name in _CALENDAR_TOOL_NAMES:
        return handle_calendar_tool_call(tool_name, tool_input)
    elif tool_name in _EMAIL_TOOL_NAMES:
        return handle_email_tool_call(tool_name, tool_input)
    else:
        return f"Unknown tool: {tool_name}"
