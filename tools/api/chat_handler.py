"""Chat handler: HTTP endpoints wrapping session.py for dashboard streaming."""

import base64
import json
import logging
import os
import re
import sqlite3
import threading
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional

import anthropic
from fastapi import APIRouter, HTTPException, Query, Request, UploadFile
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

# Re-use the private helpers from session.py without modifying it.
from tools.chat.session import (
    _assemble_context,
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
# File upload helpers
# ---------------------------------------------------------------------------

UPLOADS_ROOT = PROJECT_ROOT / "data" / "uploads"
SUPPORTED_IMAGE_MIMES = {"image/jpeg", "image/png", "image/gif", "image/webp"}
BINARY_DOC_SUFFIXES = {".pdf", ".docx", ".doc"}
MAX_TEXT_CHARS = 15_000


def _sanitize_filename(name: str) -> str:
    """Strip path components and replace unsafe characters."""
    name = Path(name).name  # drop any directory traversal
    name = re.sub(r"[^\w.\-]", "_", name)
    return name or "upload"


async def _save_uploaded_files(files: list[UploadFile]) -> list[dict]:
    """Save UploadFile objects to dated subdirectory and return attachment metadata."""
    date_dir = UPLOADS_ROOT / datetime.now().strftime("%Y-%m-%d")
    date_dir.mkdir(parents=True, exist_ok=True)

    attachments = []
    for uf in files:
        if uf.filename is None:
            continue
        safe_name = _sanitize_filename(uf.filename)
        # Prefix with a short UUID fragment to avoid collisions
        unique_name = f"{uuid.uuid4().hex[:8]}_{safe_name}"
        dest = date_dir / unique_name

        content = await uf.read()
        dest.write_bytes(content)

        attachments.append({
            "filename": str(dest.relative_to(UPLOADS_ROOT)),
            "display_name": uf.filename,
            "mime_type": uf.content_type or "",
            "size": len(content),
        })
    return attachments


def _build_user_content(text: str, attachments: list | None) -> str | list:
    """Return a plain string or multimodal content list for the user turn."""
    if not attachments:
        return text

    content: list = []
    for att in attachments:
        local_path = UPLOADS_ROOT / att.get("filename", "")
        mime = att.get("mime_type", "")
        name = att.get("display_name", att.get("filename", "file"))

        if mime in SUPPORTED_IMAGE_MIMES and local_path.exists():
            try:
                data = base64.standard_b64encode(local_path.read_bytes()).decode()
                content.append({
                    "type": "image",
                    "source": {"type": "base64", "media_type": mime, "data": data},
                })
            except Exception as exc:
                logger.warning("Failed to encode image %s: %s", local_path, exc)
                content.append({"type": "text", "text": f"[Image attachment unavailable: {name}]"})

        elif local_path.exists() and local_path.suffix.lower() in BINARY_DOC_SUFFIXES:
            suffix = local_path.suffix.lower()
            try:
                if suffix == ".pdf":
                    import pdfplumber
                    with pdfplumber.open(str(local_path)) as pdf:
                        extracted = "\n".join(
                            page.extract_text() or "" for page in pdf.pages
                        )
                elif suffix in (".docx", ".doc"):
                    import docx as _docx
                    doc = _docx.Document(str(local_path))
                    extracted = "\n".join(p.text for p in doc.paragraphs)
                else:
                    extracted = ""
                content.append({
                    "type": "text",
                    "text": f"[Attached document: {name}]\n{extracted[:MAX_TEXT_CHARS]}",
                })
            except Exception as exc:
                logger.warning("Failed to extract document %s: %s", local_path, exc)
                content.append({
                    "type": "text",
                    "text": f"[Document attachment could not be read: {name}] Error: {exc}",
                })

        elif local_path.exists():
            try:
                file_text = local_path.read_text(encoding="utf-8", errors="replace")[:MAX_TEXT_CHARS]
                content.append({"type": "text", "text": f"[Attached file: {name}]\n{file_text}"})
            except Exception as exc:
                logger.warning("Failed to read file %s: %s", local_path, exc)
                content.append({"type": "text", "text": f"[File attachment unavailable: {name}]"})

        else:
            content.append({"type": "text", "text": f"[Attachment not found: {name}]"})

    if text:
        content.append({"type": "text", "text": text})

    return content if content else text


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
async def stream_chat(request: Request):
    """SSE streaming chat endpoint — accepts both JSON and multipart/form-data.

    Streams text_delta events while Anthropic generates the response, then
    persists the conversation, extracts memories in the background, and emits
    a final done event.
    """
    content_type = request.headers.get("content-type", "")
    attachments: list = []

    if "multipart/form-data" in content_type:
        form = await request.form()
        raw_message = form.get("message", "") or ""
        session_id_raw = form.get("session_id")
        session_id = (
            str(session_id_raw)
            if session_id_raw
            else datetime.now().strftime("%Y%m%d-%H%M%S-") + uuid.uuid4().hex[:6]
        )
        uploaded: list[UploadFile] = [
            v for v in form.getlist("files") if isinstance(v, UploadFile)
        ]
        if uploaded:
            attachments = await _save_uploaded_files(uploaded)
    else:
        body = await request.json()
        raw_message = body.get("message", "") or ""
        session_id_raw = body.get("session_id")
        session_id = (
            str(session_id_raw)
            if session_id_raw
            else datetime.now().strftime("%Y%m%d-%H%M%S-") + uuid.uuid4().hex[:6]
        )

    user_message = str(raw_message).strip()

    if not user_message and not attachments:
        raise HTTPException(status_code=422, detail="message must not be empty")

    async def generate():
        conn = _get_db()
        try:
            # --- emit session meta immediately ---
            yield _sse("meta", session_id=session_id)

            # --- load conversation history (clean messages only) ---
            history = _load_history(conn, session_id)

            # --- build tiered context ---
            yield _sse("status", text="Loading context...")
            system_prompt, additional_context, _museum_id = _assemble_context(user_message)

            if additional_context:
                augmented_text = (
                    f"{user_message}\n\n---\n"
                    "[Context — do not repeat this to the user, use it to inform your response]\n"
                    f"{additional_context}"
                )
            else:
                augmented_text = user_message

            # Build the user content — plain string or multimodal list with attachments
            user_content = _build_user_content(augmented_text, attachments if attachments else None)

            # Build messages: history uses clean messages; current turn uses augmented
            messages = list(history)
            messages.append({"role": "user", "content": user_content})

            # --- stream from Anthropic (with tool-use agentic loop) ---
            client = _get_client()
            model, max_tokens, temperature = _chat_model_cfg()

            from tools.api.tool_registry import ALL_TOOLS, handle_tool_call

            # messages_for_api grows when tool rounds add assistant + tool_result turns
            messages_for_api = list(messages)
            full_response = ""
            max_tool_rounds = 15  # allow multi-step research tasks

            try:
                for _round in range(max_tool_rounds):
                    accumulated_text = ""
                    final_message = None

                    with client.messages.stream(
                        model=model,
                        max_tokens=max_tokens,
                        temperature=temperature,
                        system=system_prompt,
                        messages=messages_for_api,
                        tools=ALL_TOOLS,
                    ) as stream:
                        for event in stream:
                            if event.type == "content_block_start":
                                if event.content_block.type == "tool_use":
                                    tool_name = event.content_block.name
                                    yield _sse("status", text=f"Using {tool_name}...")
                            elif event.type == "content_block_delta":
                                if event.delta.type == "text_delta":
                                    accumulated_text += event.delta.text
                                    yield _sse("text_delta", text=event.delta.text)
                                # input_json_delta: tool input building — no streaming needed

                        # get_final_message() must be called inside the `with` block
                        final_message = stream.get_final_message()

                    full_response += accumulated_text

                    # Check for tool_use blocks in the final message
                    tool_use_blocks = [
                        b for b in final_message.content if b.type == "tool_use"
                    ]

                    if not tool_use_blocks:
                        # No tools called — streaming complete
                        break

                    # Execute each tool and build the tool_results message
                    # Append the assistant turn (with tool_use blocks) to the conversation
                    messages_for_api.append(
                        {"role": "assistant", "content": final_message.content}
                    )

                    tool_results = []
                    for tool_block in tool_use_blocks:
                        logger.info(
                            "Tool call: %s input=%s", tool_block.name, tool_block.input
                        )
                        result_text = handle_tool_call(tool_block.name, tool_block.input)
                        logger.info(
                            "Tool result: %s → %d chars", tool_block.name, len(result_text)
                        )
                        tool_results.append(
                            {
                                "type": "tool_result",
                                "tool_use_id": tool_block.id,
                                "content": result_text,
                            }
                        )

                    messages_for_api.append({"role": "user", "content": tool_results})
                    # Loop continues — next iteration streams the response with tool results

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
                    "session_id": row["session_id"],
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


@router.patch("/sessions")
async def rename_session(request: Request):
    """Rename (or set title for) a session."""
    body = await request.json()
    session_id = body.get("session_id")
    title = body.get("title", "").strip()
    if not session_id:
        raise HTTPException(status_code=422, detail="session_id is required")
    if not title:
        raise HTTPException(status_code=422, detail="title must not be empty")
    conn = _get_db()
    try:
        conn.execute(
            """
            INSERT INTO session_titles (session_id, title)
            VALUES (?, ?)
            ON CONFLICT(session_id) DO UPDATE SET title = excluded.title
            """,
            (session_id, title),
        )
        conn.commit()
        return {"renamed": True, "session_id": session_id, "title": title}
    finally:
        conn.close()


@router.delete("/memory/{memory_id}")
async def delete_memory_endpoint(memory_id: int):
    """Delete a memory by ID from memory.db."""
    from tools.memory.memory_db import delete_memory
    result = delete_memory(memory_id)
    return result


@router.patch("/memory/{memory_id}")
async def update_memory_endpoint(memory_id: int, request: Request):
    """Update a memory's content, type, importance, or museum_id."""
    body = await request.json()

    allowed_fields = {"content", "type", "importance", "museum_id"}
    updates = {k: v for k, v in body.items() if k in allowed_fields}
    if not updates:
        raise HTTPException(status_code=422, detail="No valid fields to update")

    from tools.memory.memory_db import init_db
    conn = init_db()
    try:
        set_clauses = ", ".join(f"{k} = ?" for k in updates)
        values = list(updates.values())
        values.append(memory_id)
        conn.execute(
            f"UPDATE memories SET {set_clauses}, updated_at = datetime('now') WHERE id = ?",
            values,
        )
        conn.commit()
        row = conn.execute(
            "SELECT id, content, type, importance, museum_id, tags, source, created_at, updated_at FROM memories WHERE id = ?",
            (memory_id,),
        ).fetchone()
        if row is None:
            raise HTTPException(status_code=404, detail=f"Memory {memory_id} not found")
        cols = ["id", "content", "type", "importance", "museum_id", "tags", "source", "created_at", "updated_at"]
        return dict(zip(cols, row))
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


# ---------------------------------------------------------------------------
# Transcription endpoint
# ---------------------------------------------------------------------------


@router.post("/transcribe")
async def transcribe_audio(request: Request):
    """Transcribe audio via OpenAI STT API."""
    from fastapi.responses import JSONResponse

    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        # Try loading from .env in case the server started without it
        try:
            from dotenv import load_dotenv
            load_dotenv(PROJECT_ROOT / ".env")
            api_key = os.environ.get("OPENAI_API_KEY")
        except ImportError:
            pass
    if not api_key:
        return JSONResponse({"error": "OPENAI_API_KEY not configured"}, status_code=503)

    form = await request.form()
    audio_file = form.get("audio")
    if not audio_file:
        return JSONResponse({"error": "No audio file provided"}, status_code=400)

    # Read stt_model from settings
    model = "gpt-4o-mini-transcribe"
    try:
        settings = _get_settings()
        model = settings.get("voice", {}).get("stt_model", model)
    except Exception:
        pass

    audio_bytes = await audio_file.read()
    filename = getattr(audio_file, "filename", None) or "recording.webm"
    content_type = getattr(audio_file, "content_type", None) or "audio/webm"

    # Build multipart form data for OpenAI
    import urllib.request as _urllib_request
    import json as _json

    boundary = "----TouriBotAudioBoundary"
    body = b""
    body += f"--{boundary}\r\n".encode()
    body += f'Content-Disposition: form-data; name="file"; filename="{filename}"\r\n'.encode()
    body += f"Content-Type: {content_type}\r\n\r\n".encode()
    body += audio_bytes
    body += f"\r\n--{boundary}\r\n".encode()
    body += f'Content-Disposition: form-data; name="model"\r\n\r\n{model}'.encode()
    body += f"\r\n--{boundary}--\r\n".encode()

    req = _urllib_request.Request(
        "https://api.openai.com/v1/audio/transcriptions",
        data=body,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": f"multipart/form-data; boundary={boundary}",
        },
    )

    try:
        with _urllib_request.urlopen(req, timeout=30) as resp:
            result = _json.loads(resp.read())
        return JSONResponse({"text": result.get("text", ""), "model": model})
    except Exception as exc:
        return JSONResponse({"error": f"Transcription failed: {str(exc)}"}, status_code=500)


