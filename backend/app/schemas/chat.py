from datetime import datetime
from typing import Any

from pydantic import AliasChoices, BaseModel, Field, model_validator


class ThreadOut(BaseModel):
    id: int
    language_space_id: int
    title: str | None
    type: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ThreadListResponse(BaseModel):
    threads: list[ThreadOut]
    total: int


class GenerateThreadTitleResponse(BaseModel):
    title: str
    generated: bool


class ExplainThreadSeed(BaseModel):
    source_thread_id: int
    source_message_id: int


class MessageOut(BaseModel):
    id: int
    thread_id: int
    role: str
    content: dict[str, Any]
    created_at: datetime
    metadata: dict[str, Any] | None = Field(
        default=None,
        validation_alias=AliasChoices("metadata_json", "metadata"),
        serialization_alias="metadata",
    )

    model_config = {"from_attributes": True, "populate_by_name": True}


class MessageListResponse(BaseModel):
    messages: list[MessageOut]


class SendMessageRequest(BaseModel):
    text: str | None = None
    starter_id: str | None = None
    thread_id: int | None = None

    @model_validator(mode="after")
    def xor_text_or_starter(self):
        text_ok = bool(self.text and self.text.strip())
        starter_ok = bool(self.starter_id and self.starter_id.strip())
        if text_ok == starter_ok:
            raise ValueError("Provide exactly one of non-empty text or starter_id")
        return self


class ConversationStarterItem(BaseModel):
    id: str
    display_text: str


class ConversationStartersResponse(BaseModel):
    starters: list[ConversationStarterItem]


class ExplainSendMessageRequest(BaseModel):
    text: str
    thread_id: int | None = None
    seed: ExplainThreadSeed | None = None


class SendMessageResponse(BaseModel):
    thread_id: int | None = None
    user_message: MessageOut
    assistant_message: MessageOut
