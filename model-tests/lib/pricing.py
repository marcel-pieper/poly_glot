from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PRICING_PATH = ROOT / "pricing.yaml"


def load_pricing(path: Path | None = None) -> dict[str, dict[str, float]]:
    pricing_path = path or DEFAULT_PRICING_PATH
    with pricing_path.open(encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    return {str(k): v for k, v in data.items() if isinstance(v, dict)}


def usage_dict(usage: Any) -> dict[str, int]:
    if usage is None:
        return {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0, "reasoning_tokens": 0}

    prompt = int(getattr(usage, "prompt_tokens", 0) or 0)
    completion = int(getattr(usage, "completion_tokens", 0) or 0)
    total = int(getattr(usage, "total_tokens", 0) or 0) or (prompt + completion)

    reasoning = 0
    details = getattr(usage, "completion_tokens_details", None)
    if details is not None:
        reasoning = int(getattr(details, "reasoning_tokens", 0) or 0)

    return {
        "prompt_tokens": prompt,
        "completion_tokens": completion,
        "total_tokens": total,
        "reasoning_tokens": reasoning,
    }


def estimate_cost_usd(model: str, usage: dict[str, int], pricing: dict[str, dict[str, float]]) -> float | None:
    rates = pricing.get(model)
    if not rates:
        return None

    input_rate = float(rates.get("input", 0))
    output_rate = float(rates.get("output", 0))
    prompt_tokens = usage.get("prompt_tokens", 0)
    # Bill completion + reasoning tokens at output rate (conservative for reasoning models).
    output_tokens = usage.get("completion_tokens", 0) + usage.get("reasoning_tokens", 0)

    return (prompt_tokens / 1_000_000) * input_rate + (output_tokens / 1_000_000) * output_rate