# ---------------------------------------------------------------------------
# Research endpoints
# ---------------------------------------------------------------------------

RESEARCH_DB_PATH = PROJECT_ROOT / "data" / "research.db"


def _get_research_db() -> sqlite3.Connection:
    """Open research.db (creating schema if needed) and return connection."""
    from tools.research.research_state import _get_db as _get_research_state_db
    return _get_research_state_db(RESEARCH_DB_PATH)


@router.post("/research")
async def start_research(request: Request):
    """Start a deep research session in a background thread.

    Body: {"query": "...", "depth": "standard", "museum_id": null}
    Returns: {"session_id": "...", "status": "started"}
    """
    body = await request.json()
    query = body.get("query", "").strip()
    depth = body.get("depth", "standard")
    museum_id = body.get("museum_id")  # optional int — links research to a museum lead

    if not query:
        raise HTTPException(status_code=422, detail="query must not be empty")
    if depth not in ("quick", "standard", "deep", "exhaustive"):
        raise HTTPException(status_code=422, detail="depth must be quick, standard, deep, or exhaustive")

    # Generate session_id upfront so we can return it immediately
    research_session_id = datetime.now().strftime("%Y%m%d-%H%M%S-") + uuid.uuid4().hex[:6]

    import subprocess
    import sys

    log_dir = PROJECT_ROOT / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)

    subprocess.Popen(
        [
            sys.executable, "-m", "tools.research.research_runner",
            "--query", query,
            "--depth", depth,
            "--session-id", research_session_id,
            "--museum-id", str(museum_id) if museum_id else "",
        ],
        cwd=str(PROJECT_ROOT),
        start_new_session=True,
        stdout=open(log_dir / "research.log", "a"),
        stderr=subprocess.STDOUT,
    )

    return {"session_id": research_session_id, "status": "started", "query": query, "depth": depth}


