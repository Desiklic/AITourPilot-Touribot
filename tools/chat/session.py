"""Chat session: context assembly, Anthropic API call, memory extraction, conversation log."""

import json
import logging
import os
import sqlite3
import uuid
from datetime import datetime
from pathlib import Path

import anthropic
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel

logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).parent.parent.parent
SOUL_MD = PROJECT_ROOT / "soul.md"
USER_MD = PROJECT_ROOT / "memory" / "USER.md"
MEMORY_MD = PROJECT_ROOT / "memory" / "MEMORY.md"
LOGS_DIR = PROJECT_ROOT / "memory" / "logs"
HARDPROMPTS_DIR = PROJECT_ROOT / "hardprompts"
KNOWLEDGE_DIR = PROJECT_ROOT / "knowledge" / "processed"

console = Console()


def _load_settings() -> dict:
    """Load settings from args/settings.yaml."""
    try:
        import yaml
        settings_path = PROJECT_ROOT / "args" / "settings.yaml"
        with open(settings_path) as f:
            return yaml.safe_load(f) or {}
    except Exception:
        return {}


def _load_file(path: Path) -> str:
    """Read a file, return empty string if missing."""
    if path.exists():
        return path.read_text()
    return ""


# ── Token budget helper ───────────────────────────────────────────────────────


def _count_tokens(text: str) -> int:
    """Approximate token count (chars/4)."""
    return len(text) // 4


def _truncate_to_budget(text: str, max_tokens: int) -> str:
    """Truncate text to approximately max_tokens tokens."""
    max_chars = max_tokens * 4
    if len(text) <= max_chars:
        return text
    return text[:max_chars] + "\n\n[... truncated to fit context budget ...]"


# ── Museum detection ──────────────────────────────────────────────────────────


def _detect_museum(message: str) -> dict | None:
    """Fuzzy-match user message against leads.db museum names.

    Returns the museum dict (id, name, city, country, stage, score) or None.
    Does NOT match on generic words like 'museum' alone.
    """
    try:
        from tools.leads.lead_db import list_museums
        museums = list_museums()
        msg_lower = message.lower()

        for museum in museums:
            name = museum["name"].lower()

            # Full name match — highest confidence
            if name in msg_lower:
                return museum

            # Significant-word match: skip short/common words, require all significant
            # words to appear in the message.  Also require at least 2 words to avoid
            # single-word matches like "museum" / "park" / "art".
            words = [w for w in name.split() if len(w) > 3 and w not in {
                "museum", "museums", "national", "natural", "history",
                "modern", "contemporary", "science", "technology", "arts",
                "royal", "city", "state", "great", "park",
            }]
            if len(words) >= 2 and all(w in msg_lower for w in words):
                return museum

        return None
    except Exception:
        return None


# ── Pipeline summary helper ───────────────────────────────────────────────────


def _get_pipeline_summary() -> str:
    """Get a brief pipeline summary for the system prompt."""
    try:
        from tools.leads.pipeline import pipeline_summary_text
        return pipeline_summary_text()
    except Exception:
        return ""


# ── Tier 1: Always-loaded core context ───────────────────────────────────────


def _build_tier1_context() -> str:
    """Assemble the always-loaded Tier 1 system prompt (~4K tokens max).

    Includes:
    - soul.md (identity + principles)
    - USER.md (Hermann's identity)
    - business_context.md (product/pricing/competition)
    - Pipeline summary (one-liner)
    - Top 5 global memories by importance (strategy/general, importance >= 7)
    - Current date
    """
    settings = _load_settings()
    budget = settings.get("session", {}).get("context_budget", {})
    tier1_max = budget.get("tier1_max_tokens", 4000)

    parts = []

    soul = _load_file(SOUL_MD)
    if soul:
        parts.append(soul)

    user = _load_file(USER_MD)
    if user:
        parts.append(f"\n---\n\n{user}")

    # Business context (always relevant — product/pricing/competition)
    biz = _load_file(HARDPROMPTS_DIR / "business_context.md")
    if biz:
        parts.append(f"\n---\n\n{biz}")

    # Pipeline summary — compressed one-liner
    pipeline_summary = _get_pipeline_summary()
    if pipeline_summary:
        parts.append(f"\n---\n\n## Current Pipeline State\n\n{pipeline_summary}")

    # Top 5 global strategic memories by importance
    top_memories = _get_top_global_memories(limit=5, min_importance=7)
    if top_memories:
        lines = ["## Key Strategic Memories\n"]
        for m in top_memories:
            lines.append(f"- [importance:{m['importance']}] {m['content']}")
        parts.append(f"\n---\n\n" + "\n".join(lines))

    parts.append(f"\n---\n\nCurrent date: {datetime.now().strftime('%Y-%m-%d %H:%M')}")

    result = "\n".join(parts)
    return _truncate_to_budget(result, tier1_max)


