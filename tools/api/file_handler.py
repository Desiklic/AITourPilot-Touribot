"""File access API — browse and read files from allowed knowledge source folders.

Endpoints:
    GET /api/files/list?source_label=Business+Wiki
    GET /api/files/read?source_label=Business+Wiki&path=wiki/research/article.html

Security:
    - Path traversal protection: all resolved paths are verified to sit within the
      configured source root before any file is opened.
    - Read-only enforcement: write-mode endpoints (future) will be rejected for
      sources with access=read.
    - File size cap: requests for files exceeding knowledge.max_file_size_mb return 413.
    - API is only bound to 127.0.0.1 (server.py), so not exposed to the internet.
"""

import re
from pathlib import Path

import yaml
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import JSONResponse

router = APIRouter()

PROJECT_ROOT = Path(__file__).parent.parent.parent


# ── Settings helpers ──────────────────────────────────────────────────────────


def _load_sources() -> list[dict]:
    settings_path = PROJECT_ROOT / "args" / "settings.yaml"
    try:
        with open(settings_path) as f:
            cfg = yaml.safe_load(f) or {}
        return cfg.get("knowledge", {}).get("sources", [])
    except Exception:
        return []


def _max_file_size_bytes() -> int:
    settings_path = PROJECT_ROOT / "args" / "settings.yaml"
    try:
        with open(settings_path) as f:
            cfg = yaml.safe_load(f) or {}
        mb = cfg.get("knowledge", {}).get("max_file_size_mb", 10)
        return int(mb * 1024 * 1024)
    except Exception:
        return 10 * 1024 * 1024


# ── Path resolution ───────────────────────────────────────────────────────────


def _resolve_root(raw_path: str) -> Path:
    """Expand ~ and resolve relative paths against PROJECT_ROOT."""
    p = Path(raw_path).expanduser()
    if not p.is_absolute():
        p = PROJECT_ROOT / p
    return p.resolve()


def _find_source(label: str) -> dict | None:
    """Find a source config entry by label (case-insensitive)."""
    for src in _load_sources():
        if src.get("label", "").lower() == label.lower():
            return src
    return None


def _assert_within_root(target: Path, root: Path) -> None:
    """Raise 403 if target is not strictly under root (path traversal guard)."""
    try:
        target.relative_to(root)
    except ValueError:
        raise HTTPException(
            status_code=403,
            detail="Access denied: path is outside the allowed folder."
        )


# ── Glob helpers (same as ingest.py — local copy to avoid circular import) ────


def _expand_glob(root: Path, glob_pattern: str) -> list[Path]:
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


def _matches_exclude(path: Path, exclude_patterns: list[str]) -> bool:
    for pattern in exclude_patterns:
        if path.match(pattern):
            return True
    return False


# ── Endpoints ─────────────────────────────────────────────────────────────────


@router.get("/list")
def list_files(
    source_label: str = Query(..., description="Label of the configured knowledge source"),
    glob: str = Query(None, description="Optional glob to filter files (overrides source default)"),
):
    """List files available in a configured knowledge source folder."""
    source = _find_source(source_label)
    if source is None:
        labels = [s.get("label", "") for s in _load_sources()]
        raise HTTPException(
            status_code=404,
            detail=f"Source '{source_label}' not found. Available: {labels}",
        )

    root = _resolve_root(source["path"])
    if not root.exists():
        raise HTTPException(status_code=404, detail=f"Source folder does not exist: {root}")

    glob_pattern = glob or source.get("glob", "**/*")
    exclude_patterns = source.get("exclude_patterns", [])
    max_bytes = _max_file_size_bytes()

    files = _expand_glob(root, glob_pattern)
    result = []
    for f in files:
        if not f.is_file():
            continue
        if _matches_exclude(f, exclude_patterns):
            continue
        try:
            size = f.stat().st_size
        except OSError:
            continue
        result.append({
            "path": str(f.relative_to(root)),
            "name": f.name,
            "size_bytes": size,
            "too_large": size > max_bytes,
        })

    return JSONResponse({
        "source_label": source["label"],
        "root": str(root),
        "access": source.get("access", "read"),
        "file_count": len(result),
        "files": result,
    })


@router.get("/read")
def read_file(
    source_label: str = Query(..., description="Label of the configured knowledge source"),
    path: str = Query(..., description="Relative path within the source folder"),
):
    """Read the raw content of a single file from a configured knowledge source."""
    source = _find_source(source_label)
    if source is None:
        labels = [s.get("label", "") for s in _load_sources()]
        raise HTTPException(
            status_code=404,
            detail=f"Source '{source_label}' not found. Available: {labels}",
        )

    root = _resolve_root(source["path"])
    if not root.exists():
        raise HTTPException(status_code=404, detail=f"Source folder does not exist: {root}")

    # Path traversal protection — resolve and verify
    try:
        # Reject absolute paths outright (e.g. /etc/passwd)
        if Path(path).is_absolute():
            raise HTTPException(
                status_code=403,
                detail="Access denied: absolute paths are not allowed."
            )
        # Normalise: strip leading slashes/dots so the join works correctly
        clean_rel = Path(path.lstrip("/"))
        target = (root / clean_rel).resolve()
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid path.")

    _assert_within_root(target, root)

    if not target.exists():
        raise HTTPException(status_code=404, detail=f"File not found: {path}")

    if not target.is_file():
        raise HTTPException(status_code=400, detail=f"Path is not a file: {path}")

    # Size cap
    max_bytes = _max_file_size_bytes()
    size = target.stat().st_size
    if size > max_bytes:
        raise HTTPException(
            status_code=413,
            detail=f"File too large ({size:,} bytes). Limit: {max_bytes:,} bytes.",
        )

    # Read content
    try:
        content = target.read_text(encoding="utf-8", errors="replace")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Could not read file: {e}")

    rel_path = str(target.relative_to(root))
    return JSONResponse({
        "source_label": source["label"],
        "path": rel_path,
        "size_bytes": size,
        "access": source.get("access", "read"),
        "content": content,
    })
