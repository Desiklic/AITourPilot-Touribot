"""Personalizer — Build per-museum context package for email drafting.

Given a museum name and contact name, assembles everything Touri knows:
- Memories tagged with [MUSEUM: name]
- General memories mentioning the museum or contact
- Relevant knowledge base context
- Structured brief for the drafter
"""

import logging
import re
from pathlib import Path

logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).parent.parent.parent
KNOWLEDGE_DIR = PROJECT_ROOT / "knowledge" / "processed"
HARDPROMPTS_DIR = PROJECT_ROOT / "hardprompts"


def _load_file(path: Path) -> str:
    if path.exists():
        return path.read_text()
    return ""


def _search_museum_memories(museum_name: str, contact_name: str = "") -> list[dict]:
    """Search memory DB for everything related to this museum/contact."""
    try:
        from tools.memory.memory_db import hybrid_search

        results = []
        seen_ids = set()

        # Search by museum name
        museum_results = hybrid_search(museum_name, limit=10, include_sessions=True)
        for r in museum_results:
            if r.get("score", 0) >= 0.005 and r["id"] not in seen_ids:  # RRF scores are ~0.001-0.03
                results.append(r)
                seen_ids.add(r["id"])

        # Search by contact name if provided
        if contact_name:
            contact_results = hybrid_search(contact_name, limit=5, include_sessions=True)
            for r in contact_results:
                if r.get("score", 0) >= 0.005 and r["id"] not in seen_ids:  # RRF scores are ~0.001-0.03
                    results.append(r)
                    seen_ids.add(r["id"])

        # Also search for the [MUSEUM: tag] pattern
        tag_query = f"MUSEUM {museum_name}"
        tag_results = hybrid_search(tag_query, limit=5, include_sessions=True)
        for r in tag_results:
            if r.get("score", 0) >= 0.005 and r["id"] not in seen_ids:  # RRF scores are ~0.001-0.03
                results.append(r)
                seen_ids.add(r["id"])

        # Direct lookup of research memories by museum_id (Phase M5 bridge)
        try:
            from tools.leads.lead_db import get_museum
            from tools.memory.memory_db import list_memories

            museum_record = get_museum(museum_name)
            if museum_record:
                research_mems = list_memories(
                    limit=10, memory_type="research", museum_id=museum_record["id"]
                )
                for r in research_mems:
                    if r["id"] not in seen_ids:
                        results.append(r)
                        seen_ids.add(r["id"])
        except Exception as e:
            logger.debug(f"Research memory lookup failed: {e}")

        return results

    except Exception as e:
        logger.debug(f"Memory search failed: {e}")
        return []


def _detect_language(museum_name: str, contact_name: str, memories: list[dict]) -> str:
    """Detect preferred email language from museum name and targeted memories.

    Priority: explicit language pref in memories > museum/city-based detection > English default.
    Only considers memories that actually mention this museum or contact to avoid cross-contamination.
    """
    # First pass: check museum name + contact name only (most reliable signal)
    primary_text = f"{museum_name} {contact_name}".lower()

    dach = ["austria", "graz", "vienna", "wien", "salzburg", "innsbruck",
            "germany", "berlin", "munich", "hamburg", "deutschland",
            "joanneum", "albertina", "kunsthistorisches"]
    if any(kw in primary_text for kw in dach):
        return "de"

    french = ["france", "paris", "lyon", "geneva", "geneve", "genf",
              "cap sciences", "mah geneva", "bordeaux"]
    if any(kw in primary_text for kw in french):
        return "fr"

    dutch = ["netherlands", "holland", "amsterdam", "rotterdam",
             "loevestein"]
    if any(kw in primary_text for kw in dutch):
        return "nl"

    # Second pass: check only memories that mention THIS museum or contact
    museum_lower = museum_name.lower()
    contact_lower = contact_name.lower() if contact_name else ""
    relevant_text = ""
    for m in memories:
        content = m.get("content", "").lower()
        if museum_lower in content or (contact_lower and contact_lower in content):
            relevant_text += content + " "

    if "german" in relevant_text or "auf deutsch" in relevant_text:
        return "de"
    if "french" in relevant_text or "en français" in relevant_text:
        return "fr"
    if "dutch" in relevant_text or "in het nederlands" in relevant_text:
        return "nl"

    return "en"


