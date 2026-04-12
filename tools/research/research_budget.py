"""Research budget enforcement — per-session cost gate for deep research.

Checks per-session budget cap against depth preset.
Adapted from FelixBot's tools/executors/research_budget.py.
"""
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).parent.parent.parent


def _load_research_budget_config() -> dict:
    try:
        import yaml
        cfg = yaml.safe_load(
            (PROJECT_ROOT / "args" / "settings.yaml").read_text()
        ) or {}
        return cfg.get("deep_research", {}).get("budget", {})
    except Exception:
        return {}


class ResearchBudget:
    """Tracks costs for one research session. Thread-safe read, single-writer."""

    def __init__(self, session_id: str, depth: str = "standard"):
        cfg = _load_research_budget_config()
        depth_caps = {
            "quick":      cfg.get("quick_session_usd",      0.20),
            "standard":   cfg.get("standard_session_usd",   0.60),
            "deep":       cfg.get("deep_session_usd",        2.50),
            "exhaustive": cfg.get("exhaustive_session_usd",  3.00),
        }
        self._cap = depth_caps.get(depth, 0.60)
        self._spent = 0.0
        self._session_id = session_id

    def record(self, cost_usd: float) -> None:
        """Add cost_usd to the running total for this session."""
        self._spent += cost_usd

    @property
    def total_cost(self) -> float:
        return self._spent

    @property
    def spent(self) -> float:
        return self._spent

    @property
    def cap(self) -> float:
        return self._cap

    @property
    def remaining(self) -> float:
        return max(0.0, self._cap - self._spent)

    def exhausted(self) -> bool:
        """True when session budget is spent."""
        if self._spent >= self._cap:
            logger.info(
                "Research [%s]: budget cap $%.2f reached (spent $%.3f)",
                self._session_id, self._cap, self._spent,
            )
            return True
        return False
