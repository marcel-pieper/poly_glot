from datetime import datetime
from typing import Any

from pydantic import BaseModel


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


class ExplainThreadSeed(BaseModel):
    source_thread_id: int
    source_message_id: int


class MessageOut(BaseModel):
    id: int
    thread_id: int
    role: str
    content: dict[str, Any]
    created_at: datetime

    model_config = {"from_attributes": True}


class MessageListResponse(BaseModel):
    messages: list[MessageOut]


class SendMessageRequest(BaseModel):
    text: str
    thread_id: int | None = None


class ExplainSendMessageRequest(BaseModel):
    text: str
    thread_id: int | None = None
    seed: ExplainThreadSeed | None = None


class SendMessageResponse(BaseModel):
    thread_id: int | None = None
    user_message: MessageOut
    assistant_message: MessageOut
