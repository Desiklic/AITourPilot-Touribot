"""Research runner — invoked as a detached subprocess by the API.

Usage: python -m tools.research.research_runner --query "..." --depth standard --session-id XXX
"""
import argparse
import logging
import sys
from pathlib import Path

# Project root is three levels up from this file (tools/research/research_runner.py)
PROJECT_ROOT = Path(__file__).parent.parent.parent


def _setup_logging() -> None:
    log_dir = PROJECT_ROOT / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        level=logging.INFO,
        handlers=[
            logging.FileHandler(log_dir / "research_runner.log"),
            logging.StreamHandler(sys.stderr),
        ],
    )


if __name__ == "__main__":
    sys.stderr.write("research_runner: starting\n")
    sys.stderr.flush()

    try:
        _setup_logging()
        logger = logging.getLogger(__name__)

        parser = argparse.ArgumentParser(description="TouriBot research subprocess")
        parser.add_argument("--query", required=True)
        parser.add_argument("--depth", default="standard")
        parser.add_argument("--session-id", required=True)
        parser.add_argument("--museum-id", default="", help="Integer museum id or empty string")
        args = parser.parse_args()

        # Resolve museum_id: empty string or "None" → None, otherwise int
        raw_museum_id = args.museum_id
        if raw_museum_id in ("", "None", "none", None):
            museum_id = None
        else:
            try:
                museum_id = int(raw_museum_id)
            except ValueError:
                logger.warning("research_runner: invalid --museum-id %r, treating as None", raw_museum_id)
                museum_id = None

        # Load .env independently — this is a detached subprocess
        try:
            from dotenv import load_dotenv
            load_dotenv(PROJECT_ROOT / ".env")
            sys.stderr.write("research_runner: .env loaded\n")
        except ImportError:
            sys.stderr.write("research_runner: dotenv not installed, skipping .env load\n")
        sys.stderr.flush()

        logger.info(
            "Research runner started: session=%s query=%s depth=%s museum_id=%s",
            args.session_id, args.query[:60], args.depth, museum_id,
        )

        from tools.research.orchestrator import run_research
        sys.stderr.write("research_runner: imports done\n")
        sys.stderr.flush()

        try:
            run_research(args.query, args.depth, args.session_id, museum_id)
            logger.info("Research runner completed: session=%s", args.session_id)
        except Exception as e:
            logger.exception("Research runner failed: session=%s error=%s", args.session_id, e)
            sys.exit(1)

    except Exception:
        import traceback
        sys.stderr.write("research_runner: FATAL CRASH\n")
        traceback.print_exc(file=sys.stderr)
        sys.stderr.flush()
        sys.exit(1)