def _get_top_global_memories(limit: int = 5, min_importance: int = 7) -> list[dict]:
    """Fetch top memories by importance from memory.db (global/strategy, no museum filter)."""
    try:
        from tools.memory.memory_db import init_db
        conn = init_db()
        rows = conn.execute(
            """SELECT id, content, type, importance, created_at
               FROM memories
               WHERE importance >= ?
                 AND (museum_id IS NULL OR type IN ('strategy', 'general'))
               ORDER BY importance DESC, created_at DESC
               LIMIT ?""",
            (min_importance, limit),
        ).fetchall()
        conn.close()
        return [
            {"id": r[0], "content": r[1], "type": r[2], "importance": r[3], "created_at": r[4]}
            for r in rows
        ]
    except Exception:
        return []


# ── Tier 2: Museum-specific context ──────────────────────────────────────────


def _build_tier2_context(museum_id: int, museum_name: str) -> str:
    """Assemble museum-specific Tier 2 context (~4K tokens max).

    Includes:
    - Museum record (name, city, country, stage, tier, score, notes)
    - Contact records for that museum
    - Museum-specific memories (hybrid_search filtered by museum_id, limit=10)
    - Last 3 interactions summary
    - Research brief headline (if research exists)
    """
    settings = _load_settings()
    budget = settings.get("session", {}).get("context_budget", {})
    tier2_max = budget.get("tier2_max_tokens", 4000)

    parts = []

    # Museum record
    try:
        from tools.leads.lead_db import get_museum_by_id, get_contacts, get_interaction_history

        museum = get_museum_by_id(museum_id)
        if museum:
            stage_names = {
                0: "Identified", 1: "Researched", 2: "Personalized",
                3: "Outreach Sent", 4: "In Sequence", 5: "Responded",
                6: "Demo Scheduled", 7: "Demo Completed",
                8: "Proposal Sent", 9: "Negotiating", 10: "Closed",
            }
            stage_label = stage_names.get(museum.get("stage", 0), "Unknown")
            lines = [f"## Museum: {museum['name']}"]
            if museum.get("city"):
                lines.append(f"Location: {museum['city']}, {museum.get('country', '')}")
            lines.append(f"Stage: {museum.get('stage', 0)} — {stage_label}")
            if museum.get("tier"):
                lines.append(f"Tier: {museum['tier']}")
            if museum.get("score") is not None:
                lines.append(f"Score: {museum['score']}")
            if museum.get("notes"):
                lines.append(f"Notes: {museum['notes']}")
            parts.append("\n".join(lines))

        # Contacts
        contacts = get_contacts(museum_id)
        if contacts:
            c_lines = ["## Contacts"]
            for c in contacts:
                primary = " (primary)" if c.get("is_primary") else ""
                role = f" — {c['role']}" if c.get("role") else ""
                email = f" <{c['email']}>" if c.get("email") else ""
                c_lines.append(f"- {c['full_name']}{role}{email}{primary}")
            parts.append("\n".join(c_lines))

        # Last 3 interactions summary
        interactions = get_interaction_history(museum_id)
        if interactions:
            recent = interactions[-3:]  # last 3
            i_lines = ["## Recent Interactions (last 3)"]
            for ix in recent:
                direction = ix.get("direction", "?")
                channel = ix.get("channel", "?")
                date = (ix.get("created_at") or "")[:10]
                subject = ix.get("subject") or ""
                body_snippet = (ix.get("body") or "")[:120]
                event = f" [{ix['event_type']}]" if ix.get("event_type") else ""
                i_lines.append(
                    f"- {date} | {direction}/{channel}{event}"
                    + (f" | {subject}" if subject else "")
                    + (f"\n  {body_snippet}" if body_snippet else "")
                )
            parts.append("\n".join(i_lines))

    except Exception as e:
        logger.debug(f"Tier 2 museum data load failed: {e}")

    # Museum-specific memories
    try:
        from tools.memory.memory_db import hybrid_search
        mem_results = hybrid_search(museum_name, limit=10, include_sessions=False, museum_id=museum_id)
        if mem_results:
            m_lines = ["## Museum-Specific Memories"]
            for r in mem_results:
                if r.get("score", 0) < 0.003:
                    continue
                content = (r.get("content") or "")[:250]
                m_lines.append(f"- {content}")
            if len(m_lines) > 1:
                parts.append("\n".join(m_lines))
    except Exception as e:
        logger.debug(f"Tier 2 memory search failed: {e}")

    # Research brief headline
    try:
        from tools.leads.lead_db import init_db as leads_init_db
        conn = leads_init_db()
        row = conn.execute(
            "SELECT hook_line, hypothesis FROM research WHERE museum_id = ? AND is_current = 1 LIMIT 1",
            (museum_id,),
        ).fetchone()
        conn.close()
        if row and (row[0] or row[1]):
            hook = row[0] or ""
            hyp = row[1] or ""
            r_lines = ["## Research Brief Headline"]
            if hook:
                r_lines.append(f"Hook: {hook}")
            if hyp:
                r_lines.append(f"Hypothesis: {hyp}")
            parts.append("\n".join(r_lines))
    except Exception as e:
        logger.debug(f"Tier 2 research brief load failed: {e}")

    if not parts:
        return ""

    result = "\n---\n\n## Museum Context\n\n" + "\n\n---\n\n".join(parts)
    return _truncate_to_budget(result, tier2_max)