@router.get("/research")
def list_research_sessions(limit: int = Query(20, ge=1, le=100)):
    """Return recent research sessions (all phases)."""
    if not RESEARCH_DB_PATH.exists():
        return {"sessions": []}
    conn = _get_research_db()
    try:
        rows = conn.execute(
            """SELECT session_id, phase, query, depth, started_at, updated_at
               FROM research_sessions
               ORDER BY updated_at DESC
               LIMIT ?""",
            (limit,),
        ).fetchall()
        return {
            "sessions": [
                {
                    "session_id": r[0],
                    "phase": r[1],
                    "query": r[2],
                    "depth": r[3],
                    "started_at": r[4],
                    "updated_at": r[5],
                }
                for r in rows
            ]
        }
    finally:
        conn.close()


@router.get("/research/{session_id}")
def get_research_status(session_id: str):
    """Return current phase and progress for a research session."""
    if not RESEARCH_DB_PATH.exists():
        raise HTTPException(status_code=404, detail="No research sessions found")
    conn = _get_research_db()
    try:
        row = conn.execute(
            "SELECT phase, query, depth, state_json, started_at, updated_at "
            "FROM research_sessions WHERE session_id = ?",
            (session_id,),
        ).fetchone()
        if row is None:
            raise HTTPException(status_code=404, detail=f"Session {session_id} not found")

        phase, query, depth, state_json, started_at, updated_at = row

        # Parse minimal progress counters from state_json without loading full state
        try:
            import json as _json
            s = _json.loads(state_json)
            progress = {
                "search_calls": s.get("search_calls", 0),
                "page_reads": s.get("page_reads", 0),
                "llm_calls": s.get("llm_calls", 0),
                "total_cost_usd": s.get("total_cost_usd", 0.0),
                "excerpts_collected": len(s.get("excerpts", [])),
                "error_message": s.get("error_message", ""),
                "output_path": s.get("output_path", ""),
            }
        except Exception:
            progress = {}

        return {
            "session_id": session_id,
            "phase": phase,
            "query": query,
            "depth": depth,
            "started_at": started_at,
            "updated_at": updated_at,
            "progress": progress,
        }
    finally:
        conn.close()


