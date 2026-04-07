#!/usr/bin/env python3
"""Knowledge Ingestion — Extract markdown from AITourPilot wiki HTML files.

The wiki pages embed markdown in window.__MD_EN = backtick-delimited template literals.
This tool extracts that markdown, cleans it, and saves to knowledge/processed/.

Usage:
    python -m tools.knowledge.ingest          # Process all configured sources
    python -m tools.knowledge.ingest --list   # Show configured sources
"""

import re
import sys
from pathlib import Path

from rich.console import Console

PROJECT_ROOT = Path(__file__).parent.parent.parent
RAW_DIR = PROJECT_ROOT / "knowledge" / "raw"
PROCESSED_DIR = PROJECT_ROOT / "knowledge" / "processed"

console = Console()

# Source document configuration
# Maps source HTML files to output markdown files
SOURCES = [
    {
        "source": Path.home() / "Desktop" / "AITourPilot Project" / "BUSINESS_CONTENT" / "wiki" / "marketing-platform" / "20260314-precision-partner-acquisition-engine.html",
        "target": "precision_partner_engine.md",
        "title": "Precision Partner Acquisition Engine",
        "priority": "P0",
    },
    {
        "source": Path.home() / "Desktop" / "AITourPilot Project" / "BUSINESS_CONTENT" / "wiki" / "marketing-platform" / "20260406-campaign-launch-research-summary.html",
        "target": "campaign_research.md",
        "title": "Campaign Launch Research Summary",
        "priority": "P0",
    },
    {
        "source": Path.home() / "Desktop" / "AITourPilot Project" / "BUSINESS_CONTENT" / "wiki" / "marketing-platform" / "20260403-aitourpilot-product-overview-platform-benefits-and-case-study.html",
        "target": "product_overview.md",
        "title": "AITourPilot Product Overview",
        "priority": "P1",
    },
    {
        "source": Path.home() / "Desktop" / "AITourPilot Project" / "BUSINESS_CONTENT" / "wiki" / "marketing-platform" / "20260318-outreach-infrastructure-blueprint.html",
        "target": "outreach_infrastructure.md",
        "title": "Outreach Infrastructure Blueprint",
        "priority": "P2",
    },
    {
        "source": Path.home() / "Desktop" / "AITourPilot Project" / "BUSINESS_CONTENT" / "wiki" / "marketing-platform" / "20260317-touribot-marketing-platform-architecture.html",
        "target": "touribot_architecture_original.md",
        "title": "TouriBot Marketing Platform Architecture (Original Vision)",
        "priority": "P2",
    },
]

# Sections to extract from specific documents into separate files
SECTION_EXTRACTS = [
    {
        "from_target": "precision_partner_engine.md",
        "output": "email_templates.md",
        "sections": ["Module 4: Message Sequencing Engine"],
        "title": "Email Sequencing Templates",
    },
    {
        "from_target": "precision_partner_engine.md",
        "output": "engagement_response_framework.md",
        "sections": ["Module 6: Response Handling Engine"],
        "title": "Engagement Response Framework",
    },
    {
        "from_target": "campaign_research.md",
        "output": "museum_procurement.md",
        "sections": ["Museum Procurement Intelligence", "Recommended Pilot Structure"],
        "title": "Museum Procurement Intelligence",
    },
    {
        "from_target": "precision_partner_engine.md",
        "output": "campaign_2025_analysis.md",
        "sections": ["Reactivation Campaign: The 74 Warm Contacts", "LinkedIn Campaign 2.0"],
        "title": "Campaign Analysis and Reactivation Strategy",
    },
]


def _extract_markdown_from_html(html_content: str) -> str:
    """Extract markdown from window.__MD_EN template literal in HTML."""
    match = re.search(r'window\.__MD_EN\s*=\s*`(.*?)`\s*;', html_content, re.DOTALL)
    if match:
        return match.group(1).strip()
    return ""


def _clean_markdown(md: str) -> str:
    """Clean up extracted markdown."""
    # Unescape backtick escapes from JS template literals
    md = md.replace("\\`", "`")
    md = md.replace("\\$", "$")
    # Unescape unicode sequences (e.g. \u2192 → →, \u2193 → ↓)
    md = re.sub(r'\\u([0-9a-fA-F]{4})', lambda m: chr(int(m.group(1), 16)), md)
    # Remove any zero-width characters
    md = md.replace("\u200b", "")
    # Normalize line endings
    md = md.replace("\r\n", "\n")
    # Remove excessive blank lines (more than 2 consecutive)
    md = re.sub(r'\n{4,}', '\n\n\n', md)
    return md.strip()


