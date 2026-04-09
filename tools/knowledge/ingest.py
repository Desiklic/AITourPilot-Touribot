#!/usr/bin/env python3
"""Knowledge Ingestion — config-driven extraction from multiple file formats.

Sources are declared in args/settings.yaml under knowledge.sources.
Each source specifies a folder path, glob pattern, extractor type, and access mode.

Supported extractors:
  html_wiki — Wiki HTML pages with window.__MD_EN template literal
  txt       — Plain text files
  md        — Markdown files (read as-is)
  pdf       — PDF files (pdfplumber)
  docx      — Word documents (python-docx)
  auto      — Detect by file extension

Usage:
    python -m tools.knowledge.ingest          # Process all configured sources
    python -m tools.knowledge.ingest --list   # Show configured sources with counts
"""

import re
import sys
from pathlib import Path

import yaml
from rich.console import Console

PROJECT_ROOT = Path(__file__).parent.parent.parent
PROCESSED_DIR = PROJECT_ROOT / "knowledge" / "processed"

console = Console()

# ── Legacy hardcoded section extracts (preserved from Phase 1-5) ──────────────
# These derive sub-documents from the main HTML-sourced markdown files.

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

# ── Legacy hardcoded HTML sources (preserved for backward compatibility) ──────
# These are also captured by the Business Wiki source in settings.yaml,
# but we keep the explicit list so existing target filenames and section extracts
# continue to work unchanged.

