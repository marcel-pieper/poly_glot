"""Load conversation starter definitions from app/chat_starters.json."""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

_DATA_PATH = Path(__file__).resolve().parent.parent / "chat_starters.json"


class ChatStarterError(KeyError):
    """Unknown starter id."""


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


def list_starters_for_api() -> list[dict]:
    """Return [{id, display_text}, ...] for the client."""
    rows: list[dict] = []
    for sid, cfg in sorted(raw_starters().items()):
        if not isinstance(cfg, dict):
            continue
        display = cfg.get("display_text")
        if isinstance(display, str):
            rows.append({"id": sid, "display_text": display})
    return rows


def starter_message_text(starter_id: str) -> str:
    cfg = raw_starters().get(starter_id)
    if not isinstance(cfg, dict):
        raise ChatStarterError(starter_id)
    text = cfg.get("starter_text")
    if not isinstance(text, str) or not text.strip():
        raise ChatStarterError(starter_id)
    return text.strip()


def invalidate_starters_cache() -> None:
    raw_starters.cache_clear()