def _extract_sections(markdown: str, section_headings: list[str]) -> str:
    """Extract specific ## sections from a markdown document."""
    lines = markdown.split("\n")
    result_lines = []
    capturing = False
    capture_level = 0

    for line in lines:
        # Check if this line is a heading
        heading_match = re.match(r'^(#{1,6})\s+(.+)', line)
        if heading_match:
            level = len(heading_match.group(1))
            heading_text = heading_match.group(2).strip()

            if any(heading_text.startswith(sh) for sh in section_headings):
                capturing = True
                capture_level = level
                result_lines.append(line)
                continue

            if capturing and level <= capture_level:
                # Hit a same-or-higher-level heading — stop capturing
                capturing = False

        if capturing:
            result_lines.append(line)

    return "\n".join(result_lines).strip()


def ingest_all():
    """Process all configured source documents."""
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    processed_count = 0
    extracted_count = 0

    # Step 1: Process full HTML → markdown files
    for src in SOURCES:
        source_path = src["source"]
        target_path = PROCESSED_DIR / src["target"]

        if not source_path.exists():
            console.print(f"  [yellow]SKIP[/yellow] {src['title']} — source not found: {source_path.name}")
            continue

        html = source_path.read_text(encoding="utf-8")
        md = _extract_markdown_from_html(html)

        if not md:
            console.print(f"  [red]FAIL[/red] {src['title']} — no markdown found in HTML")
            continue

        md = _clean_markdown(md)
        # Add title header
        output = f"# {src['title']}\n\n*Source: {source_path.name}*\n*Priority: {src['priority']}*\n\n{md}\n"

        target_path.write_text(output, encoding="utf-8")
        console.print(f"  [green]OK[/green]   {src['target']} ({len(md):,} chars) [{src['priority']}]")
        processed_count += 1

    # Step 2: Extract specific sections into separate files
    for ext in SECTION_EXTRACTS:
        source_file = PROCESSED_DIR / ext["from_target"]
        target_path = PROCESSED_DIR / ext["output"]

        if not source_file.exists():
            console.print(f"  [yellow]SKIP[/yellow] {ext['title']} — source not yet processed")
            continue

        full_md = source_file.read_text(encoding="utf-8")
        extracted = _extract_sections(full_md, ext["sections"])

        if not extracted:
            console.print(f"  [yellow]WARN[/yellow] {ext['title']} — sections not found: {ext['sections']}")
            continue

        output = f"# {ext['title']}\n\n*Extracted from: {ext['from_target']}*\n\n{extracted}\n"
        target_path.write_text(output, encoding="utf-8")
        console.print(f"  [green]OK[/green]   {ext['output']} ({len(extracted):,} chars) [extract]")
        extracted_count += 1

    return processed_count, extracted_count


def list_sources():
    """List all configured sources and their status."""
    console.print("\n[bold]Configured Knowledge Sources:[/bold]\n")
    for src in SOURCES:
        exists = src["source"].exists()
        status = "[green]found[/green]" if exists else "[red]missing[/red]"
        target = PROCESSED_DIR / src["target"]
        processed = "[green]processed[/green]" if target.exists() else "[dim]pending[/dim]"
        console.print(f"  [{src['priority']}] {src['title']}")
        console.print(f"       Source: {status} — {src['source'].name}")
        console.print(f"       Target: {processed} — {src['target']}")
        console.print()


def run_ingest():
    """Main entry point for the ingest command."""
    console.print("\n[bold cyan]Knowledge Ingestion[/bold cyan]\n")

    if "--list" in sys.argv:
        list_sources()
        return

    processed, extracted = ingest_all()
    total = processed + extracted

    console.print(f"\n[bold]Done:[/bold] {processed} documents processed, {extracted} sections extracted ({total} total files)")

    # List output files
    if PROCESSED_DIR.exists():
        files = sorted(PROCESSED_DIR.glob("*.md"))
        total_chars = sum(f.stat().st_size for f in files)
        console.print(f"[dim]{len(files)} files in knowledge/processed/ ({total_chars:,} chars total)[/dim]\n")


if __name__ == "__main__":
    run_ingest()
