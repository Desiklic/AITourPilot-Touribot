"""Model gateway for research — routes to Anthropic or Google Gemini.

Research areas use Gemini for cost-efficiency and large context windows.
Falls back to Anthropic if Google API key is not configured.
"""
import json
import logging
import os
import time
import urllib.request
from pathlib import Path
from types import SimpleNamespace

import anthropic

_anthropic_client = None

# Gateway logger — writes to logs/gateway.log for Gemini failure tracking
_log_dir = Path(os.environ.get("TOURIBOT_HOME", Path(__file__).parent.parent.parent)) / "logs"
_log_dir.mkdir(parents=True, exist_ok=True)
_file_handler = logging.FileHandler(str(_log_dir / "gateway.log"))
_file_handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
logger = logging.getLogger("touribot.gateway")
if not logger.handlers:
    logger.addHandler(_file_handler)
    logger.setLevel(logging.INFO)


def _get_anthropic_client() -> anthropic.Anthropic:
    global _anthropic_client
    if _anthropic_client is None:
        try:
            from dotenv import load_dotenv
            from pathlib import Path
            load_dotenv(Path(__file__).parent.parent.parent / ".env")
        except ImportError:
            pass
        _anthropic_client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))
    return _anthropic_client


# Model routing: research areas → Gemini (if key available), else Anthropic fallback
GEMINI_AREA_MODELS = {
    "fast_research": "gemini-2.5-flash",
    "research": "gemini-2.5-pro",
    "deep_research": "gemini-2.5-pro",
}

ANTHROPIC_AREA_MODELS = {
    "fast_research": "claude-haiku-4-5-20251001",
    "research": "claude-sonnet-4-6",
    "deep_research": "claude-sonnet-4-6",
}

# Cost estimates per million tokens (input, output)
_MODEL_COSTS = {
    "claude-haiku-4-5-20251001": (0.80, 4.00),
    "claude-sonnet-4-6": (3.00, 15.00),
    "gemini-2.5-flash": (0.15, 0.60),
    "gemini-2.5-pro": (1.25, 10.00),
}


def _estimate_cost(model: str, input_tokens: int, output_tokens: int) -> float:
    cost_in, cost_out = _MODEL_COSTS.get(model, (3.00, 15.00))
    return (input_tokens * cost_in + output_tokens * cost_out) / 1_000_000


def _has_gemini_key() -> bool:
    return bool(os.environ.get("GOOGLE_AI_API_KEY"))


def _get_area_max_tokens(area: str) -> int:
    """Read max_tokens for an area from settings.yaml."""
    try:
        import yaml
        settings_path = os.path.join(os.environ.get("TOURIBOT_HOME", "."), "args", "settings.yaml")
        with open(settings_path) as f:
            settings = yaml.safe_load(f) or {}
        return settings.get("models", {}).get(area, {}).get("max_tokens", 4096)
    except Exception:
        return 4096


