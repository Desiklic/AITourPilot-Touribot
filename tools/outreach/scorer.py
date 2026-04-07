"""Response Scorer — Classify inbound replies on a 1-5 scale.

Given the text of an inbound reply and museum context, scores the response
and suggests the appropriate next action + draft reply.
"""

import logging
import os
from pathlib import Path

import anthropic
from rich.console import Console
from rich.panel import Panel

logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).parent.parent.parent
HARDPROMPTS_DIR = PROJECT_ROOT / "hardprompts"

console = Console()


def _load_file(path: Path) -> str:
    if path.exists():
        return path.read_text()
    return ""


def score_response(museum_name: str, reply_text: str,
                   contact_name: str = "") -> dict:
    """Score an inbound reply 1-5 with explanation and suggested next action.

    Args:
        museum_name: The museum that replied
        reply_text: The full text of the inbound reply
        contact_name: Optional contact name

    Returns:
        dict with: score, category, explanation, suggested_action, draft_reply
    """
    from tools.outreach.personalizer import build_context, format_brief

    # Build context for this museum
    ctx = build_context(museum_name, contact_name)
    brief = format_brief(ctx)

    # Load response framework
    framework = _load_file(HARDPROMPTS_DIR / "objection_handling.md")

    system_prompt = f"""You are Touri, scoring an inbound email reply for Hermann Kudlich (AITourPilot).

{framework}

## Museum Context
{brief}

## Instructions
1. Score the reply 1-5 using the framework above
2. Explain your classification in 1-2 sentences
3. Suggest the specific next action Hermann should take
4. Draft a response email if appropriate (skip for Score 1 declines unless graceful thanks is needed)

## Output Format (use exactly this structure)
**Score:** [1-5]
**Category:** [Meeting requested / Strong interest / Bad timing / Unclear / Decline]
**Explanation:** [1-2 sentences]
**Next action:** [Specific action]
**Draft reply:**
[The reply email, or "N/A" if none needed]"""

    user_message = f"""Score this inbound reply from {contact_name or 'a contact'} at {museum_name}:

---
{reply_text}
---"""

    # Load settings
    try:
        import yaml
        settings_path = PROJECT_ROOT / "args" / "settings.yaml"
        with open(settings_path) as f:
            settings = yaml.safe_load(f) or {}
    except Exception:
        settings = {}

    model_cfg = settings.get("models", {}).get("chat", {})
    model = model_cfg.get("model", "claude-sonnet-4-6")

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise RuntimeError("ANTHROPIC_API_KEY not set")

    client = anthropic.Anthropic(api_key=api_key)

    response = client.messages.create(
        model=model,
        max_tokens=1024,
        temperature=0.3,
        system=system_prompt,
        messages=[{"role": "user", "content": user_message}],
    )

    result_text = response.content[0].text

    # Parse the structured output
    score = 0
    category = ""
    explanation = ""
    next_action = ""
    draft_reply = ""

    for line in result_text.split("\n"):
        if line.startswith("**Score:**"):
            try:
                score = int(line.split("**Score:**")[1].strip().split()[0])
            except (ValueError, IndexError):
                pass
        elif line.startswith("**Category:**"):
            category = line.split("**Category:**")[1].strip()
        elif line.startswith("**Explanation:**"):
            explanation = line.split("**Explanation:**")[1].strip()
        elif line.startswith("**Next action:**"):
            next_action = line.split("**Next action:**")[1].strip()
        elif line.startswith("**Draft reply:**"):
            # Everything after this line is the draft reply
            idx = result_text.index("**Draft reply:**")
            draft_reply = result_text[idx + len("**Draft reply:**"):].strip()
            break

    # Display
    score_colors = {5: "green", 4: "cyan", 3: "yellow", 2: "red", 1: "red"}
    color = score_colors.get(score, "white")

    console.print()
    console.print(Panel(
        f"[bold {color}]Score: {score}/5 — {category}[/bold {color}]\n\n"
        f"[white]{explanation}[/white]\n\n"
        f"[bold]Next action:[/bold] {next_action}",
        title=f"Response from {contact_name or museum_name}",
        border_style=color,
    ))

    if draft_reply and draft_reply != "N/A":
        console.print(f"\n[bold cyan]Draft reply:[/bold cyan]\n{draft_reply}\n")

    # Save to memory
    try:
        from tools.memory.memory_write import write_memory
        write_memory(
            content=f"[MUSEUM: {museum_name}] Received reply from {contact_name or 'contact'}, scored {score}/5 ({category}). {explanation}",
            memory_type="event",
            importance=7,
            update_memory=True,
        )
    except Exception as e:
        logger.debug(f"Memory save failed: {e}")

    return {
        "score": score,
        "category": category,
        "explanation": explanation,
        "next_action": next_action,
        "draft_reply": draft_reply,
        "full_text": result_text,
    }
