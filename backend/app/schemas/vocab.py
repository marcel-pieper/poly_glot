from datetime import datetime

from pydantic import BaseModel, Field


class AddVocabRequest(BaseModel):
    """Add an item to the user's vocab.

    The server resolves the lemma row by `(active space's target language,
    lemma, type)`, creating it if needed, so the client never has to know the
    `lemma_id`.
    """

    lemma: str = Field(min_length=1, max_length=255)
    type: str = Field(min_length=1, max_length=32)


class VocabItem(BaseModel):
    id: int
    lemma_id: int
    lemma: str
    type: str
    language: str
    glosses: list[str] = []
    state: int
    due: datetime
    last_review: datetime | None = None
    review_count: int
    lapse_count: int
    is_due: bool

    model_config = {"from_attributes": True}


class VocabListResponse(BaseModel):
    items: list[VocabItem]
    total: int
    due_count: int


class AddVocabResponse(BaseModel):
    item: VocabItem
    created: bool
