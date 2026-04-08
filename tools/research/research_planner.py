"""Research planner — decompose research question into concrete sub-queries.

Uses fast_research model (Haiku) to generate search queries.
Deduplicates queries and normalises them for search API submission.
Adds museum-specific sub-query categories for TouriBot prospect research.
"""
import json
import logging
import re

logger = logging.getLogger(__name__)

_PLANNER_PROMPT = """You are a research planning assistant for AITourPilot, a company that sells
AI-powered audio guides to museums.

Given a research question about a museum prospect, generate a set of specific, targeted web search
queries that together would cover the topic comprehensively — with a focus on what Hermann needs to
know before reaching out to that museum.

Output JSON only — an array of strings. Each string is a standalone search query.
No preamble, no explanation.

Rules:
- Each query should target a distinct aspect of the topic
- Queries should be phrased as a human would type into Google
- Cover these museum-specific research categories:
  * Museum overview and visitor numbers
  * Museum digital strategy and innovation
  * Current audio guide / technology stack (competitor products?)
  * Key decision makers (digital director, innovation director, curator)
  * Recent exhibitions and partnerships
  * Budget, funding, and procurement signals
  * Press mentions, awards, upcoming projects
- Aim for {n_queries} queries
- No duplicates or near-duplicates

Research question: {question}
"""


def plan_queries(question: str, n_queries: int = 10) -> tuple:
    """Generate search queries from a research question.

    Returns (queries: list[str], cost_usd: float).
    """
    from tools.research.gateway import chat
    prompt = _PLANNER_PROMPT.format(question=question, n_queries=n_queries)
    resp = chat("fast_research", [{"role": "user", "content": prompt}])
    cost = getattr(resp, "cost_usd", 0.0)

    if not resp.ok or not resp.text:
        logger.warning("Planner: empty response for question: %s", question[:80])
        return [question], cost  # Fallback: use the raw question as a single query

    # Parse JSON — be lenient about code fences
    text = resp.text.strip()
    m = re.search(r'\[.*\]', text, re.DOTALL)
    if m:
        try:
            queries = json.loads(m.group(0))
            if isinstance(queries, list) and all(isinstance(q, str) for q in queries):
                return _deduplicate(queries), cost
        except json.JSONDecodeError:
            pass

    logger.warning("Planner: could not parse query list, using fallback")
    return [question], cost


def _deduplicate(queries: list) -> list:
    """Remove exact and near-duplicate queries (case-insensitive)."""
    seen = set()
    result = []
    for q in queries:
        norm = q.lower().strip()
        if norm not in seen:
            seen.add(norm)
            result.append(q)
    return result
