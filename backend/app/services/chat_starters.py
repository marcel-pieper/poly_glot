"""Load conversation starter definitions from app/chat_starters.json."""

from __future__ import annotations

import json
import random
from functools import lru_cache
from pathlib import Path

_DATA_PATH = Path(__file__).resolve().parent.parent / "chat_starters.json"


class ChatStarterError(KeyError):
    """Unknown starter id or starter cannot produce message text."""


def _starter_path() -> Path:
    return _DATA_PATH


@lru_cache(maxsize=1)
def raw_starters() -> dict[str, dict]:
    path = _starter_path()
    if not path.is_file():
        return {}
    with path.open(encoding="utf-8") as f:
        data = json.load(f)
        if not isinstance(data, dict):
            return {}
        return data


def _variant_pool(cfg: dict) -> list[str]:
    """Non-empty stripped strings from message_variants."""
    raw = cfg.get("message_variants")
    if not isinstance(raw, list):
        return []
    out: list[str] = []
    for x in raw:
        if isinstance(x, str) and x.strip():
            out.append(x.strip())
    return out


def list_starters_for_api() -> list[dict]:
    """Return [{id, display_text}, ...] for the client (only starters that can send)."""
    rows: list[dict] = []
    for sid, cfg in sorted(raw_starters().items()):
        if not isinstance(cfg, dict):
            continue
        display = cfg.get("display_text")
        if not isinstance(display, str) or not display.strip():
            continue
        if not _variant_pool(cfg):
            continue
        rows.append({"id": sid, "display_text": display.strip()})
    return rows


def resolve_starter_message_text(starter_id: str) -> str:
    """Pick one concrete user message for this starter (randomized across variants)."""
    cfg = raw_starters().get(starter_id)
    if not isinstance(cfg, dict):
        raise ChatStarterError(starter_id)
    pool = _variant_pool(cfg)
    if not pool:
        raise ChatStarterError(starter_id)
    return random.choice(pool)


def invalidate_starters_cache() -> None:
    raw_starters.cache_clear()
