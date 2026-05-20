"""Translation item extraction: pull phrases/words/verbs out of a translation pair.

Pipeline:
  1. Call the model with both source and translated text to get structured items.
  2. Append the full raw result to a JSONL log for QA.
  3. Upsert into `lemmas` and `lemma_translations` so the global inventory grows.

The API layer hides `lemma_translation` from the client for now, but it is still
extracted, persisted, and logged so the future "see all meanings" view has data.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from openai import OpenAI
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.logging_config import BACKEND_DIR
from app.models.lemma import Lemma, LemmaTranslation

settings = get_settings()
logger = logging.getLogger("polyglot.extraction")

VALID_TYPES = {"phrase", "noun", "verb", "other"}
MAX_ITEMS_PER_TRANSLATION = 10


def _extractions_log_path() -> Path:
    log_dir = Path(settings.log_dir)
    if not log_dir.is_absolute():
        log_dir = BACKEND_DIR / log_dir
    log_dir.mkdir(parents=True, exist_ok=True)
    return log_dir / "extractions.jsonl"


def _normalize_lemma(value: str) -> str:
    return value.strip()


def _coerce_item(raw: Any) -> dict | None:
    if not isinstance(raw, dict):
        return None
    item_type = str(raw.get("type", "")).strip().lower()
    if item_type not in VALID_TYPES:
        item_type = "other"
    raw_item = str(raw.get("raw_item", "")).strip()
    lemma = _normalize_lemma(str(raw.get("lemma", "")))
    if not raw_item or not lemma:
        return None
    return {
        "type": item_type,
        "raw_item": raw_item,
        "raw_item_translation": str(raw.get("raw_item_translation", "")).strip(),
        "lemma": lemma,
        "lemma_translation": str(raw.get("lemma_translation", "")).strip(),
    }


def extract_items(
    source_text: str,
    translated_text: str,
    source_language: str | None,
    gloss_language: str | None,
) -> list[dict]:
    """Ask the model to extract phrases/words/verbs from the source-language text.

    Returns a list of items shaped like:
      {type, raw_item, raw_item_translation, lemma, lemma_translation}
    Always returns a list; on failure returns []. Caller decides what to do.
    """
    if not translated_text.strip() or not source_text.strip():
        return []
    if not settings.openai_api_key:
        return []

    system_prompt = (
        "You extract vocabulary study items from a bilingual translation pair for Polyglot.\n"
        f"Source-language items come from {source_language or 'the source language'} "
        f"and their glosses are in {gloss_language or 'the translation language'}.\n\n"
        "Rules:\n"
        "- Extract notable PHRASES (multi-word expressions, idioms, useful chunks), "
        "NOUNS, and VERBS from the SOURCE text.\n"
        "- For verbs, `lemma` must be the infinitive form in the source language.\n"
        "- For nouns and other words, `lemma` is the dictionary headword "
        "(singular, no article).\n"
        "- For phrases, `lemma` is a normalized form of the chunk.\n"
        f"- Cap the list at {MAX_ITEMS_PER_TRANSLATION} items, prioritizing the most "
        "study-worthy entries.\n"
        "- Skip names, numbers, and trivial function words unless they form an idiom.\n"
        "- `raw_item` is the exact substring as it appears in the source text.\n"
        "- `raw_item_translation` is how that exact substring is rendered in the "
        "translation (use the corresponding span from the translated text).\n"
        "- `lemma_translation` is a short dictionary-style gloss in the gloss language.\n\n"
        "Return ONLY valid JSON of this shape:\n"
        "{\n"
        '  "items": [\n'
        "    {\n"
        '      "type": "phrase" | "noun" | "verb" | "other",\n'
        '      "raw_item": "...",\n'
        '      "raw_item_translation": "...",\n'
        '      "lemma": "...",\n'
        '      "lemma_translation": "..."\n'
        "    }\n"
        "  ]\n"
        "}"
    )

    user_prompt = (
        f"Source language: {source_language or 'unknown'}\n"
        f"Gloss language: {gloss_language or 'unknown'}\n\n"
        f"Source text:\n{source_text.strip()}\n\n"
        f"Translated text:\n{translated_text.strip()}"
    )

    try:
        client = OpenAI(api_key=settings.openai_api_key)
        response = client.chat.completions.create(
            model=settings.openai_model_translation,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            response_format={"type": "json_object"},
        )
        raw = response.choices[0].message.content or "{}"
        data = json.loads(raw)
    except Exception:
        logger.exception("Item extraction call failed")
        return []

    items_raw = data.get("items") if isinstance(data, dict) else None
    if not isinstance(items_raw, list):
        return []

    cleaned: list[dict] = []
    for raw_item in items_raw[:MAX_ITEMS_PER_TRANSLATION]:
        item = _coerce_item(raw_item)
        if item is not None:
            cleaned.append(item)
    return cleaned


def log_extraction(
    translation_id: int | None,
    source_language: str | None,
    gloss_language: str | None,
    source_text: str,
    translated_text: str,
    items: list[dict],
) -> None:
    """Append the full extraction result to logs/extractions.jsonl (best effort)."""
    record = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "translation_id": translation_id,
        "source_language": source_language,
        "gloss_language": gloss_language,
        "model": settings.openai_model_translation,
        "source_text": source_text,
        "translated_text": translated_text,
        "items": items,
    }
    try:
        path = _extractions_log_path()
        with path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(record, ensure_ascii=False) + "\n")
    except Exception:
        logger.exception("Failed to write extraction log entry")


def get_or_create_lemma(
    db: Session,
    *,
    language: str,
    lemma: str,
    type: str,
) -> Lemma:
    """Find a lemma by (language, lemma, type) or create it.

    Caller is responsible for the surrounding transaction. Flushes so the
    returned row has its `id` populated.
    """
    row = db.execute(
        select(Lemma).where(
            Lemma.language == language,
            Lemma.lemma == lemma,
            Lemma.type == type,
        )
    ).scalar_one_or_none()
    if row is not None:
        return row
    row = Lemma(language=language, lemma=lemma, type=type)
    db.add(row)
    db.flush()
    return row


def add_lemma_translation_if_new(
    db: Session,
    *,
    lemma_id: int,
    gloss_language: str,
    translation: str,
) -> None:
    """Insert a `LemmaTranslation` row if the (lemma, gloss_language, text)
    triple is not already present. No-op when `translation` is empty."""
    text = translation.strip()
    if not text:
        return
    exists = db.execute(
        select(LemmaTranslation.id).where(
            LemmaTranslation.lemma_id == lemma_id,
            LemmaTranslation.gloss_language == gloss_language,
            LemmaTranslation.translation == text,
        )
    ).scalar_one_or_none()
    if exists is None:
        db.add(
            LemmaTranslation(
                lemma_id=lemma_id,
                gloss_language=gloss_language,
                translation=text,
            )
        )


def persist_items(
    db: Session,
    items: list[dict],
    source_language: str,
    gloss_language: str,
) -> None:
    """Upsert into `lemmas` and insert-if-new into `lemma_translations`.

    Best-effort: a failure on one item does not abort the rest. Caller still
    owns the surrounding transaction's commit.
    """
    for item in items:
        # Savepoint per item so one bad row doesn't drop sibling inserts.
        try:
            with db.begin_nested():
                lemma_row = get_or_create_lemma(
                    db,
                    language=source_language,
                    lemma=item["lemma"],
                    type=item["type"],
                )
                add_lemma_translation_if_new(
                    db,
                    lemma_id=lemma_row.id,
                    gloss_language=gloss_language,
                    translation=item.get("lemma_translation", ""),
                )
        except Exception:
            logger.exception("Failed to persist extracted item: %s", item)
