"""Research synthesizer — produce final museum prospect brief from collected excerpts.

Single-pass for quick/standard/deep depth; multi-pass for exhaustive depth (>15 sources).
Multi-pass: Phase1=theme extraction, Phase2=source assignment, Phase3=per-theme
synthesis, Phase4=executive merge. Guarantees output via raw-findings fallback.
"""
import json
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

# Progressive context reduction tiers for single-pass synthesis retries.
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

LENGTH GUIDANCE: Standard=5,000-10,000 words; Deep=10,000-20,000 words; Exhaustive=20,000-40,000+ words.
For EXHAUSTIVE multi-pass reports: you are writing ONE SECTION — focus ONLY on the assigned theme, 3,000-8,000 words.

DO NOT STOP SHORT. Every source deserves proper analysis. When in doubt, write MORE.

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

_THEME_EXTRACTION_PROMPT = (
    "Research question: {question}\n\nSource summaries:\n{summaries}\n\n"
    "Identify 5-8 major themes. Return ONLY valid JSON — no prose, no markdown fences.\n"
    'Format: [{{"theme": "...", "keywords": ["...", "..."]}}]'
)

_PER_THEME_PROMPT = (
    'Research question: {question}\n\nTheme: "{theme}"\n\n'
    "Source excerpts for this theme:\n{excerpts}\n\n"
    "Write a DEEP, comprehensive analysis of this theme using the {n} sources above. "
    "Target: 3,000-8,000 words. Cover every source thoroughly. Use markdown."
)

_MERGE_PROMPT = (
    "Research question: {question}\n\n"
    "You have {n_themes} deep per-theme sections from a multi-pass synthesis. "
    "Produce the final integrated museum prospect brief.\n\n"
    "Per-theme sections:\n{sections}\n\nSource list:\n{source_list}\n\n"
    "Structure: 1. Executive Summary (1,000-2,000 words) 2. Key Findings (15-30 items) "
    "3. Source Comparison Matrix 4. Conclusions (with confidence levels) 5. Methodology "
    '6. Full Source List\n\nThen append all per-theme sections under "## Detailed Analysis". '
    "Format: Markdown"
)


def synthesize(state) -> tuple:
    """Main entry point. Routes to single-pass or multi-pass based on depth.

    Multi-pass is used only for exhaustive depth with >15 sources.
    Returns (report: str, cost_usd: float).
    """
    if state.depth == "exhaustive" and len(state.excerpts) > 15:
        return _synthesize_multi_pass(state)
    return _synthesize_single_pass(state)


