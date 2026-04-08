"""Web search client — URL discovery for deep research.

Supports Tavily ($0.005/query basic, $0.01/query advanced) and Serper ($0.001/query).
Provider: configured via settings.yaml deep_research.search_provider or SEARCH_PROVIDER env.
"""
import json
import logging
import os
import urllib.request
import urllib.error
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).parent.parent.parent

# Flat cost per search query (basic tier)
_TAVILY_COST_PER_QUERY = 0.005
_SERPER_COST_PER_QUERY = 0.001


def _load_provider_config() -> dict:
    """Load provider config from settings.yaml deep_research section."""
    try:
        import yaml
        path = PROJECT_ROOT / "args" / "settings.yaml"
        cfg = yaml.safe_load(path.read_text()) or {}
        return cfg.get("deep_research", {})
    except Exception:
        return {}


class SearchResult:
    __slots__ = ("url", "title", "snippet", "score")

    def __init__(self, url: str, title: str, snippet: str, score: float = 0.0):
        self.url = url
        self.title = title
        self.snippet = snippet
        self.score = score


def search(query: str, max_results: int = 10,
           provider: Optional[str] = None) -> tuple[list[SearchResult], float]:
    """Search and return (results, cost_usd). Returns ([], 0.0) on error (non-fatal)."""
    cfg = _load_provider_config()
    provider = provider or os.getenv("SEARCH_PROVIDER") or cfg.get("search_provider", "tavily")

    if provider == "tavily":
        return _tavily_search(query, max_results, cfg)
    elif provider == "serper":
        return _serper_search(query, max_results, cfg)
    else:
        logger.warning("Unknown search provider: %s. Returning empty.", provider)
        return [], 0.0


def _tavily_search(query: str, max_results: int, cfg: dict) -> tuple[list[SearchResult], float]:
    api_key = os.getenv("TAVILY_API_KEY") or cfg.get("tavily_api_key", "")
    if not api_key:
        logger.warning("TAVILY_API_KEY not set — search skipped")
        return [], 0.0

    payload = json.dumps({
        "api_key": api_key,
        "query": query,
        "max_results": max_results,
        "search_depth": "basic",
    }).encode("utf-8")

    try:
        req = urllib.request.Request(
            "https://api.tavily.com/search",
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=20) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        results = [
            SearchResult(
                url=r.get("url", ""),
                title=r.get("title", ""),
                snippet=r.get("content", ""),
                score=float(r.get("score", 0.0)),
            )
            for r in data.get("results", [])
            if r.get("url")
        ]
        return results, _TAVILY_COST_PER_QUERY
    except urllib.error.HTTPError as e:
        logger.warning("Tavily HTTP %s for query %r", e.code, query)
        return [], 0.0
    except Exception as e:
        logger.warning("Tavily search failed: %s", e)
        return [], 0.0


def _serper_search(query: str, max_results: int, cfg: dict) -> tuple[list[SearchResult], float]:
    api_key = os.getenv("SERPER_API_KEY") or cfg.get("serper_api_key", "")
    if not api_key:
        logger.warning("SERPER_API_KEY not set — search skipped")
        return [], 0.0

    payload = json.dumps({"q": query, "num": max_results}).encode("utf-8")

    try:
        req = urllib.request.Request(
            "https://google.serper.dev/search",
            data=payload,
            headers={
                "Content-Type": "application/json",
                "X-API-KEY": api_key,
            },
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=20) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        # Serper has no relevance scores — synthesize from result position
        results = [
            SearchResult(
                url=r.get("link", ""),
                title=r.get("title", ""),
                snippet=r.get("snippet", ""),
                score=1.0 / (rank + 1),  # rank 0 → 1.0, rank 1 → 0.5, rank 2 → 0.33…
            )
            for rank, r in enumerate(data.get("organic", []))
            if r.get("link")
        ]
        return results, _SERPER_COST_PER_QUERY
    except urllib.error.HTTPError as e:
        logger.warning("Serper HTTP %s for query %r", e.code, query)
        return [], 0.0
    except Exception as e:
        logger.warning("Serper search failed: %s", e)
        return [], 0.0
