"""Email Drafter — Generate personalized outreach emails via Claude API.

Takes a personalizer brief + message type, calls Claude with a focused drafting
prompt, saves the output to output/emails/, and returns the draft text.
"""

import logging
import os
import re
from datetime import datetime
from pathlib import Path

import anthropic
from rich.console import Console

logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).parent.parent.parent
SOUL_MD = PROJECT_ROOT / "soul.md"
HARDPROMPTS_DIR = PROJECT_ROOT / "hardprompts"
OUTPUT_DIR = PROJECT_ROOT / "output" / "emails"

console = Console()


def _load_file(path: Path) -> str:
    if path.exists():
        return path.read_text()
    return ""


def _slugify(name: str) -> str:
    """Turn a contact name into a filename-safe slug."""
    slug = name.lower().strip()
    slug = re.sub(r'[^a-z0-9]+', '-', slug)
    return slug.strip('-')


def _next_version(contact_slug: str, date_str: str) -> int:
    """Find the next available version number for today's drafts."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    existing = list(OUTPUT_DIR.glob(f"{date_str}-{contact_slug}-v*.md"))
    if not existing:
        return 1
    versions = []
    for f in existing:
        match = re.search(r'-v(\d+)\.md$', f.name)
        if match:
            versions.append(int(match.group(1)))
    return max(versions, default=0) + 1


def _build_drafting_prompt(brief: str, message_type: str) -> str:
    """Build the focused drafting system prompt."""
    # Load soul.md email principles
    soul = _load_file(SOUL_MD)

    # Extract just the email drafting principles section
    principles = ""
    if "## Email Drafting Principles" in soul:
        idx = soul.index("## Email Drafting Principles")
        # Take from that header to the next ## or end
        rest = soul[idx:]
        next_section = rest.find("\n## ", 3)
        principles = rest[:next_section] if next_section > 0 else rest

    # Load email templates
    templates = _load_file(HARDPROMPTS_DIR / "email_templates.md")

    type_instruction = {
        "initial": "Draft the FIRST outreach email (Message 1: Insight Hook). This is the first time Hermann contacts this person.",
        "follow-up": "Draft a FOLLOW-UP email (Message 2 or 3). Hermann has already sent an initial email with no reply.",
        "reactivation": "Draft a REACTIVATION email. Hermann met this person before but lost touch. Reference the prior connection warmly.",
        "response": "Draft a REPLY to an inbound email. Match the tone and content of their message.",
    }.get(message_type, "Draft an outreach email appropriate to the context.")

    return f"""You are Touri, drafting a personalized email for Hermann Kudlich (AITourPilot founder).

{principles}

## Task
{type_instruction}

## Key Rules
- NEVER invent facts about the museum or contact. If the brief says "we don't know" something, do NOT make it up. Either omit it or acknowledge the gap.
- The email is FROM Hermann, not from an AI. Write in first person as Hermann.
- Under 200 words for initial outreach. Under 150 for follow-ups.
- End with ONE specific, low-friction question — not "let me know".
- Match the language specified in the brief.
- Include a subject line.

## Email Templates (reference structure, do not copy verbatim)
{templates}

## Personalization Brief
{brief}

## Output Format
Write ONLY the email. Start with "Subject: ..." then the body. No preamble, no commentary, no "Here's the draft" intro."""


def draft_email(museum_name: str, contact_name: str = "",
                message_type: str = "initial", extra_context: str = "",
                stream: bool = True) -> dict:
    """Draft a personalized email and save to output/emails/.

    Args:
        museum_name: Target museum
        contact_name: Contact person name
        message_type: initial, follow-up, reactivation, response
        extra_context: Additional context from Hermann
        stream: Whether to stream output to console

    Returns:
        dict with: draft_text, file_path, museum_name, contact_name, message_type
    """
    from tools.outreach.personalizer import build_context, format_brief

    # Build personalization context
    ctx = build_context(museum_name, contact_name, extra_context)
    brief = format_brief(ctx)

    # Auto-detect reactivation if memories mention a prior meeting
    if message_type == "initial" and "reactivation" in ctx["suggested_angle"].lower():
        message_type = "reactivation"

    # Build prompt
    system_prompt = _build_drafting_prompt(brief, message_type)

    # Determine language instruction for user message
    lang = ctx["language_label"]
    user_message = f"Draft the email for {contact_name or 'the contact'} at {museum_name} in {lang}."
    if extra_context:
        user_message += f"\n\nHermann's notes: {extra_context}"

    # Load settings
    try:
        import yaml
        settings_path = PROJECT_ROOT / "args" / "settings.yaml"
        with open(settings_path) as f:
            settings = yaml.safe_load(f) or {}
    except Exception:
        settings = {}

    model_cfg = settings.get("models", {}).get("drafting", {})
    model = model_cfg.get("model", "claude-sonnet-4-6")
    max_tokens = model_cfg.get("max_tokens", 2048)
    temperature = model_cfg.get("temperature", 0.6)

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise RuntimeError("ANTHROPIC_API_KEY not set")

    client = anthropic.Anthropic(api_key=api_key)

    # Collect full response, then save to disk (safety invariant: never lose work)
    draft_text = ""

    if stream:
        console.print()
        with client.messages.stream(
            model=model,
            max_tokens=max_tokens,
            temperature=temperature,
            system=system_prompt,
            messages=[{"role": "user", "content": user_message}],
        ) as response_stream:
            console.print("[bold cyan]Touri > [/bold cyan]", end="")
            for text in response_stream.text_stream:
                console.print(text, end="", highlight=False)
                draft_text += text
        console.print("\n")
    else:
        response = client.messages.create(
            model=model,
            max_tokens=max_tokens,
            temperature=temperature,
            system=system_prompt,
            messages=[{"role": "user", "content": user_message}],
        )
        draft_text = response.content[0].text

    # Save to file
    date_str = datetime.now().strftime("%Y-%m-%d")
    slug = _slugify(contact_name or museum_name)
    version = _next_version(slug, date_str)
    filename = f"{date_str}-{slug}-v{version}.md"
    file_path = OUTPUT_DIR / filename

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Build the saved file with metadata header
    saved_content = f"""# Email Draft: {contact_name or museum_name} @ {museum_name}

**Date:** {date_str}
**Type:** {message_type}
**Language:** {ctx['language_label']}
**Version:** v{version}

---

{draft_text.strip()}

---

*Generated by Touri | Personalization brief included {len(ctx['memories'])} memory items*
"""
    file_path.write_text(saved_content, encoding="utf-8")

    console.print(f"[green]Saved to:[/green] {file_path.relative_to(PROJECT_ROOT)}")

    # Save event to memory
    try:
        from tools.memory.memory_write import write_memory
        summary = draft_text[:200].replace('\n', ' ')
        write_memory(
            content=f"[MUSEUM: {museum_name}] Drafted {message_type} email for {contact_name or 'contact'}: {summary}",
            memory_type="event",
            importance=6,
        )
    except Exception as e:
        logger.debug(f"Memory save failed: {e}")

    return {
        "draft_text": draft_text,
        "file_path": str(file_path),
        "museum_name": museum_name,
        "contact_name": contact_name,
        "message_type": message_type,
        "language": ctx["language"],
        "version": version,
    }
