"""Unified tool registry for TouriBot chat.

Aggregates all Anthropic tool-use specs and provides a single dispatch
function for the chat handler's tool-use agentic loop.

Tools available:
  - browse_url       — fetch any web page via Jina Reader
  - web_search       — search the web via Tavily/Serper
  - check_calendar   — read Hermann's Google Calendar
  - schedule_event   — create demo events / follow-up reminders
  - check_email      — read Zoho inbox for museum contact replies (read-only)
  - list_files       — list files in project folders
  - read_file        — read file content (txt, csv, xlsx, pdf, docx, etc.)
  - query_contacts   — search/list CRM contacts with museum + interaction data
  - query_museum     — get full detail on a specific museum
  - query_pipeline   — get pipeline overview stats
"""
from __future__ import annotations

from tools.api.browse_tools import BROWSE_TOOLS, handle_browse_tool_call
from tools.api.calendar_tools import CALENDAR_TOOLS, handle_calendar_tool_call
from tools.api.email_tools import EMAIL_TOOLS, handle_email_tool_call
from tools.api.file_tools import FILE_TOOLS, handle_file_tool_call
from tools.api.crm_tools import CRM_TOOLS, handle_crm_tool_call

# Combined list passed to client.messages.stream(tools=ALL_TOOLS)
ALL_TOOLS: list[dict] = BROWSE_TOOLS + CALENDAR_TOOLS + EMAIL_TOOLS + FILE_TOOLS + CRM_TOOLS

_BROWSE_TOOL_NAMES = {"browse_url", "web_search"}
_CALENDAR_TOOL_NAMES = {"check_calendar", "schedule_event"}
_EMAIL_TOOL_NAMES = {"check_email"}
_FILE_TOOL_NAMES = {"list_files", "read_file"}
_CRM_TOOL_NAMES = {"query_contacts", "query_museum", "query_pipeline"}


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
    elif tool_name in _FILE_TOOL_NAMES:
        return handle_file_tool_call(tool_name, tool_input)
    elif tool_name in _CRM_TOOL_NAMES:
        return handle_crm_tool_call(tool_name, tool_input)
    else:
        return f"Unknown tool: {tool_name}"
