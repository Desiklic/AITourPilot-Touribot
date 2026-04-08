"""Simple model gateway for research — routes to Anthropic.

All research uses Anthropic models only (no Google SDK dependency).
"""
import os
from types import SimpleNamespace

import anthropic

_client = None


def _get_client() -> anthropic.Anthropic:
    global _client
    if _client is None:
        try:
            from dotenv import load_dotenv
            from pathlib import Path
            load_dotenv(Path(__file__).parent.parent.parent / ".env")
        except ImportError:
            pass
        _client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))
    return _client


AREA_MODELS = {
    "fast_research": "claude-haiku-4-5-20251001",
    "research": "claude-sonnet-4-6",
    "deep_research": "claude-sonnet-4-6",
}

# Approximate costs per million tokens (input, output) by model
_MODEL_COSTS = {
    "claude-haiku-4-5-20251001": (0.80, 4.00),      # $0.80 / $4.00 per MTok
    "claude-sonnet-4-6":        (3.00, 15.00),       # $3.00 / $15.00 per MTok
}


def _estimate_cost(model: str, input_tokens: int, output_tokens: int) -> float:
    """Return estimated USD cost for a call."""
    cost_in, cost_out = _MODEL_COSTS.get(model, (3.00, 15.00))
    return (input_tokens * cost_in + output_tokens * cost_out) / 1_000_000


def chat(area: str, messages: list, system: str = None,
         max_tokens: int = 4096, temperature: float = 0.7) -> SimpleNamespace:
    """Call Anthropic and return a SimpleNamespace with ok, text, cost_usd."""
    model = AREA_MODELS.get(area, "claude-sonnet-4-6")
    kwargs = {
        "model": model,
        "max_tokens": max_tokens,
        "messages": messages,
        "temperature": temperature,
    }
    if system:
        kwargs["system"] = system

    try:
        client = _get_client()
        response = client.messages.create(**kwargs)
        text = response.content[0].text if response.content else ""
        input_tokens = response.usage.input_tokens
        output_tokens = response.usage.output_tokens
        cost = _estimate_cost(model, input_tokens, output_tokens)
        return SimpleNamespace(ok=True, text=text, cost_usd=cost, error=None)
    except Exception as e:
        return SimpleNamespace(ok=False, text="", cost_usd=0.0, error=str(e))