# ── Marketing context loader ──────────────────────────────────────────────────


def _load_marketing_context(max_files: int = 5, max_chars_per_file: int = 3000) -> list[str]:
    """Load relevant marketing files from knowledge/processed/.

    Finds all processed files produced from the Marketing Materials source
    (prefixed with 'marketing_materials__') and loads the most relevant ones.
    Returns a list of markdown strings, capped to avoid blowing the token budget.
    """
    try:
        if not KNOWLEDGE_DIR.exists():
            return []

        marketing_files = sorted(KNOWLEDGE_DIR.glob("marketing_materials__*.md"))
        if not marketing_files:
            return []

        parts = []
        files_to_load = marketing_files[:max_files]

        header_lines = [f"## Marketing Materials ({len(marketing_files)} files available, loading top {len(files_to_load)})"]
        parts.append("\n".join(header_lines))

        for f in files_to_load:
            content = _load_file(f)
            if content:
                # Truncate per-file to keep total size manageable
                if len(content) > max_chars_per_file:
                    content = content[:max_chars_per_file] + "\n\n[... truncated ...]"
                parts.append(content)

        return parts
    except Exception as e:
        logger.debug(f"Marketing context load failed: {e}")
        return []


# ── Tier 3: Task-specific full context ───────────────────────────────────────


def _build_tier3_context(museum_id: int | None, task_types: set[str]) -> str:
    """Assemble task-specific Tier 3 context (~8K tokens max).

    Includes:
    - Email templates (when 'drafting' in task_types)
    - Full research document from disk (when museum has research)
    - Detailed interaction history (when drafting follow-ups)
    - Objection handling (when 'scoring' in task_types)
    - Pipeline guide (when 'pipeline' in task_types)
    - Museum procurement knowledge (when 'research' in task_types)
    - Personalizer brief (when 'drafting' + museum detected)
    """
    settings = _load_settings()
    budget = settings.get("session", {}).get("context_budget", {})
    tier3_max = budget.get("tier3_max_tokens", 8000)

    parts = []

    if "drafting" in task_types:
        templates = _load_file(HARDPROMPTS_DIR / "email_templates.md")
        if templates:
            parts.append(templates)

        # Personalizer brief when museum is known
        if museum_id is not None:
            try:
                from tools.leads.lead_db import get_museum_by_id, get_contacts
                museum = get_museum_by_id(museum_id)
                if museum:
                    from tools.outreach.personalizer import build_context, format_brief
                    contacts = get_contacts(museum_id)
                    contact_name = contacts[0]["full_name"] if contacts else ""
                    ctx = build_context(museum["name"], contact_name)
                    brief = format_brief(ctx)
                    if brief:
                        parts.append(brief)
            except Exception as e:
                logger.debug(f"Tier 3 personalizer brief failed: {e}")

        # Full research document from disk when museum is known
        if museum_id is not None:
            try:
                from tools.leads.lead_db import init_db as leads_init_db
                conn = leads_init_db()
                row = conn.execute(
                    "SELECT insights FROM research WHERE museum_id = ? AND is_current = 1 LIMIT 1",
                    (museum_id,),
                ).fetchone()
                conn.close()
                if row and row[0]:
                    parts.append(f"## Full Research Insights\n\n{row[0]}")
            except Exception as e:
                logger.debug(f"Tier 3 research insights load failed: {e}")

    if "scoring" in task_types:
        objections = _load_file(HARDPROMPTS_DIR / "objection_handling.md")
        if objections:
            parts.append(objections)

    if "pipeline" in task_types:
        pipeline = _load_file(HARDPROMPTS_DIR / "pipeline_guide.md")
        if pipeline:
            parts.append(pipeline)

    if "research" in task_types:
        procurement = _load_file(KNOWLEDGE_DIR / "museum_procurement.md")
        if procurement:
            parts.append(procurement)

    if "marketing" in task_types:
        marketing_parts = _load_marketing_context()
        if marketing_parts:
            parts.extend(marketing_parts)

    if not parts:
        return ""

    result = "\n---\n\n## Loaded Knowledge\n\n" + "\n\n---\n\n".join(parts)
    return _truncate_to_budget(result, tier3_max)


