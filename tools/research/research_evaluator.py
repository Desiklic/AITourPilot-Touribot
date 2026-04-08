"""Research evaluator — quality gate and gap analysis.

Uses research model (Sonnet) to evaluate coverage and identify gaps.
Called at the end of each deep reading phase to decide: synthesize or iterate?
"""
import json
import logging
import re

logger = logging.getLogger(__name__)

_EVAL_PROMPT = """You are evaluating whether a set of research excerpts sufficiently answers
a research question about a museum prospect for AITourPilot outreach.

Research question: {question}

Sub-questions that should be answered:
{sub_questions}

Excerpts collected so far (summaries):
{excerpt_summaries}

Respond with JSON only:
{{
  "coverage_score": 0.0-1.0,
  "answered_sub_questions": ["..."],
  "unanswered_sub_questions": ["..."],
  "gap_queries": ["search query 1", "search query 2"],
  "is_sufficient": true,
  "reasoning": "one sentence"
}}

is_sufficient should be true when coverage_score >= {min_coverage} and
the most important sub-questions are answered (especially: key decision maker,
current tech stack, and any personalization hooks).
"""


class EvalResult:
    __slots__ = ("coverage_score", "is_sufficient", "gap_queries", "reasoning", "cost_usd")

    def __init__(self, coverage_score: float, is_sufficient: bool,
                 gap_queries: list, reasoning: str, cost_usd: float = 0.0):
        self.coverage_score = coverage_score
        self.is_sufficient = is_sufficient
        self.gap_queries = gap_queries
        self.reasoning = reasoning
        self.cost_usd = cost_usd


def evaluate_coverage(question: str, sub_questions: list,
                      excerpts, min_coverage: float = 0.8) -> EvalResult:
    """Evaluate research coverage and return gap queries if insufficient."""
    from tools.research.gateway import chat

    excerpt_summaries = "\n\n".join(
        f"[{e.url}]\n{e.summary[:500]}" for e in excerpts[:40]
    )
    sub_q_text = "\n".join(f"- {q}" for q in sub_questions)
    prompt = _EVAL_PROMPT.format(
        question=question,
        sub_questions=sub_q_text,
        excerpt_summaries=excerpt_summaries,
        min_coverage=min_coverage,
    )

    resp = chat("research", [{"role": "user", "content": prompt}])
    cost = getattr(resp, "cost_usd", 0.0)

    if not resp.ok or not resp.text:
        logger.warning("Evaluator: empty response, defaulting to is_sufficient=False")
        return EvalResult(0.0, False, [], "evaluator failed", cost_usd=cost)

    text = resp.text.strip()

    # Try parsing the full response as JSON first
    try:
        d = json.loads(text)
        return EvalResult(
            coverage_score=float(d.get("coverage_score", 0.0)),
            is_sufficient=bool(d.get("is_sufficient", False)),
            gap_queries=d.get("gap_queries", []),
            reasoning=d.get("reasoning", ""),
            cost_usd=cost,
        )
    except (json.JSONDecodeError, ValueError, AttributeError):
        pass

    # Fallback: extract JSON object via regex (needs DOTALL for multiline JSON)
    m = re.search(r'\{.*\}', text, re.DOTALL)
    if m:
        try:
            d = json.loads(m.group(0))
            return EvalResult(
                coverage_score=float(d.get("coverage_score", 0.0)),
                is_sufficient=bool(d.get("is_sufficient", False)),
                gap_queries=d.get("gap_queries", []),
                reasoning=d.get("reasoning", ""),
                cost_usd=cost,
            )
        except (json.JSONDecodeError, KeyError, ValueError) as e:
            logger.warning("Evaluator: parse error: %s", e)

    return EvalResult(0.0, False, [], "parse failed", cost_usd=cost)
