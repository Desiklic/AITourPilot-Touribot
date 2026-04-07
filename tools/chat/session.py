"""Chat session: context assembly, Anthropic API call, memory extraction, conversation log."""

import logging
import os
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


def _build_system_prompt() -> str:
    """Assemble the system prompt from soul.md + USER.md + MEMORY.md."""
    parts = []

    soul = _load_file(SOUL_MD)
    if soul:
        parts.append(soul)

    user = _load_file(USER_MD)
    if user:
        parts.append(f"\n---\n\n{user}")

    memory = _load_file(MEMORY_MD)
    if memory:
        parts.append(f"\n---\n\n## Working Memory\n\n{memory}")

    parts.append(f"\n---\n\nCurrent date: {datetime.now().strftime('%Y-%m-%d %H:%M')}")

    return "\n".join(parts)


def _search_memory_context(user_message: str) -> str:
    """Search memory DB for context relevant to the user's message."""
    try:
        from tools.memory.memory_db import hybrid_search
        results = hybrid_search(user_message, limit=5, include_sessions=True)
        if not results:
            return ""

        lines = ["## Relevant Memories\n"]
        for r in results:
            score = r.get("score", 0.0)
            if score < 0.1:
                continue
            source = r.get("source", "memory")
            content = r.get("content", "")[:300]
            lines.append(f"- [{source}] {content}")

        if len(lines) > 1:
            return "\n".join(lines)
    except Exception as e:
        logger.debug(f"Memory search failed: {e}")

    return ""


def _extract_and_save_memories(user_message: str, assistant_response: str, client: anthropic.Anthropic, settings: dict):
    """After a response, use a fast model to extract facts worth remembering."""
    try:
        model_cfg = settings.get("models", {}).get("memory_extraction", {})
        model = model_cfg.get("model", "claude-haiku-4-5-20251001")

        extraction_prompt = f"""Analyze this exchange and extract any facts worth remembering for future sessions.
Focus on:
- Decisions made about specific museums or contacts
- New information about leads (names, roles, preferences, responses)
- Campaign strategy decisions
- Email drafting preferences or feedback

If there is nothing worth saving, respond with exactly: NONE

If there are facts to save, respond with one fact per line, each prefixed with:
- [FACT] for permanent facts (importance 7+)
- [EVENT] for dated interactions (importance 5)
- [INSIGHT] for learnings (importance 6)

Include [MUSEUM: Name] tags where relevant.

Exchange:
Hermann: {user_message}
Touri: {assistant_response[:1000]}"""

        response = client.messages.create(
            model=model,
            max_tokens=512,
            temperature=0.2,
            messages=[{"role": "user", "content": extraction_prompt}],
        )

        text = response.content[0].text.strip()
        if text == "NONE" or not text:
            return

        from tools.memory.memory_write import write_memory

        for line in text.split("\n"):
            line = line.strip()
            if not line:
                continue

            if line.startswith("[FACT]"):
                content = line[6:].strip()
                write_memory(content, memory_type="fact", importance=7, update_memory=True)
            elif line.startswith("[EVENT]"):
                content = line[7:].strip()
                write_memory(content, memory_type="event", importance=5)
            elif line.startswith("[INSIGHT]"):
                content = line[9:].strip()
                write_memory(content, memory_type="insight", importance=6, update_memory=True)

    except Exception as e:
        logger.debug(f"Memory extraction failed: {e}")


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


def run_chat():
    """Main interactive chat loop."""
    # Load .env
    try:
        from dotenv import load_dotenv
        load_dotenv(PROJECT_ROOT / ".env")
    except ImportError:
        pass

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

    system_prompt = _build_system_prompt()

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

        # Search memory for relevant context
        memory_context = _search_memory_context(user_input)

        # Build messages
        messages = list(conversation_history)

        # Inject memory context as a system-like user message if we have any
        if memory_context:
            augmented_input = f"{user_input}\n\n---\n[Context from memory — do not repeat this to the user, use it to inform your response]\n{memory_context}"
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