# ── Memory context ────────────────────────────────────────────────────────────


def _search_memory_context(user_message: str, museum_id: int = None) -> str:
    """Search memory DB for context relevant to the user's message."""
    try:
        from tools.memory.memory_db import hybrid_search
        results = hybrid_search(user_message, limit=5, include_sessions=True, museum_id=museum_id)
        if not results:
            return ""

        lines = ["## Relevant Memories\n"]
        for r in results:
            score = r.get("score", 0.0)
            if score < 0.005:  # RRF scores are ~0.001-0.03; filter only near-zero results
                continue
            source = r.get("source", "memory")
            content = r.get("content", "")[:300]
            lines.append(f"- [{source}] {content}")

        if len(lines) > 1:
            return "\n".join(lines)
    except Exception as e:
        logger.debug(f"Memory search failed: {e}")

    return ""


# ── Context orchestrator ──────────────────────────────────────────────────────


def _assemble_context(user_message: str) -> tuple[str, str, int | None]:
    """Assemble tiered context based on the user's message.

    Returns:
        (system_prompt, additional_context, museum_id)
        - system_prompt: Tier 1 (always-loaded)
        - additional_context: Tier 2 + Tier 3 + memory search (appended to user message)
        - museum_id: int if a museum was detected, else None
    """
    settings = _load_settings()
    budget = settings.get("session", {}).get("context_budget", {})
    total_max = budget.get("total_max_tokens", 16000)

    # Tier 1 — always loaded
    system_prompt = _build_tier1_context()

    # Detect museum
    museum = _detect_museum(user_message)
    museum_id = museum["id"] if museum else None

    # Loading indicator for CLI
    if museum:
        console.print(f"  [dim]Loading context for {museum['name']}...[/dim]")

    # Tier 2 — museum-specific
    tier2_context = ""
    if museum:
        tier2_context = _build_tier2_context(museum_id, museum["name"])

    # Tier 3 — task-specific
    task_types = _detect_task_type(user_message)
    tier3_context = ""
    if task_types:
        if museum:
            console.print(f"  [dim]Loading {', '.join(sorted(task_types))} resources...[/dim]")
        tier3_context = _build_tier3_context(museum_id, task_types)

    # Memory search (museum-aware)
    memory_context = _search_memory_context(user_message, museum_id=museum_id)

    # Combine additional context parts
    additional_parts = [p for p in [tier2_context, tier3_context, memory_context] if p]
    additional_context = "\n\n".join(additional_parts)

    # Token budget check on additional context
    tier1_tokens = _count_tokens(system_prompt)
    additional_tokens = _count_tokens(additional_context)
    remaining_budget = total_max - tier1_tokens
    if additional_tokens > remaining_budget and remaining_budget > 0:
        additional_context = _truncate_to_budget(additional_context, remaining_budget)

    return system_prompt, additional_context, museum_id


# ── Backward-compatible system prompt builder ─────────────────────────────────


def _build_system_prompt() -> str:
    """Assemble the system prompt. Delegates to _build_tier1_context() for backward compatibility."""
    return _build_tier1_context()


# ── Task type detection ───────────────────────────────────────────────────────


