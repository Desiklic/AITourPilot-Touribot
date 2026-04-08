"""Deep Research Orchestrator — synchronous state machine for web-grounded research.

Entry point: run_research(query, depth, session_id, museum_id) -> session_id

Synchronous (no asyncio, no subprocess). Progress printed to console.
Phases: planning → discovery → deep_reading → gap_analysis (optional loop) → synthesis → done.
State persisted to data/research.db after each phase.
Final report saved to output/research/YYYYMMDD_MUSEUM_NAME.md.
Research also saved to leads.db research table if museum_id is provided.
"""

import logging
import re
import sqlite3
from collections import deque
from datetime import datetime
from pathlib import Path
from typing import Optional

from tools.research.research_state import (
    ResearchState,
    SearchExcerpt,
    save_state,
)
from tools.research.research_planner import plan_queries
from tools.research.research_evaluator import evaluate_coverage
from tools.research.research_synthesizer import synthesize

logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).parent.parent.parent

# Depth preset: (max_search_queries, max_pages_to_read, max_gap_iterations)
_DEPTH_PRESETS_DEFAULT = {
    "quick":    (5,  5,  1),
    "standard": (10, 10, 2),
    "deep":     (20, 20, 4),
}


def _load_depth_presets() -> dict:
    """Load depth presets from settings.yaml, falling back to hardcoded defaults."""
    try:
        import yaml
        cfg = yaml.safe_load(
            (PROJECT_ROOT / "args" / "settings.yaml").read_text()
        ) or {}
        presets_cfg = cfg.get("deep_research", {}).get("presets", {})
        if not presets_cfg:
            return _DEPTH_PRESETS_DEFAULT
        result = {}
        for name, vals in presets_cfg.items():
            result[name] = (
                vals.get("max_queries", 10),
                vals.get("max_pages", 10),
                vals.get("max_gap_iterations", 2),
            )
        return {**_DEPTH_PRESETS_DEFAULT, **result}
    except Exception as e:
        logger.warning("_load_depth_presets failed, using defaults: %s", e)
        return _DEPTH_PRESETS_DEFAULT


_DEPTH_PRESETS = _load_depth_presets()


def run_research(query: str, depth: str = "standard",
                 session_id: Optional[str] = None,
                 museum_id: Optional[int] = None) -> str:
    """Run deep research synchronously. Returns session_id.

    Suitable for running in a background thread (via threading.Thread).
    Prints progress to console and persists to research.db.
    """
    if not query or not query.strip():
        return "Error: research query cannot be empty"

    # Build output path
    slug = re.sub(r"[^\w\s-]", "", query[:40]).strip().replace(" ", "_")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = PROJECT_ROOT / "output" / "research"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = str(output_dir / f"{timestamp}_{slug}.md")

    # Initialize state
    state = ResearchState(query=query, depth=depth)
    if session_id:
        state.session_id = session_id
    state.output_path = output_path
    state.museum_id = museum_id

    max_queries, max_pages, max_gaps = _DEPTH_PRESETS.get(depth, _DEPTH_PRESETS["standard"])

    _print(f"[{state.session_id}] Research started: {query[:80]}")
    _print(f"[{state.session_id}] Depth: {depth} — {max_queries} queries, {max_pages} pages, {max_gaps} gap iterations")

    _checkpoint(state)

    try:
        # Phase 1: Planning
        _phase_planning(state, max_queries)
        _checkpoint(state)

        # Phase 2+: Discovery → Deep Reading → Gap Analysis loop
        gap_iterations = 0
        while True:
            _phase_discovery(state, max_queries)
            _checkpoint(state)

            _phase_deep_reading(state, max_pages)
            _checkpoint(state)

            eval_result = _phase_gap_analysis(state)
            _checkpoint(state)

            if eval_result.is_sufficient:
                _print(f"[{state.session_id}] Quality gate passed (score={eval_result.coverage_score:.2f}) — synthesizing")
                break

            if gap_iterations >= max_gaps:
                _print(f"[{state.session_id}] Max gap iterations ({max_gaps}) reached — synthesizing with coverage={eval_result.coverage_score:.2f}")
                break

            # Push new gap queries onto the queue for next discovery pass
            state.gap_queue.extend(eval_result.gap_queries)
            gap_iterations += 1
            _print(f"[{state.session_id}] Gap iteration {gap_iterations} — {len(eval_result.gap_queries)} new queries queued")

        # Phase N: Synthesis
        _phase_synthesis(state)
        _checkpoint(state)

        _print(
            f"[{state.session_id}] COMPLETE — "
            f"{state.page_reads} pages, {state.search_calls} searches, "
            f"${state.total_cost_usd:.3f}"
        )
        _print(f"[{state.session_id}] Report: {state.output_path}")

        # Save to leads.db research table if museum_id is known
        if state.museum_id:
            _save_to_leads_db(state)

    except Exception as e:
        state.phase = "error"
        state.error_message = str(e)
        _checkpoint(state)
        logger.exception("Research [%s] failed: %s", state.session_id, e)
        _print(f"[{state.session_id}] ERROR: {e}")

    return state.session_id


# ---------------------------------------------------------------------------
# Phase implementations
# ---------------------------------------------------------------------------

def _phase_planning(state: ResearchState, max_queries: int) -> None:
    state.phase = "planning"
    _print(f"[{state.session_id}] Phase: planning ({max_queries} queries)")
    queries, cost = plan_queries(state.query, max_queries)
    state.total_cost_usd += cost
    state.llm_calls += 1
    state.sub_queries = queries
    state.gap_queue = deque(queries)  # seed the queue with the initial plan
    _print(f"[{state.session_id}] Planned {len(queries)} queries")


