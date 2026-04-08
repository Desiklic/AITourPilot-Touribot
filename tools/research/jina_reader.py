"""Jina Reader API client — fetch clean markdown from any URL.

Free tier: 20 RPM. Paid: higher limits. Optional API key for higher rate limits.
Endpoint: https://r.jina.ai/{url}
"""
import logging
import os
import time
import urllib.request
import urllib.error
from typing import Optional

logger = logging.getLogger(__name__)

JINA_BASE = "https://r.jina.ai/"
_DEFAULT_TIMEOUT = 30
_DEFAULT_MAX_CHARS = 40000  # trim fetched markdown to avoid blowing token budgets


def fetch_page(url: str, timeout: int = _DEFAULT_TIMEOUT,
               max_chars: int = _DEFAULT_MAX_CHARS) -> Optional[str]:
    """Fetch URL via Jina Reader. Returns markdown text or None on failure."""
    jina_url = JINA_BASE + url
    headers = {
        "Accept": "text/plain",
        "User-Agent": "TouriBot/1.0",
    }
    api_key = os.getenv("JINA_API_KEY", "")
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"

    try:
        req = urllib.request.Request(jina_url, headers=headers)
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            text = resp.read().decode("utf-8", errors="replace")
            if max_chars and len(text) > max_chars:
                text = text[:max_chars] + "\n\n[truncated]"
            logger.debug("Jina: fetched %s → %d chars", url, len(text))
            return text
    except urllib.error.HTTPError as e:
        logger.warning("Jina HTTP %s for %s", e.code, url)
        return None
    except Exception as e:
        logger.warning("Jina fetch failed for %s: %s", url, e)
        return None


def fetch_pages_with_ratelimit(urls: list[str], rpm: int = 18) -> dict[str, Optional[str]]:
    """Fetch multiple URLs sequentially, respecting Jina free-tier RPM limit."""
    results: dict[str, Optional[str]] = {}
    delay = 60.0 / rpm
    for i, url in enumerate(urls):
        if i > 0:
            time.sleep(delay)
        results[url] = fetch_page(url)
    return results
