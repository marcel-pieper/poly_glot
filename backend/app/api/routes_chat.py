import logging
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.deps import current_user
from app.db.session import get_db
from app.models.language_space import LanguageSpace
from app.models.message import Message, MessageRole
from app.models.supported_language import SupportedLanguage
from app.models.thread import Thread, ThreadType
from app.models.user import User
from app.schemas.chat import (
    CreateThreadRequest,
    MessageListResponse,
    MessageOut,
    SendMessageRequest,
    SendMessageResponse,
    ThreadListResponse,
    ThreadOut,
)
from app.services.openai_service import get_chat_turn

router = APIRouter(prefix="/chat", tags=["chat"])
logger = logging.getLogger("polyglot.chat")


def _require_user_thread(thread_id: int, user: User, db: Session) -> Thread:
    """Return thread if owned by user, otherwise raise 403/404."""
    thread = db.get(Thread, thread_id)
    if not thread:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Thread not found")
    space = db.get(LanguageSpace, thread.language_space_id)
    if not space or space.user_id != user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
    return thread


@router.post("/threads", response_model=ThreadOut, status_code=status.HTTP_201_CREATED)
def create_thread(
    payload: CreateThreadRequest,
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
):
    thread = Thread(
        language_space_id=user.active_language_space_id,
        type=ThreadType.CHAT,
        title=payload.title,
    )
    db.add(thread)
    db.commit()
    db.refresh(thread)
    logger.info("Thread %s created for user %s", thread.id, user.id)
    return thread


@router.get("/threads", response_model=ThreadListResponse)
def list_threads(
    limit: int = 50,
    offset: int = 0,
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
):
    base_q = (
        select(Thread)
        .join(LanguageSpace, Thread.language_space_id == LanguageSpace.id)
        .where(LanguageSpace.user_id == user.id)
        .where(Thread.type == ThreadType.CHAT)
    )
    total: int = db.execute(select(func.count()).select_from(base_q.subquery())).scalar_one()
    threads = (
        db.execute(base_q.order_by(Thread.updated_at.desc()).limit(limit).offset(offset))
        .scalars()
        .all()
    )
    return ThreadListResponse(threads=list(threads), total=total)


@router.get("/threads/{thread_id}/messages", response_model=MessageListResponse)
def list_messages(
    thread_id: int,
    limit: int = 50,
    offset: int = 0,
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
):
    _require_user_thread(thread_id, user, db)
    messages = (
        db.execute(
            select(Message)
            .where(Message.thread_id == thread_id)
            .order_by(Message.created_at.asc())
            .limit(limit)
            .offset(offset)
        )
        .scalars()
        .all()
    )
    return MessageListResponse(messages=list(messages))


@router.post(
    "/threads/{thread_id}/messages",
    response_model=SendMessageResponse,
    status_code=status.HTTP_201_CREATED,
)
def send_message(
    thread_id: int,
    payload: SendMessageRequest,
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
):
    thread = _require_user_thread(thread_id, user, db)
    if thread.type != ThreadType.CHAT:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Thread is not a chat thread",
        )

    user_msg = Message(
        thread_id=thread_id,
        role=MessageRole.USER,
        content={"text": payload.text},
    )
    db.add(user_msg)
    db.flush()

    history = (
        db.execute(
            select(Message)
            .where(Message.thread_id == thread_id)
            .order_by(Message.created_at.asc())
            .limit(20)
        )
        .scalars()
        .all()
    )

    space = db.get(LanguageSpace, thread.language_space_id)
    target_lang_code: str | None = None
    native_lang_code: str | None = None
    if space:
        target_lang = db.get(SupportedLanguage, space.target_language_id)
        if target_lang:
            target_lang_code = target_lang.code
    if user.native_language_id:
        native_lang = db.get(SupportedLanguage, user.native_language_id)
        if native_lang:
            native_lang_code = native_lang.code

    logger.info(
        "Calling OpenAI for thread %s (target=%s native=%s)",
        thread_id,
        target_lang_code,
        native_lang_code,
    )
    ai_content = get_chat_turn(
        history=[{"role": m.role.value, "content": m.content} for m in history],
        target_language=target_lang_code,
        native_language=native_lang_code,
    )

    assistant_msg = Message(
        thread_id=thread_id,
        role=MessageRole.ASSISTANT,
        content=ai_content,
    )
    db.add(assistant_msg)

    thread.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(user_msg)
    db.refresh(assistant_msg)

    logger.info("Message pair persisted for thread %s", thread_id)
    return SendMessageResponse(
        user_message=MessageOut.model_validate(user_msg, from_attributes=True),
        assistant_message=MessageOut.model_validate(assistant_msg, from_attributes=True),
    )