def _detect_task_type(user_message: str) -> set[str]:
    """Detect what kind of task the user is requesting to load relevant knowledge."""
    msg = user_message.lower()
    types = set()

    # Drafting emails
    draft_kw = ["draft", "email", "write", "outreach", "message", "follow-up",
                 "reactivation", "sequence", "template"]
    if any(kw in msg for kw in draft_kw):
        types.add("drafting")

    # Marketing / campaign strategy
    marketing_kw = ["marketing", "campaign", "linkedin", "newsletter", "automation",
                    "content", "social", "advertising", "brand", "branding",
                    "outreach strategy", "deck", "linkedin post"]
    if any(kw in msg for kw in marketing_kw):
        types.add("marketing")

    # Scoring responses / handling objections
    score_kw = ["score", "response", "reply", "replied", "objection", "decline",
                 "interested", "not now", "bad timing", "meeting"]
    if any(kw in msg for kw in score_kw):
        types.add("scoring")

    # Pipeline / stage management
    pipe_kw = ["pipeline", "stage", "stale", "status", "next action", "tier"]
    if any(kw in msg for kw in pipe_kw):
        types.add("pipeline")

    # Museum research / product questions
    research_kw = ["competitor", "smartify", "gesso", "cuseum", "pricing",
                    "pilot", "eur", "enterprise", "visitor", "procurement"]
    if any(kw in msg for kw in research_kw):
        types.add("research")

    return types


# ── On-demand knowledge loader (kept for backward compatibility) ──────────────


def _load_knowledge_for_task(task_types: set[str], user_message: str = "") -> str:
    """Load on-demand knowledge files based on detected task type.

    Note: In the tiered context system, this is superseded by _build_tier3_context().
    Kept for backward compatibility with any external callers.
    """
    return _build_tier3_context(museum_id=None, task_types=task_types)


# ── Draft target extraction ───────────────────────────────────────────────────


def _extract_draft_target(message: str) -> dict | None:
    """Try to extract museum and contact names from a drafting request.

    Uses _detect_museum() for dynamic museum detection from leads.db,
    falling back to regex patterns for contact names.
    """
    import re
    msg = message.lower()

    # Dynamic museum detection from leads.db
    museum_record = _detect_museum(message)
    museum = museum_record["name"] if museum_record else None

    # Known contacts (static — contacts are not in a separate queryable index yet)
    known_contacts = {
        "georgie power": "Georgie Power",
        "georgie": "Georgie Power",
        "lisa witschnig": "Lisa Witschnig",
        "lisa": "Lisa Witschnig",
        "nils van keulen": "Nils van Keulen",
        "nils": "Nils van Keulen",
        "sebastien mathivet": "Sebastien Mathivet",
        "sebastien": "Sebastien Mathivet",
        "treglia": "Treglia-Detraz",
    }

    contact = None
    for key, val in known_contacts.items():
        if key in msg:
            contact = val
            break

    # Try "for X at Y" pattern when no museum detected
    if not museum:
        m = re.search(r'(?:for|to)\s+\w+\s+(?:\w+\s+)?at\s+(.+?)(?:\.|,|$)', msg)
        if m:
            museum = m.group(1).strip().title()

    if museum:
        return {"museum": museum, "contact": contact or ""}
    return None


# ── Memory extraction ─────────────────────────────────────────────────────────

EXTRACTION_PROMPT = """Analyze this conversation exchange between Hermann (founder of AITourPilot, \
a conversational AI audioguide for museums) and his outreach assistant Touri.

Extract facts worth remembering for future outreach sessions. Focus on:
- Contact intelligence: names, roles, preferences, communication styles, response patterns
- Museum intelligence: visitor numbers, current tech stack, budget status, decision-maker structure
- Interactions: emails sent/received, meetings held, demos given, responses and their scores
- Strategy: what outreach angles work, timing insights, template performance, campaign learnings

Rules:
- Each memory must be self-contained (understandable without the conversation context)
- Do NOT save vague summaries like "Discussed Joanneum outreach" -- save the SPECIFIC fact
- Do NOT save what Touri said she would do -- only save what was actually decided or learned
- Include the museum name when the memory relates to a specific museum
- Set importance 8-10 only for permanent facts; use 5-6 for routine interactions

If this exchange is trivial (greetings, thanks, small talk, questions about Touri itself), \
set worth_saving to false and return an empty memories array."""