@router.get("/research/{session_id}/report")
def get_research_report(session_id: str):
    """Return the final markdown report for a completed research session."""
    if not RESEARCH_DB_PATH.exists():
        raise HTTPException(status_code=404, detail="No research sessions found")
    conn = _get_research_db()
    try:
        row = conn.execute(
            "SELECT phase, state_json FROM research_sessions WHERE session_id = ?",
            (session_id,),
        ).fetchone()
        if row is None:
            raise HTTPException(status_code=404, detail=f"Session {session_id} not found")

        phase, state_json = row
        if phase not in ("done", "synthesis"):
            return {"session_id": session_id, "phase": phase, "report": None,
                    "message": f"Research still in progress (phase: {phase})"}

        # Try to read the report from disk (preferred — no size limit)
        try:
            import json as _json
            s = _json.loads(state_json)
            output_path = s.get("output_path", "")
            if output_path and Path(output_path).exists():
                report_text = Path(output_path).read_text()
                return {"session_id": session_id, "phase": phase, "report": report_text,
                        "output_path": output_path}
        except Exception:
            pass

        # Fallback: return from state_json (may be truncated for very large reports)
        try:
            import json as _json
            s = _json.loads(state_json)
            report_text = s.get("final_report", "")
            if report_text:
                return {"session_id": session_id, "phase": phase, "report": report_text}
        except Exception:
            pass

        raise HTTPException(status_code=404, detail="Report not yet available")
    finally:
        conn.close()
