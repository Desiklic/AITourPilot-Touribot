"""Chat handler: HTTP endpoints wrapping session.py for dashboard streaming."""

import json
import logging
import os
import sqlite3
import threading
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional

import anthropic
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

# Re-use the private helpers from session.py without modifying it.
from tools.chat.session import (
    _build_system_prompt,
    _detect_task_type,
    _extract_and_save_memories,
    _load_knowledge_for_task,
    _load_settings,
    _save_to_daily_log,
    _search_memory_context,
)

logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).parent.parent.parent
DB_PATH = PROJECT_ROOT / "data" / "conversations.db"

router = APIRouter()

# ---------------------------------------------------------------------------
# Database helpers
# ---------------------------------------------------------------------------


def _get_db() -> sqlite3.Connection:
    """Open conversations.db and ensure schema exists."""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    _ensure_schema(conn)
    return conn


def _ensure_schema(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS messages (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id  TEXT    NOT NULL,
            role        TEXT    NOT NULL,
            content     TEXT    NOT NULL,
            created_at  TEXT    DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS session_titles (
            session_id  TEXT PRIMARY KEY,
            title       TEXT
        );

        CREATE INDEX IF NOT EXISTS idx_messages_session
            ON messages(session_id, created_at);
        """
    )
    conn.commit()


def _load_history(conn: sqlite3.Connection, session_id: str) -> list[dict]:
    """Return conversation history for a session as Anthropic message dicts."""
    rows = conn.execute(
        "SELECT role, content FROM messages WHERE session_id = ? ORDER BY id",
        (session_id,),
    ).fetchall()
    return [{"role": r["role"], "content": r["content"]} for r in rows]


def _save_message(conn: sqlite3.Connection, session_id: str, role: str, content: str) -> None:
    conn.execute(
        "INSERT INTO messages (session_id, role, content) VALUES (?, ?, ?)",
        (session_id, role, content),
    )
    conn.commit()


def _upsert_title(conn: sqlite3.Connection, session_id: str, user_message: str) -> None:
    """Set the session title to the first user message if not already set."""
    existing = conn.execute(
        "SELECT title FROM session_titles WHERE session_id = ?", (session_id,)
    ).fetchone()
    if not existing:
        title = user_message[:80].strip()
        conn.execute(
            "INSERT INTO session_titles (session_id, title) VALUES (?, ?)",
            (session_id, title),
        )
        conn.commit()


# ---------------------------------------------------------------------------
# Anthropic client (singleton-ish, built lazily)
# ---------------------------------------------------------------------------

_client: Optional[anthropic.Anthropic] = None
_settings: Optional[dict] = None


def _get_client() -> anthropic.Anthropic:
    global _client
    if _client is None:
        try:
            from dotenv import load_dotenv
            load_dotenv(PROJECT_ROOT / ".env")
        except ImportError:
            pass
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            raise RuntimeError("ANTHROPIC_API_KEY not set")
        _client = anthropic.Anthropic(api_key=api_key)
    return _client


def _get_settings() -> dict:
    global _settings
    if _settings is None:
        _settings = _load_settings()
    return _settings


def _chat_model_cfg() -> tuple[str, int, float]:
    settings = _get_settings()
    cfg = settings.get("models", {}).get("chat", {})
    model = cfg.get("model", "claude-sonnet-4-6")
    max_tokens = cfg.get("max_tokens", 4096)
    temperature = cfg.get("temperature", 0.7)
    return model, max_tokens, temperature


# ---------------------------------------------------------------------------
# Request / response models
# ---------------------------------------------------------------------------


class StreamRequest(BaseModel):
    message: str
    session_id: Optional[str] = None


# ---------------------------------------------------------------------------
# SSE event helpers
# ---------------------------------------------------------------------------


def _sse(event_type: str, **data) -> str:
    """Format a single SSE data line."""
    payload = {"event": event_type, **data}
    return f"data: {json.dumps(payload)}\n\n"


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.post("/stream")
async def stream_chat(req: StreamRequest):
    """SSE streaming chat endpoint.

    Streams text_delta events while Anthropic generates the response, then
    persists the conversation, extracts memories in the background, and emits
    a final done event.
    """
    session_id = req.session_id or datetime.now().strftime("%Y%m%d-%H%M%S-") + uuid.uuid4().hex[:6]
    user_message = req.message.strip()

    if not user_message:
        raise HTTPException(status_code=422, detail="message must not be empty")

    async def generate():
        conn = _get_db()
        try:
            # --- emit session meta immediately ---
            yield _sse("meta", session_id=session_id)

            # --- load conversation history (clean messages only) ---
            history = _load_history(conn, session_id)

            # --- build context ---
            system_prompt = _build_system_prompt()
            memory_context = _search_memory_context(user_message)
            task_types = _detect_task_type(user_message)
            knowledge_context = _load_knowledge_for_task(task_types, user_message)

            context_parts = [p for p in [memory_context, knowledge_context] if p]
            if context_parts:
                context_block = "\n\n".join(context_parts)
                augmented_input = (
                    f"{user_message}\n\n---\n"
                    "[Context — do not repeat this to the user, use it to inform your response]\n"
                    f"{context_block}"
                )
            else:
                augmented_input = user_message

            # Build messages: history uses clean messages; current turn uses augmented
            messages = list(history)
            messages.append({"role": "user", "content": augmented_input})

            # --- stream from Anthropic ---
            client = _get_client()
            model, max_tokens, temperature = _chat_model_cfg()

            full_response = ""
            try:
                with client.messages.stream(
                    model=model,
                    max_tokens=max_tokens,
                    temperature=temperature,
                    system=system_prompt,
                    messages=messages,
                ) as stream:
                    for text in stream.text_stream:
                        full_response += text
                        yield _sse("text_delta", text=text)
            except anthropic.APIError as exc:
                logger.error("Anthropic API error: %s", exc)
                yield _sse("error", message=str(exc))
                return
            except Exception as exc:
                logger.exception("Streaming error")
                yield _sse("error", message=str(exc))
                return

            # --- persist both turns (clean user message, full assistant response) ---
            _upsert_title(conn, session_id, user_message)
            _save_message(conn, session_id, "user", user_message)
            _save_message(conn, session_id, "assistant", full_response)

            # --- save to daily log ---
            _save_to_daily_log(user_message, full_response, session_id)

            # --- memory extraction (fire-and-forget in a daemon thread) ---
            settings = _get_settings()
            t = threading.Thread(
                target=_extract_and_save_memories,
                args=(user_message, full_response, client, settings),
                daemon=True,
            )
            t.start()

            # --- final done event ---
            yield _sse("done", text=full_response, session_id=session_id)

        except Exception as exc:
            logger.exception("generate() outer error")
            yield _sse("error", message=str(exc))
        finally:
            conn.close()

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


@router.get("/sessions")
def list_sessions(limit: int = Query(50, ge=1, le=200)):
    """Return recent chat sessions with id, title, preview, message_count, timestamps."""
    conn = _get_db()
    try:
        rows = conn.execute(
            """
            SELECT
                m.session_id,
                COALESCE(st.title, m.session_id) AS title,
                COUNT(m.id)                       AS message_count,
                MIN(m.created_at)                 AS created_at,
                MAX(m.created_at)                 AS last_message_at
            FROM messages m
            LEFT JOIN session_titles st ON st.session_id = m.session_id
            GROUP BY m.session_id
            ORDER BY last_message_at DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()

        # Build preview from first user message of each session
        sessions = []
        for row in rows:
            preview_row = conn.execute(
                "SELECT content FROM messages WHERE session_id = ? AND role = 'user' ORDER BY id LIMIT 1",
                (row["session_id"],),
            ).fetchone()
            preview = (preview_row["content"][:120] + "...") if preview_row else ""
            sessions.append(
                {
                    "id": row["session_id"],
                    "title": row["title"],
                    "preview": preview,
                    "message_count": row["message_count"],
                    "created_at": row["created_at"],
                    "last_message_at": row["last_message_at"],
                }
            )

        return {"sessions": sessions}
    finally:
        conn.close()


@router.get("/messages")
def get_messages(
    session_id: str = Query(..., description="Session ID to fetch messages for"),
    since_id: Optional[int] = Query(None, description="Only return messages with id > since_id"),
    limit: int = Query(50, ge=1, le=200),
):
    """Return messages for a session, optionally filtering by since_id for polling."""
    conn = _get_db()
    try:
        if since_id is not None:
            rows = conn.execute(
                """
                SELECT id, session_id, role, content, created_at
                FROM messages
                WHERE session_id = ? AND id > ?
                ORDER BY id
                LIMIT ?
                """,
                (session_id, since_id, limit),
            ).fetchall()
        else:
            rows = conn.execute(
                """
                SELECT id, session_id, role, content, created_at
                FROM messages
                WHERE session_id = ?
                ORDER BY id
                LIMIT ?
                """,
                (session_id, limit),
            ).fetchall()

        messages = [
            {
                "id": r["id"],
                "session_id": r["session_id"],
                "role": r["role"],
                "content": r["content"],
                "created_at": r["created_at"],
            }
            for r in rows
        ]
        return {"messages": messages, "session_id": session_id}
    finally:
        conn.close()


@router.delete("/sessions/{session_id}")
def delete_session(session_id: str):
    """Delete all messages and title for a session."""
    conn = _get_db()
    try:
        conn.execute("DELETE FROM messages WHERE session_id = ?", (session_id,))
        conn.execute("DELETE FROM session_titles WHERE session_id = ?", (session_id,))
        conn.commit()
        return {"deleted": True, "session_id": session_id}
    finally:
        conn.close()