EXTRACTION_SCHEMA = {
    "type": "object",
    "properties": {
        "worth_saving": {
            "type": "boolean",
            "description": "True if this exchange contains information worth remembering"
        },
        "memories": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "content": {"type": "string", "description": "The fact to remember, concise and self-contained"},
                    "type": {"type": "string", "enum": ["contact_intel", "museum_intel", "interaction", "strategy", "general"]},
                    "importance": {"type": "integer", "minimum": 1, "maximum": 10},
                    "museum_name": {"type": "string", "description": "Museum name if applicable, else null"},
                    "tags": {"type": "array", "items": {"type": "string"}, "description": "Optional tags"}
                },
                "required": ["content", "type", "importance"]
            }
        }
    },
    "required": ["worth_saving", "memories"]
}


def _extract_and_save_memories(user_message: str, assistant_response: str, client: anthropic.Anthropic, settings: dict):
    """Extract structured memories using Sonnet with JSON schema output."""
    try:
        model = _load_settings().get("models", {}).get("memory_extraction", {}).get("model", "claude-sonnet-4-6")
        max_tokens = _load_settings().get("models", {}).get("memory_extraction", {}).get("max_tokens", 1024)

        # Truncate response to keep extraction prompt manageable
        response_truncated = assistant_response[:1500]

        extraction_message = f"""User said: {user_message}

Assistant responded: {response_truncated}

Analyze this exchange and extract any facts worth remembering. Return your answer as JSON matching this exact schema:
{json.dumps(EXTRACTION_SCHEMA, indent=2)}"""

        response = client.messages.create(
            model=model,
            max_tokens=max_tokens,
            temperature=0.2,
            messages=[{"role": "user", "content": extraction_message}],
            system=EXTRACTION_PROMPT,
        )

        # Parse JSON response
        text = response.content[0].text.strip()
        # Handle potential markdown code fences
        if text.startswith("```"):
            text = text.split("\n", 1)[1].rsplit("```", 1)[0].strip()

        try:
            data = json.loads(text)
        except json.JSONDecodeError as je:
            logger.debug(f"Memory extraction JSON parse failed: {je} | raw: {text[:200]}")
            return

        if not data.get("worth_saving", False):
            return  # Gate: trivial exchange, skip saving

        from tools.memory.memory_db import _resolve_museum_id
        from tools.memory.memory_write import write_memory

        for mem in data.get("memories", []):
            content = mem.get("content", "").strip()
            if not content or len(content) < 10:
                continue

            memory_type = mem.get("type", "general")
            importance = mem.get("importance", 5)
            museum_name = mem.get("museum_name")
            tags = mem.get("tags")

            # Resolve museum_id
            museum_id = None
            if museum_name:
                museum_id = _resolve_museum_id(museum_name)

            # Promote to MEMORY.md for high-importance strategic/contact/museum intel
            update_memory = importance >= 7 and memory_type in ("contact_intel", "museum_intel", "strategy")

            write_memory(
                content=content,
                memory_type=memory_type,
                importance=importance,
                update_memory=update_memory,
                museum_id=museum_id,
                tags=json.dumps(tags) if tags else None,
                source="extraction",
            )

    except Exception as e:
        logger.debug(f"Memory extraction failed: {e}")


# ── Logging helpers ───────────────────────────────────────────────────────────


def _save_to_daily_log(user_message: str, assistant_response: str, session_id: str):
    """Append the exchange to the daily conversation log."""
    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    log_path = LOGS_DIR / f"{datetime.now().strftime('%Y-%m-%d')}.md"

    timestamp = datetime.now().strftime("%H:%M:%S")

    if not log_path.exists():
        log_path.write_text(f"# Conversation Log - {datetime.now().strftime('%Y-%m-%d')}\n\n")

    with open(log_path, "a") as f:
        f.write(f"## Session {session_id} — {timestamp}\n")
        f.write(f"**Hermann:** {user_message}\n\n")
        f.write(f"**Touri:** {assistant_response}\n\n---\n\n")


def _index_session_on_exit(session_id: str, conversation_history: list):
    """Index the full session for cross-session search."""
    try:
        from tools.memory.memory_db import index_session
        messages = [
            (i, msg["role"], msg["content"])
            for i, msg in enumerate(conversation_history)
        ]
        index_session(session_id, messages)
    except Exception as e:
        logger.debug(f"Session indexing failed: {e}")


# ── Curator ───────────────────────────────────────────────────────────────────


