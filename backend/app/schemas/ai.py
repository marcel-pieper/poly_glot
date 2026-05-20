from datetime import datetime

from pydantic import BaseModel, Field


class TranslateRequest(BaseModel):
    text: str = Field(min_length=1, max_length=4000)


class TranslateItem(BaseModel):
    """Item returned to the client.

    `lemma_translation` is intentionally omitted: it is extracted, logged, and
    stored server-side, but the v1 UI only displays raw item, raw item
    translation, and the lemma.
    """

    type: str
    raw_item: str
    raw_item_translation: str
    lemma: str


class TranslateResponse(BaseModel):
    translation_id: int | None = None
    source_text: str
    translated_text: str
    status: str
    items: list[TranslateItem] = []


class TranslationSummary(BaseModel):
    id: int
    source_text: str
    translated_text: str
    from_language: str
    to_language: str
    created_at: datetime

    model_config = {"from_attributes": True}


class TranslationListResponse(BaseModel):
    translations: list[TranslationSummary]
    total: int
