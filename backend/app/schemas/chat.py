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


class CreateThreadRequest(BaseModel):
    title: str | None = None


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


class SendMessageResponse(BaseModel):
    user_message: MessageOut
    assistant_message: MessageOut