def build_context(museum_name: str, contact_name: str = "",
                  extra_context: str = "") -> dict:
    """Build a structured context package for a specific museum/contact.

    Returns a dict with:
        museum_name, contact_name, language,
        what_we_know, what_we_dont_know, suggested_angle,
        memories (raw list), extra_context
    """
    memories = _search_museum_memories(museum_name, contact_name)
    language = _detect_language(museum_name, contact_name, memories)

    # Filter memories to those actually relevant to THIS museum/contact
    museum_lower = museum_name.lower()
    contact_lower = contact_name.lower() if contact_name else ""
    known_facts = []
    for m in memories:
        content = m.get("content", "").strip()
        if not content:
            continue
        content_lower = content.lower()
        if museum_lower in content_lower or (contact_lower and contact_lower in content_lower):
            known_facts.append(content)

    # Build what-we-know summary
    what_we_know = "\n".join(f"- {fact}" for fact in known_facts) if known_facts else "No prior information in memory."

    # Build what-we-don't-know (standard gaps)
    unknowns = []
    combined_text = " ".join(known_facts).lower()
    if "visitor" not in combined_text and "attendance" not in combined_text:
        unknowns.append("Visitor numbers / attendance figures")
    if "audio" not in combined_text and "guide" not in combined_text and "digital" not in combined_text:
        unknowns.append("Current audio guide or digital guide setup")
    if "role" not in combined_text and "head of" not in combined_text and "director" not in combined_text:
        unknowns.append(f"Exact role/title of {contact_name or 'the contact'}")
    if "budget" not in combined_text and "innovation" not in combined_text:
        unknowns.append("Innovation budget status for 2026")
    if not unknowns:
        unknowns.append("All key facts appear to be covered")

    what_we_dont_know = "\n".join(f"- {gap}" for gap in unknowns)

    # Suggested angle based on what we know
    if any("meeting" in f.lower() or "demo" in f.lower() or "met" in f.lower() for f in known_facts):
        suggested_angle = "Reactivation — reference the prior meeting, acknowledge the gap, offer to pick up where you left off"
    elif any("replied" in f.lower() or "interest" in f.lower() for f in known_facts):
        suggested_angle = "Follow-up — build on their expressed interest with new proof points"
    else:
        suggested_angle = "Cold outreach — lead with an insight specific to their museum, use the Insight Hook template"

    lang_labels = {"en": "English", "de": "German", "fr": "French", "nl": "Dutch"}

    return {
        "museum_name": museum_name,
        "contact_name": contact_name,
        "language": language,
        "language_label": lang_labels.get(language, "English"),
        "what_we_know": what_we_know,
        "what_we_dont_know": what_we_dont_know,
        "suggested_angle": suggested_angle,
        "memories": memories,
        "extra_context": extra_context,
    }


def format_brief(ctx: dict) -> str:
    """Format the context package as a readable brief for the drafter prompt."""
    lines = [
        f"## Personalization Brief: {ctx['museum_name']}",
        f"**Contact:** {ctx['contact_name'] or 'Unknown'}",
        f"**Language:** {ctx['language_label']}",
        f"**Suggested angle:** {ctx['suggested_angle']}",
        "",
        "### What we know",
        ctx["what_we_know"],
        "",
        "### What we don't know",
        ctx["what_we_dont_know"],
    ]

    if ctx.get("extra_context"):
        lines.extend(["", "### Additional context from Hermann", ctx["extra_context"]])

    return "\n".join(lines)
