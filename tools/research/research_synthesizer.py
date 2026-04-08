"""Research synthesizer — produce final museum prospect brief from collected excerpts.

Uses Sonnet for synthesis with progressive fallback:
full context → reduced context → summaries-only → raw findings.
Guarantees a usable document is ALWAYS produced — never loses research.
"""
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

# Progressive context reduction tiers for synthesis retries.
# Each tier: (max_excerpts, max_text_per_excerpt, model_area, description)
_SYNTHESIS_TIERS = [
    (25, 6000, "deep_research", "full context"),
    (15, 3000, "research",      "reduced context"),
    (20, 0,    "research",      "summaries only"),   # 0 = skip full_text
    (10, 0,    "fast_research", "minimal summaries"),
]

_SYNTHESIS_SYSTEM = """You are producing a FINAL, COMPREHENSIVE museum prospect brief
from collected web sources. You are helping Hermann Kudlich of AITourPilot prepare
for outreach to a museum.

AITourPilot sells AI-powered audio guides that replace traditional audio guide hardware with
a mobile app. The ideal prospect is a museum actively investing in digital visitor experience.

YOUR OUTPUT WINDOW IS 32,000 TOKENS. Use as much as the content demands.

MANDATORY STRUCTURE — every section must be present:

1. Executive Summary (300-500 words)
   — Key takeaways, fit score (1-10), recommended next action

2. Museum Overview
   — Size, visitor numbers, collections, location, prestige
   — Recent major exhibitions or milestones

3. Digital Strategy & Technology
   — Current audio guide / visitor app setup (competitor products identified?)
   — Website / digital maturity signals
   — Any tech partnerships, innovation labs, or digital projects mentioned

4. Key Decision Makers
   — Digital Director, Innovation Director, Head of Visitor Experience, or equivalent
   — Curators or department heads relevant to audio guide decisions
   — Names, LinkedIn profiles, recent quotes or publications if found

5. Procurement & Budget Signals
   — Funding sources (government, private, endowment)
   — Recent grants, EU cultural funding, renovation projects
   — Any mentions of procurement, tenders, or vendor evaluations

6. Personalization Hooks for Outreach
   — Specific facts Hermann can reference to show he did his homework
   — Recent news, exhibitions, or initiatives to mention
   — Shared interests or connections

7. Recommended Email Angle
   — 2-3 sentence summary of the most compelling pitch angle for this specific museum
   — Suggested subject line

8. Sources
   — Every URL cited, with title and relevance note

Format: Markdown
"""

_SYNTHESIS_PROMPT = """Research question: {question}

Source excerpts:
{excerpts}

Produce the final museum prospect brief now.
"""


def synthesize(state) -> tuple:
    """Synthesize research state into a final museum prospect brief.

    Progressive fallback: tries increasingly smaller context sizes.
    If ALL LLM attempts fail, assembles a raw findings document from
    summaries — guarantees a usable document is always produced.

    Returns (report: str, cost_usd: float).
    """
    from tools.research.gateway import chat

    all_excerpts = state.excerpts
    total_cost = 0.0

    # Try each synthesis tier with progressively smaller context
    for tier_idx, (max_exc, max_text, model, desc) in enumerate(_SYNTHESIS_TIERS):
        excerpts = _select_top_excerpts(all_excerpts, max_exc)
        excerpt_text = _format_excerpts(excerpts, max_text)
        prompt = _SYNTHESIS_PROMPT.format(
            question=state.query,
            excerpts=excerpt_text,
        )
        prompt_chars = len(prompt) + len(_SYNTHESIS_SYSTEM)
        logger.info(
            "Synthesis tier %d/%d (%s): %d excerpts, ~%dK chars, model=%s",
            tier_idx + 1, len(_SYNTHESIS_TIERS), desc,
            len(excerpts), prompt_chars // 1000, model,
        )

        resp = chat(model, [{"role": "user", "content": prompt}],
                    system=_SYNTHESIS_SYSTEM, max_tokens=8192)
        total_cost += getattr(resp, "cost_usd", 0.0)

        if resp.ok and resp.text and len(resp.text) > 500:
            report = _add_metadata_header(resp.text, state)
            logger.info("Synthesis succeeded on tier %d (%s): %d chars",
                        tier_idx + 1, desc, len(report))
            return report, total_cost

        logger.warning(
            "Synthesis tier %d failed: %s",
            tier_idx + 1, getattr(resp, "error", None) or "empty/short response",
        )

    # ALL tiers failed — assemble raw findings from summaries (no LLM needed)
    logger.warning("All synthesis tiers failed — assembling raw findings document")
    report = _assemble_raw_findings(state)
    return report, total_cost


def _select_top_excerpts(excerpts: list, max_count: int) -> list:
    """Select top excerpts by summary richness (longer summary = more useful)."""
    if len(excerpts) <= max_count:
        return excerpts
    return sorted(
        excerpts,
        key=lambda e: len(getattr(e, "summary", "") or ""),
        reverse=True,
    )[:max_count]


def _format_excerpts(excerpts: list, max_text: int = 6000) -> str:
    """Format excerpts for the synthesis prompt."""
    parts = []
    for i, e in enumerate(excerpts, 1):
        block = (
            f"--- Source {i}: {e.url} ---\n"
            f"Title: {e.title}\n"
            f"Summary: {e.summary}"
        )
        if max_text > 0 and getattr(e, "full_text", ""):
            block += f"\n\nFull excerpt:\n{e.full_text[:max_text]}"
        parts.append(block)
    return "\n\n".join(parts)


def _add_metadata_header(report: str, state) -> str:
    header = (
        f"# Museum Prospect Brief: {state.query}\n\n"
        f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M')}\n"
        f"**Session:** {state.session_id}\n"
        f"**Depth:** {state.depth}\n"
        f"**Sources read:** {state.page_reads}\n"
        f"**Search queries issued:** {state.search_calls}\n"
        f"**Total cost:** ${state.total_cost_usd:.3f}\n\n"
        f"---\n\n"
    )
    return header + report


def _assemble_raw_findings(state) -> str:
    """Assemble a structured document from raw summaries — no LLM call needed.

    Last-resort fallback when ALL synthesis attempts fail.
    """
    parts = [
        f"# Raw Research Findings: {state.query}\n",
        f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        f"**Session:** {state.session_id}",
        f"**Depth:** {state.depth}",
        f"**Sources read:** {state.page_reads}",
        f"**Search queries issued:** {state.search_calls}",
        f"**Total cost:** ${state.total_cost_usd:.3f}\n",
        "---\n",
        "> **Note:** Automated synthesis failed after multiple attempts. "
        "This document contains all collected source summaries. "
        "Re-run synthesis manually from this data.\n",
        "---\n",
    ]

    for i, e in enumerate(state.excerpts, 1):
        parts.append(f"## Source {i}: {getattr(e, 'title', 'Untitled')}")
        parts.append(f"**URL:** {getattr(e, 'url', 'N/A')}")
        summary = getattr(e, "summary", "")
        if summary:
            parts.append(f"\n{summary}")
        parts.append("---\n")

    return "\n\n".join(parts)