def _synthesize_single_pass(state) -> tuple:
    """Single-pass synthesis with progressive fallback tiers.

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


def _synthesize_multi_pass(state) -> tuple:
    """Multi-pass synthesis for exhaustive depth with >15 sources.

    Phase 1: Theme extraction via fast_research (~$0.01)
    Phase 2: Source assignment to themes (pure Python, no LLM)
    Phase 3: Per-theme deep synthesis via deep_research (~$0.10-0.20 per theme)
    Phase 4: Executive merge via deep_research (~$0.20)

    Falls back to single-pass if theme extraction fails.
    Returns (report: str, cost_usd: float).
    """
    from tools.research.gateway import chat

    total_cost = 0.0

    # Phase 1: Extract themes
    themes = _extract_themes(state, chat)
    if themes is None:
        logger.warning("Multi-pass: theme extraction failed — falling back to single-pass")
        return _synthesize_single_pass(state)
    total_cost += themes["cost"]
    theme_list = themes["themes"]
    logger.info("Multi-pass: extracted %d themes", len(theme_list))

    # Phase 2: Assign sources to themes
    assignments = _assign_sources_to_themes(state.excerpts, theme_list)

    # Phase 3: Per-theme deep synthesis
    theme_sections = []
    for theme_entry in theme_list:
        theme_name = theme_entry["theme"]
        assigned = assignments.get(theme_name, [])
        if not assigned:
            # Fall back to summaries-only for this theme if no sources assigned
            assigned = state.excerpts[:5]

        prompt = _PER_THEME_PROMPT.format(
            question=state.query,
            theme=theme_name,
            excerpts=_format_excerpts(assigned, max_text=6000),
            n=len(assigned),
        )
        resp = chat("deep_research", [{"role": "user", "content": prompt}],
                    system=_SYNTHESIS_SYSTEM, max_tokens=8192)
        total_cost += getattr(resp, "cost_usd", 0.0)

        if resp.ok and resp.text and len(resp.text) > 200:
            theme_sections.append(f"## Theme: {theme_name}\n\n{resp.text}")
            logger.info("Multi-pass phase 3: theme '%s' synthesized (%d chars)", theme_name, len(resp.text))
        else:
            # Per-theme synthesis failed — use raw summaries for this theme
            logger.warning("Multi-pass: theme '%s' synthesis failed — using raw summaries", theme_name)
            raw = "\n\n".join(
                f"**{getattr(e, 'title', 'Untitled')}** ({e.url})\n{getattr(e, 'summary', '')}"
                for e in assigned
            )
            theme_sections.append(f"## Theme: {theme_name}\n\n{raw}")

    # Phase 4: Executive merge
    source_list = "\n".join(
        f"- [{getattr(e, 'title', 'Untitled')}]({e.url})"
        for e in state.excerpts
    )
    merge_prompt = _MERGE_PROMPT.format(
        question=state.query,
        n_themes=len(theme_sections),
        sections="\n\n---\n\n".join(theme_sections),
        source_list=source_list,
    )
    merge_resp = chat("deep_research", [{"role": "user", "content": merge_prompt}],
                      system=_SYNTHESIS_SYSTEM, max_tokens=8192)
    total_cost += getattr(merge_resp, "cost_usd", 0.0)

    if merge_resp.ok and merge_resp.text and len(merge_resp.text) > 500:
        report = _add_metadata_header(merge_resp.text, state)
    else:
        # Merge failed — concatenate per-theme sections as-is
        logger.warning("Multi-pass: executive merge failed — concatenating theme sections")
        report = _add_metadata_header("\n\n---\n\n".join(theme_sections), state)

    logger.info("Multi-pass synthesis complete: %d chars, cost=$%.3f", len(report), total_cost)
    return report, total_cost


def _extract_themes(state, chat) -> dict | None:
    """Phase 1: Ask the LLM to identify major themes from all source summaries.

    Returns {"themes": [...], "cost": float} or None on failure.
    """
    summaries = "\n".join(
        f"- [{getattr(e, 'title', 'Untitled')}] {(getattr(e, 'summary', '') or '')[:200]}"
        for e in state.excerpts
    )
    prompt = _THEME_EXTRACTION_PROMPT.format(
        question=state.query,
        summaries=summaries,
    )
    resp = chat("fast_research", [{"role": "user", "content": prompt}])
    cost = getattr(resp, "cost_usd", 0.0)

    if not resp.ok or not resp.text:
        return None

    # Strip markdown fences if the model wrapped the JSON anyway
    raw = resp.text.strip()
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
        raw = raw.strip()

    try:
        themes = json.loads(raw)
        if not isinstance(themes, list) or not themes:
            return None
        # Normalise entries to ensure "theme" and "keywords" keys exist
        cleaned = [
            {"theme": t.get("theme", ""), "keywords": t.get("keywords", [])}
            for t in themes if isinstance(t, dict) and t.get("theme")
        ]
        return {"themes": cleaned, "cost": cost}
    except (json.JSONDecodeError, AttributeError):
        return None


def _assign_sources_to_themes(excerpts: list, themes: list) -> dict:
    """Phase 2: Assign each excerpt to its best-matching theme by keyword overlap.

    Pure Python — no LLM call. Returns {theme_name: [excerpt, ...]}
    """
    assignments: dict = {t["theme"]: [] for t in themes}

    for excerpt in excerpts:
        text = (
            (getattr(excerpt, "title", "") or "") + " " +
            (getattr(excerpt, "summary", "") or "")
        ).lower()

        best_theme = None
        best_score = -1
        for t in themes:
            score = sum(1 for kw in t.get("keywords", []) if kw.lower() in text)
            if score > best_score:
                best_score = score
                best_theme = t["theme"]

        # Always assign to at least the best match (even if score == 0)
        if best_theme is not None:
            assignments[best_theme].append(excerpt)

    return assignments


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

    This is the last-resort fallback when ALL synthesis attempts fail.
    It produces a usable document from the per-page summaries that were
    already collected during the deep reading phase.
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
        "This document contains all collected source summaries organized "
        "by source. The raw findings preserve the full research value — "
        "a synthesis can be re-attempted later from this data.\n",
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