def _maybe_run_curator():
    """Run memory curator once per day (check via a simple flag file).

    Silently skips if already run today.  Any error is swallowed so it
    never interrupts a chat session.
    """
    flag_path = PROJECT_ROOT / "data" / ".curator_last_run"
    today = datetime.now().strftime("%Y-%m-%d")

    if flag_path.exists() and flag_path.read_text().strip() == today:
        return  # Already ran today

    try:
        from tools.memory.memory_curator import expire_working_memory, expire_db_memories, consolidate_memories
        expired_md = expire_working_memory()
        expired_db = expire_db_memories()
        consolidated = consolidate_memories()
        if expired_md or expired_db or consolidated:
            logger.info(
                "Curator: expired %d MEMORY.md entries, %d DB memories, consolidated %d",
                expired_md, expired_db, consolidated,
            )
        flag_path.parent.mkdir(parents=True, exist_ok=True)
        flag_path.write_text(today)
    except Exception as e:
        logger.debug("Curator failed silently: %s", e)


# ── Main chat loop ────────────────────────────────────────────────────────────


def run_chat():
    """Main interactive chat loop."""
    # Load .env
    try:
        from dotenv import load_dotenv
        load_dotenv(PROJECT_ROOT / ".env")
    except ImportError:
        pass

    # Run curator once per day (silent — errors are swallowed)
    _maybe_run_curator()

    # Suppress tokenizer parallelism warnings
    os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")

    settings = _load_settings()
    model_cfg = settings.get("models", {}).get("chat", {})
    model = model_cfg.get("model", "claude-sonnet-4-6")
    max_tokens = model_cfg.get("max_tokens", 4096)
    temperature = model_cfg.get("temperature", 0.7)

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        console.print("[bold red]Error:[/] ANTHROPIC_API_KEY not set. Add it to .env", style="red")
        return

    client = anthropic.Anthropic(api_key=api_key)
    session_id = datetime.now().strftime("%Y%m%d-%H%M%S-") + uuid.uuid4().hex[:6]
    conversation_history = []

    # Header
    console.print()
    console.print(Panel(
        "[bold cyan]Touri[/bold cyan] — AITourPilot Outreach Co-Pilot",
        subtitle=f"Session {session_id}",
        border_style="cyan",
    ))
    console.print("  Type [bold]exit[/bold] or [bold]quit[/bold] to end the session.\n")

    while True:
        try:
            user_input = console.input("[bold green]Hermann > [/bold green]").strip()
        except (EOFError, KeyboardInterrupt):
            console.print("\n")
            break

        if not user_input:
            continue

        if user_input.lower() in ("exit", "quit", "/exit", "/quit"):
            break

        # Assemble tiered context (system prompt rebuilt each turn for museum context awareness)
        system_prompt, additional_context, museum_id = _assemble_context(user_input)

        # Build messages
        messages = list(conversation_history)

        # Inject additional context into user message
        if additional_context:
            augmented_input = (
                f"{user_input}\n\n---\n"
                "[Context — do not repeat this to the user, use it to inform your response]\n"
                f"{additional_context}"
            )
        else:
            augmented_input = user_input

        messages.append({"role": "user", "content": augmented_input})

        # Call Anthropic API with streaming
        try:
            console.print()
            full_response = ""

            with client.messages.stream(
                model=model,
                max_tokens=max_tokens,
                temperature=temperature,
                system=system_prompt,
                messages=messages,
            ) as stream:
                console.print("[bold cyan]Touri > [/bold cyan]", end="")
                for text in stream.text_stream:
                    console.print(text, end="", highlight=False)
                    full_response += text

            console.print("\n")

            # Update conversation history (store original user input, not augmented)
            conversation_history.append({"role": "user", "content": user_input})
            conversation_history.append({"role": "assistant", "content": full_response})

            # Save to daily log
            _save_to_daily_log(user_input, full_response, session_id)

            # Extract and save memories (async-like, but synchronous for simplicity)
            _extract_and_save_memories(user_input, full_response, client, settings)

        except anthropic.APIError as e:
            console.print(f"\n[bold red]API Error:[/bold red] {e}", style="red")
        except Exception as e:
            console.print(f"\n[bold red]Error:[/bold red] {e}", style="red")
            logger.exception("Chat error")

    # Session end: index for future search
    console.print("[dim]Indexing session for future recall...[/dim]")
    _index_session_on_exit(session_id, conversation_history)
    console.print("[dim]Session ended. Memories saved.[/dim]\n")
