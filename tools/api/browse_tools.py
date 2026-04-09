"""Browse and search tools for TouriBot chat.

Defines BROWSE_TOOLS (Anthropic tool-use specs) and handle_browse_tool_call()
for dispatching tool calls to the Jina Reader and Tavily/Serper search clients.
"""
from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Tool specifications (Anthropic tool-use format)
# ---------------------------------------------------------------------------

BROWSE_TOOLS: list[dict[str, Any]] = [
    {
        "name": "browse_url",
        "description": (
            "Fetch and read the content of a website URL. Returns the page content as clean text. "
            "Use for museum websites, competitor sites, aitourpilot.com, or any URL the user mentions."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "url": {
                    "type": "string",
                    "description": "The full URL to fetch (must start with http:// or https://)",
                }
            },
            "required": ["url"],
        },
    },
    {
        "name": "web_search",
        "description": (
            "Search the web for current information. Use when the user asks about something that "
            "needs up-to-date information, or when researching a museum, competitor, or market trend."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "The search query",
                }
            },
            "required": ["query"],
        },
    },
]


# ---------------------------------------------------------------------------
# Tool handler dispatch
# ---------------------------------------------------------------------------


def handle_browse_tool_call(tool_name: str, tool_input: dict[str, Any]) -> str:
    """Execute a browse/search tool and return the result as a plain-text string.

    Returns a string in all cases — never raises. Errors are returned as
    descriptive strings so Claude can incorporate them into its response.

    Args:
        tool_name:  "browse_url" or "web_search"
        tool_input: The input dict from the tool_use block.

    Returns:
        Plain-text string with the tool result (for Claude to synthesise).
    """
    if tool_name == "browse_url":
        return _handle_browse_url(tool_input)
    elif tool_name == "web_search":
        return _handle_web_search(tool_input)
    else:
        return f"Unknown browse tool: {tool_name}"


def _handle_browse_url(tool_input: dict[str, Any]) -> str:
    """Fetch a URL via Jina Reader and return clean text content."""
    url = tool_input.get("url", "")
    if not url:
        return "Error: URL is required."
    if not url.startswith(("http://", "https://")):
        return "Error: URL must start with http:// or https://"

    try:
        from tools.research.jina_reader import fetch_page
        content = fetch_page(url, max_chars=15000)
        if not content or len(content) < 50:
            return (
                f"Could not fetch meaningful content from {url}. "
                "The page may be empty, blocked, or require authentication."
            )
        # Jina already truncates, but apply our own cap for safety
        if len(content) > 15000:
            content = content[:15000] + "\n\n[... content truncated at 15,000 characters ...]"
        logger.info("browse_url: fetched %s (%d chars)", url, len(content))
        return content
    except Exception as exc:
        logger.warning("browse_url failed for %s: %s", url, exc)
        return f"Error fetching {url}: {exc}"


def _handle_web_search(tool_input: dict[str, Any]) -> str:
    """Run a web search via Tavily/Serper and return formatted results."""
    query = tool_input.get("query", "").strip()
    if not query:
        return "Error: search query is empty."

    try:
        from tools.research.search_client import search
        results, _cost = search(query, max_results=5)
        if not results:
            # search_client returns [] when API key is missing or on error
            import os
            if not os.getenv("TAVILY_API_KEY") and not os.getenv("SERPER_API_KEY"):
                return (
                    "Web search is not configured — neither TAVILY_API_KEY nor SERPER_API_KEY "
                    "is set in the environment. Please add one to .env to enable web search."
                )
            return f"No search results found for: {query}"

        formatted: list[str] = []
        for r in results:
            title = r.title or "Untitled"
            url = r.url or ""
            snippet = r.snippet or ""
            formatted.append(f"**{title}**\n{url}\n{snippet}")

        logger.info("web_search: %d results for %r", len(results), query)
        return "\n\n---\n\n".join(formatted)
    except Exception as exc:
        logger.warning("web_search failed for %r: %s", query, exc)
        return f"Search error: {exc}"