_LEGACY_SOURCES = [
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

# Filenames produced by legacy sources — excluded from config-driven processing
# so the same content is not ingested twice.
_LEGACY_TARGET_NAMES = {src["source"].name for src in _LEGACY_SOURCES}


# ── Settings loader ───────────────────────────────────────────────────────────


def _load_settings() -> dict:
    settings_path = PROJECT_ROOT / "args" / "settings.yaml"
    try:
        with open(settings_path) as f:
            return yaml.safe_load(f) or {}
    except Exception:
        return {}


def _load_sources() -> list[dict]:
    """Return the knowledge sources list from settings.yaml."""
    settings = _load_settings()
    return settings.get("knowledge", {}).get("sources", [])


def _max_file_size_bytes() -> int:
    settings = _load_settings()
    mb = settings.get("knowledge", {}).get("max_file_size_mb", 10)
    return int(mb * 1024 * 1024)


# ── Path helpers ──────────────────────────────────────────────────────────────


def _resolve_source_path(raw_path: str) -> Path:
    """Expand ~ and relative paths against PROJECT_ROOT."""
    p = Path(raw_path).expanduser()
    if not p.is_absolute():
        p = PROJECT_ROOT / p
    return p


def _safe_stem(path: Path) -> str:
    """Create a safe output filename stem from a source path."""
    # Use parent folder (slugified) + stem to avoid collisions across folders
    folder_slug = re.sub(r'[^a-z0-9]+', '_', path.parent.name.lower()).strip('_')
    file_slug = re.sub(r'[^a-z0-9]+', '_', path.stem.lower()).strip('_')
    return f"{folder_slug}__{file_slug}"


def _matches_exclude(path: Path, exclude_patterns: list[str]) -> bool:
    """Return True if the path matches any exclude glob pattern."""
    for pattern in exclude_patterns:
        if path.match(pattern):
            return True
    return False


# ── Glob expansion ────────────────────────────────────────────────────────────


def _expand_glob(root: Path, glob_pattern: str) -> list[Path]:
    """Expand a glob pattern that may contain brace alternatives like **/*.{txt,md}."""
    brace_match = re.search(r'\{([^}]+)\}', glob_pattern)
    if brace_match:
        alternatives = brace_match.group(1).split(',')
        prefix = glob_pattern[:brace_match.start()]
        suffix = glob_pattern[brace_match.end():]
        paths = []
        for alt in alternatives:
            expanded = prefix + alt.strip() + suffix
            paths.extend(root.glob(expanded))
        return sorted(set(paths))
    return sorted(root.glob(glob_pattern))


# ── Extraction dispatch ───────────────────────────────────────────────────────


def _extract(path: Path, extractor: str) -> str:
    """Dispatch to the correct extractor and return markdown text."""
    from tools.knowledge.extractors import (
        extract_html, extract_txt, extract_md, extract_pdf, extract_docx, extract_auto,
    )
    if extractor == "html_wiki":
        return extract_html(path)
    elif extractor == "txt":
        return extract_txt(path)
    elif extractor == "md":
        return extract_md(path)
    elif extractor == "pdf":
        return extract_pdf(path)
    elif extractor == "docx":
        return extract_docx(path)
    else:  # auto
        return extract_auto(path)


# ── Section extraction (legacy helper, preserved) ─────────────────────────────


def _extract_sections(markdown: str, section_headings: list[str]) -> str:
    """Extract specific ## sections from a markdown document."""
    lines = markdown.split("\n")
    result_lines = []
    capturing = False
    capture_level = 0

    for line in lines:
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
                capturing = False

        if capturing:
            result_lines.append(line)

    return "\n".join(result_lines).strip()


# ── Core ingest logic ─────────────────────────────────────────────────────────


def _ingest_legacy_sources(processed_dir: Path) -> int:
    """Process the legacy hardcoded HTML sources → named markdown files."""
    from tools.knowledge.extractors import extract_html
    count = 0
    for src in _LEGACY_SOURCES:
        source_path = src["source"]
        target_path = processed_dir / src["target"]

        if not source_path.exists():
            console.print(f"  [yellow]SKIP[/yellow] {src['title']} — source not found: {source_path.name}")
            continue

        md = extract_html(source_path)
        if not md:
            console.print(f"  [red]FAIL[/red] {src['title']} — no markdown found in HTML")
            continue

        output = f"# {src['title']}\n\n*Source: {source_path.name}*\n*Priority: {src['priority']}*\n\n{md}\n"
        target_path.write_text(output, encoding="utf-8")
        console.print(f"  [green]OK[/green]   {src['target']} ({len(md):,} chars) [{src['priority']}]")
        count += 1
    return count


def _ingest_section_extracts(processed_dir: Path) -> int:
    """Derive sub-documents from already-processed markdown files."""
    count = 0
    for ext in SECTION_EXTRACTS:
        source_file = processed_dir / ext["from_target"]
        target_path = processed_dir / ext["output"]

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
        count += 1
    return count


def _ingest_configured_sources(processed_dir: Path) -> int:
    """Process all sources declared in settings.yaml knowledge.sources."""
    sources = _load_sources()
    max_bytes = _max_file_size_bytes()
    count = 0

    for source_cfg in sources:
        raw_path = source_cfg.get("path", "")
        glob_pattern = source_cfg.get("glob", "**/*")
        extractor = source_cfg.get("extractor", "auto")
        label = source_cfg.get("label", raw_path)
        exclude_patterns = source_cfg.get("exclude_patterns", [])

        root = _resolve_source_path(raw_path)
        if not root.exists():
            console.print(f"  [yellow]SKIP[/yellow] [{label}] folder not found: {root}")
            continue

        files = _expand_glob(root, glob_pattern)
        source_count = 0

        for file_path in files:
            # Skip legacy-managed files (avoid duplicate processing)
            if file_path.name in _LEGACY_TARGET_NAMES:
                continue

            # Skip excluded patterns
            if _matches_exclude(file_path, exclude_patterns):
                continue

            # Skip files that are too large
            try:
                if file_path.stat().st_size > max_bytes:
                    console.print(f"  [yellow]SKIP[/yellow] {file_path.name} — exceeds {max_bytes // (1024*1024)}MB limit")
                    continue
            except OSError:
                continue

            # Extract content
            content = _extract(file_path, extractor)
            if not content or not content.strip():
                continue

            # Build output filename: label_slug__file_stem.md
            label_slug = re.sub(r'[^a-z0-9]+', '_', label.lower()).strip('_')
            file_stem = _safe_stem(file_path)
            out_name = f"{label_slug}__{file_stem}.md"
            out_path = processed_dir / out_name

            # Build header
            rel_path = file_path.relative_to(root) if file_path.is_relative_to(root) else file_path
            header = (
                f"# {file_path.stem}\n\n"
                f"*Source: {label} / {rel_path}*\n\n"
            )
            out_path.write_text(header + content + "\n", encoding="utf-8")
            source_count += 1
            count += 1

        if source_count > 0:
            console.print(f"  [green]OK[/green]   [{label}] {source_count} files processed")
        elif root.exists():
            console.print(f"  [dim]    [{label}] 0 files matched (folder exists)[/dim]")

    return count


def ingest_all():
    """Process all sources: legacy HTML + configured folder sources + section extracts."""
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    console.print("\n[bold]Step 1:[/bold] Legacy HTML sources")
    legacy_count = _ingest_legacy_sources(PROCESSED_DIR)

    console.print("\n[bold]Step 2:[/bold] Config-driven folder sources")
    config_count = _ingest_configured_sources(PROCESSED_DIR)

    console.print("\n[bold]Step 3:[/bold] Section extracts")
    extract_count = _ingest_section_extracts(PROCESSED_DIR)

    return legacy_count, config_count, extract_count


# ── List command ──────────────────────────────────────────────────────────────


def list_sources():
    """List all configured sources with file counts."""
    console.print("\n[bold]Legacy HTML Sources:[/bold]\n")
    for src in _LEGACY_SOURCES:
        exists = src["source"].exists()
        status = "[green]found[/green]" if exists else "[red]missing[/red]"
        target = PROCESSED_DIR / src["target"]
        processed = "[green]processed[/green]" if target.exists() else "[dim]pending[/dim]"
        console.print(f"  [{src['priority']}] {src['title']}")
        console.print(f"       Source: {status} — {src['source'].name}")
        console.print(f"       Target: {processed} — {src['target']}")
        console.print()

    sources = _load_sources()
    if not sources:
        console.print("[dim]No sources configured in settings.yaml knowledge.sources[/dim]")
        return

    console.print("[bold]Config-driven Sources:[/bold]\n")
    max_bytes = _max_file_size_bytes()
    for source_cfg in sources:
        raw_path = source_cfg.get("path", "")
        glob_pattern = source_cfg.get("glob", "**/*")
        extractor = source_cfg.get("extractor", "auto")
        label = source_cfg.get("label", raw_path)
        access = source_cfg.get("access", "read")
        exclude_patterns = source_cfg.get("exclude_patterns", [])

        root = _resolve_source_path(raw_path)
        exists = root.exists()
        status = "[green]found[/green]" if exists else "[red]missing[/red]"

        file_count = 0
        if exists:
            files = _expand_glob(root, glob_pattern)
            file_count = sum(
                1 for f in files
                if f.name not in _LEGACY_TARGET_NAMES
                and not _matches_exclude(f, exclude_patterns)
                and f.stat().st_size <= max_bytes
            )

        console.print(f"  [bold]{label}[/bold] ({access})")
        console.print(f"       Path:      {status} — {root}")
        console.print(f"       Glob:      {glob_pattern}  extractor={extractor}")
        console.print(f"       Files:     {file_count} eligible files")
        console.print()


# ── Entry point ───────────────────────────────────────────────────────────────


def run_ingest():
    """Main entry point for the ingest command."""
    console.print("\n[bold cyan]Knowledge Ingestion[/bold cyan]\n")

    if "--list" in sys.argv:
        list_sources()
        return

    legacy_count, config_count, extract_count = ingest_all()
    total = legacy_count + config_count + extract_count

    console.print(
        f"\n[bold]Done:[/bold] {legacy_count} legacy HTML, "
        f"{config_count} config-driven, "
        f"{extract_count} section extracts "
        f"({total} total files written)"
    )

    if PROCESSED_DIR.exists():
        files = sorted(PROCESSED_DIR.glob("*.md"))
        total_chars = sum(f.stat().st_size for f in files)
        console.print(f"[dim]{len(files)} files in knowledge/processed/ ({total_chars:,} chars total)[/dim]\n")


if __name__ == "__main__":
    run_ingest()