def _phase_discovery(state: ResearchState, max_queries: int) -> None:
    """Drain gap_queue (up to max_queries), issue searches, collect URLs."""
    from tools.research.search_client import search as web_search
    state.phase = "discovery"

    batch = []
    while state.gap_queue and len(batch) < max_queries:
        batch.append(state.gap_queue.popleft())

    if not batch:
        _print(f"[{state.session_id}] Discovery — no queries to run")
        return

    _print(f"[{state.session_id}] Phase: discovery — searching {len(batch)} queries")
    new_urls = 0
    for query in batch:
        results, search_cost = web_search(query, 10)
        state.search_calls += 1
        state.total_cost_usd += search_cost
        for r in results:
            if r.url not in state.visited_urls:
                state.visited_urls.add(r.url)
                state.excerpts.append(SearchExcerpt(
                    url=r.url, title=r.title, snippet=r.snippet,
                    full_text="", summary="", relevance=r.score,
                    fetched_at="",
                ))
                new_urls += 1

    _print(f"[{state.session_id}] Discovery found {new_urls} new URLs ({len(state.excerpts)} total)")


def _phase_deep_reading(state: ResearchState, max_pages: int) -> None:
    """Read top-K unread URLs via Jina, summarize via Haiku."""
    from tools.research.jina_reader import fetch_page
    from tools.research.gateway import chat
    state.phase = "deep_reading"

    # Select unread excerpts (full_text == ""), sorted by relevance desc
    unread = [e for e in state.excerpts if not e.full_text]
    unread.sort(key=lambda e: e.relevance, reverse=True)
    to_read = unread[:max_pages]

    _print(f"[{state.session_id}] Phase: deep_reading — reading {len(to_read)} pages")

    for i, excerpt in enumerate(to_read):
        full_text = fetch_page(excerpt.url)
        if not full_text:
            continue

        excerpt.full_text = full_text
        excerpt.fetched_at = datetime.now().isoformat()
        state.page_reads += 1

        # Summarize with Haiku (cheap, fast)
        summary_resp = chat(
            "fast_research",
            [{"role": "user", "content":
              f"Summarize this in 300 words for museum outreach research on: {state.query}\n\n{full_text[:8000]}"}],
        )
        if summary_resp.ok and summary_resp.text:
            excerpt.summary = summary_resp.text
            state.llm_calls += 1
            state.total_cost_usd += summary_resp.cost_usd

        if (i + 1) % 5 == 0:
            _print(f"[{state.session_id}] Read {i + 1}/{len(to_read)} pages so far...")

    _print(f"[{state.session_id}] Deep reading complete — {state.page_reads} pages total")


def _phase_gap_analysis(state: ResearchState):
    """Evaluate coverage and identify remaining gaps."""
    state.phase = "gap_analysis"
    _print(f"[{state.session_id}] Phase: gap_analysis")
    result = evaluate_coverage(state.query, state.sub_queries, state.excerpts)
    state.total_cost_usd += result.cost_usd
    state.llm_calls += 1
    _print(
        f"[{state.session_id}] Coverage: {result.coverage_score:.2f}, "
        f"sufficient: {result.is_sufficient}, gap queries: {len(result.gap_queries)}"
    )
    return result


def _phase_synthesis(state: ResearchState) -> None:
    """Produce and write the final museum prospect brief."""
    state.phase = "synthesis"
    _print(f"[{state.session_id}] Phase: synthesis — {len(state.excerpts)} sources")
    report, cost = synthesize(state)
    state.total_cost_usd += cost
    state.final_report = report
    state.llm_calls += 1

    # Write final report to disk
    out_path = Path(state.output_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(report)
    state.phase = "done"
    _print(f"[{state.session_id}] Report written: {state.output_path}")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _checkpoint(state: ResearchState) -> None:
    """Persist state to research.db for crash recovery and API status polling."""
    try:
        save_state(state)
    except Exception as e:
        logger.warning("Research checkpoint failed: %s", e)  # best-effort


def _print(message: str) -> None:
    """Print progress to console with timestamp."""
    ts = datetime.now().strftime("%H:%M:%S")
    print(f"[{ts}] {message}", flush=True)


def _save_to_leads_db(state: ResearchState) -> None:
    """Save final report to leads.db research table for the identified museum."""
    leads_db = PROJECT_ROOT / "data" / "leads.db"
    if not leads_db.exists():
        logger.warning("leads.db not found — skipping research save")
        return

    try:
        conn = sqlite3.connect(str(leads_db))
        try:
            # Mark any existing research for this museum as not current
            conn.execute(
                "UPDATE research SET is_current = 0 WHERE museum_id = ?",
                (state.museum_id,),
            )
            # Insert the new research brief
            conn.execute(
                """INSERT INTO research
                       (museum_id, insights, sources, created_at, is_current)
                   VALUES (?, ?, ?, ?, 1)""",
                (
                    state.museum_id,
                    state.final_report[:10000],  # trim to fit column (full text is in the file)
                    state.output_path,
                    datetime.now().isoformat(),
                ),
            )
            conn.commit()
            _print(f"[{state.session_id}] Research saved to leads.db (museum_id={state.museum_id})")
        finally:
            conn.close()
    except Exception as e:
        logger.warning("Failed to save research to leads.db: %s", e)
