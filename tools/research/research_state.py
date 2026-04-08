"""ResearchState — typed dataclass + SQLite persistence for research sessions.

State is persisted after each phase transition. If the process crashes and restarts,
the orchestrator can resume from the last checkpoint.
"""
import json
import sqlite3
import uuid
from collections import deque
from dataclasses import dataclass, field, fields
from datetime import datetime
from pathlib import Path
from typing import Optional

PROJECT_ROOT = Path(__file__).parent.parent.parent
RESEARCH_DB = PROJECT_ROOT / "data" / "research.db"

PHASES = ["planning", "discovery", "deep_reading", "gap_analysis", "synthesis", "done", "error"]


@dataclass
class SearchExcerpt:
    url: str
    title: str
    snippet: str          # raw search snippet
    full_text: str        # Jina-fetched markdown (up to max_chars)
    summary: str          # Haiku-generated summary
    relevance: float      # 0.0-1.0 estimated relevance
    fetched_at: str       # ISO timestamp


@dataclass
class ResearchState:
    session_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    query: str = ""
    depth: str = "standard"       # quick | standard | deep
    phase: str = "planning"
    sub_queries: list = field(default_factory=list)
    gap_queue: deque = field(default_factory=deque)   # FIFO gap questions
    visited_urls: set = field(default_factory=set)
    excerpts: list = field(default_factory=list)
    final_report: str = ""
    output_path: str = ""
    started_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())
    search_calls: int = 0
    page_reads: int = 0
    llm_calls: int = 0
    total_cost_usd: float = 0.0
    error_message: str = ""
    museum_id: Optional[int] = None   # foreign key into leads.db museums table

    def to_json(self) -> str:
        d = {k: v for k, v in self.__dict__.items()}
        d["visited_urls"] = list(self.visited_urls)
        d["gap_queue"] = list(self.gap_queue)  # deque is not JSON-serializable
        d["excerpts"] = [e.__dict__ for e in self.excerpts]
        return json.dumps(d)

    @classmethod
    def from_json(cls, text: str) -> "ResearchState":
        d = json.loads(text)
        excerpts = [SearchExcerpt(**e) for e in d.pop("excerpts", [])]
        visited = set(d.pop("visited_urls", []))
        gap_queue = deque(d.pop("gap_queue", []))  # list → deque on load
        # Filter to known fields so old/new JSON with extra or missing keys doesn't crash
        valid = {f.name for f in fields(cls)}
        state = cls(**{k: v for k, v in d.items() if k in valid})
        state.excerpts = excerpts
        state.visited_urls = visited
        state.gap_queue = gap_queue
        return state


def _get_db(db_path: Path = RESEARCH_DB) -> sqlite3.Connection:
    """Open research.db, creating schema if needed."""
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path))
    try:
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA busy_timeout=5000")
        conn.execute("""
            CREATE TABLE IF NOT EXISTS research_sessions (
                session_id TEXT PRIMARY KEY,
                phase TEXT NOT NULL,
                query TEXT NOT NULL,
                depth TEXT NOT NULL,
                state_json TEXT NOT NULL,
                started_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        """)
        conn.commit()
    except Exception:
        conn.close()
        raise
    return conn


def save_state(state: ResearchState, db_path: Path = RESEARCH_DB) -> None:
    """Upsert ResearchState into research.db."""
    state.updated_at = datetime.now().isoformat()
    conn = _get_db(db_path)
    try:
        conn.execute("""
            INSERT INTO research_sessions
                (session_id, phase, query, depth, state_json, started_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(session_id) DO UPDATE SET
                phase = excluded.phase,
                state_json = excluded.state_json,
                updated_at = excluded.updated_at
        """, (
            state.session_id,
            state.phase,
            state.query,
            state.depth,
            state.to_json(),
            state.started_at,
            state.updated_at,
        ))
        conn.commit()
    finally:
        conn.close()


def load_state(session_id: str, db_path: Path = RESEARCH_DB) -> Optional[ResearchState]:
    """Load a ResearchState by session_id. Returns None if not found."""
    if not db_path.exists():
        return None
    conn = _get_db(db_path)
    try:
        row = conn.execute(
            "SELECT state_json FROM research_sessions WHERE session_id = ?",
            (session_id,),
        ).fetchone()
        if row is None:
            return None
        return ResearchState.from_json(row[0])
    finally:
        conn.close()


def list_active_sessions(db_path: Path = RESEARCH_DB) -> list:
    """Return all sessions not in done/error phase."""
    if not db_path.exists():
        return []
    conn = _get_db(db_path)
    try:
        rows = conn.execute(
            "SELECT session_id, phase, query, depth, updated_at FROM research_sessions "
            "WHERE phase NOT IN ('done', 'error') ORDER BY updated_at DESC"
        ).fetchall()
        return [
            {"session_id": r[0], "phase": r[1], "query": r[2],
             "depth": r[3], "updated_at": r[4]}
            for r in rows
        ]
    finally:
        conn.close()