def _call_gemini(model: str, messages: list, system: str = None,
                 max_tokens: int = 4096, temperature: float = 0.7) -> SimpleNamespace:
    """Call Google Gemini via REST API (no SDK dependency).

    Retries up to 3 times with exponential backoff on 5xx errors and timeouts.
    4xx errors are returned immediately (real errors like bad API key).
    """
    api_key = os.environ.get("GOOGLE_AI_API_KEY")
    if not api_key:
        return SimpleNamespace(ok=False, text="", cost_usd=0.0, error="GOOGLE_AI_API_KEY not set")

    # Convert Anthropic-style messages to Gemini format
    contents = []
    for msg in messages:
        role = "user" if msg["role"] == "user" else "model"
        text = msg["content"] if isinstance(msg["content"], str) else str(msg["content"])
        contents.append({"role": role, "parts": [{"text": text}]})

    body: dict = {
        "contents": contents,
        "generationConfig": {
            "maxOutputTokens": max_tokens,
            "temperature": temperature,
        },
    }

    # Add system instruction if provided
    if system:
        body["systemInstruction"] = {"parts": [{"text": system}]}

    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"

    req = urllib.request.Request(
        url,
        data=json.dumps(body).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    max_retries = 3
    for attempt in range(max_retries):
        try:
            with urllib.request.urlopen(req, timeout=120) as resp:
                result = json.loads(resp.read())

            # Extract text from response
            candidates = result.get("candidates", [])
            if not candidates:
                return SimpleNamespace(ok=False, text="", cost_usd=0.0, error="No candidates in Gemini response")

            parts = candidates[0].get("content", {}).get("parts", [])
            text = "".join(p.get("text", "") for p in parts)

            # Extract token usage
            usage = result.get("usageMetadata", {})
            input_tokens = usage.get("promptTokenCount", 0)
            output_tokens = usage.get("candidatesTokenCount", 0)
            cost = _estimate_cost(model, input_tokens, output_tokens)

            return SimpleNamespace(ok=True, text=text, cost_usd=cost, error=None)

        except urllib.error.HTTPError as e:
            if e.code >= 500 and attempt < max_retries - 1:
                wait = 2 ** attempt  # exponential backoff: 1s, 2s, 4s
                logger.warning("Gemini HTTP %d on attempt %d — retrying in %ds", e.code, attempt + 1, wait)
                time.sleep(wait)
                continue
            return SimpleNamespace(ok=False, text="", cost_usd=0.0, error=f"Gemini HTTP {e.code}: {e.reason}")

        except (urllib.error.URLError, TimeoutError) as e:
            if attempt < max_retries - 1:
                wait = 2 ** attempt
                logger.warning("Gemini timeout/network on attempt %d — retrying in %ds: %s", attempt + 1, wait, e)
                time.sleep(wait)
                continue
            return SimpleNamespace(ok=False, text="", cost_usd=0.0, error=f"Gemini timeout/network: {e}")

        except Exception as e:
            return SimpleNamespace(ok=False, text="", cost_usd=0.0, error=str(e))

    # Should not be reached, but safety net
    return SimpleNamespace(ok=False, text="", cost_usd=0.0, error="Gemini: max retries exceeded")


def _call_anthropic(model: str, messages: list, system: str = None,
                    max_tokens: int = 4096, temperature: float = 0.7) -> SimpleNamespace:
    """Call Anthropic Claude."""
    kwargs = {
        "model": model,
        "max_tokens": max_tokens,
        "messages": messages,
        "temperature": temperature,
    }
    if system:
        kwargs["system"] = system

    try:
        client = _get_anthropic_client()
        response = client.messages.create(**kwargs)
        text = response.content[0].text if response.content else ""
        input_tokens = response.usage.input_tokens
        output_tokens = response.usage.output_tokens
        cost = _estimate_cost(model, input_tokens, output_tokens)
        return SimpleNamespace(ok=True, text=text, cost_usd=cost, error=None)
    except Exception as e:
        return SimpleNamespace(ok=False, text="", cost_usd=0.0, error=str(e))


def chat(area: str, messages: list, system: str = None,
         max_tokens: int = 4096, temperature: float = 0.7) -> SimpleNamespace:
    """Route to Gemini (preferred for research) or Anthropic (fallback).

    Uses Gemini for research areas when GOOGLE_AI_API_KEY is available.
    Falls back to Anthropic if Gemini fails or key is missing.
    """
    # Try Gemini first for research areas
    if _has_gemini_key() and area in GEMINI_AREA_MODELS:
        model = GEMINI_AREA_MODELS[area]
        result = _call_gemini(model, messages, system, max_tokens, temperature)
        if result.ok:
            return result
        # Gemini failed — log to gateway.log and fall back to Anthropic
        logger.warning(
            "Gemini call failed for area=%s model=%s, falling back to Anthropic: %s",
            area, model, result.error,
        )

    # Anthropic fallback (or primary if no Gemini key)
    model = ANTHROPIC_AREA_MODELS.get(area, "claude-sonnet-4-6")
    return _call_anthropic(model, messages, system, max_tokens, temperature)
