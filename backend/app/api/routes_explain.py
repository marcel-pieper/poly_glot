import logging
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.deps import current_user
from app.api.thread_access import require_user_thread
from app.db.session import get_db
from app.models.language_space import LanguageSpace
from app.models.message import Message, MessageRole
from app.models.supported_language import SupportedLanguage
from app.models.thread import Thread, ThreadType
from app.models.user import User
from app.schemas.chat import (
    CreateExplainThreadRequest,
    MessageListResponse,
    MessageOut,
    SendMessageRequest,
    SendMessageResponse,
    ThreadListResponse,
    ThreadOut,
)
from app.services.openai_service import get_explain_turn

router = APIRouter(prefix="/explain", tags=["explain"])
logger = logging.getLogger("polyglot.explain")


@router.post("/threads", response_model=ThreadOut, status_code=status.HTTP_201_CREATED)
def create_explain_thread(
    payload: CreateExplainThreadRequest,
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
):
    source_thread = require_user_thread(payload.source_thread_id, user, db)

    source_message = (
        db.execute(
            select(Message)
            .where(Message.id == payload.source_message_id)
            .where(Message.thread_id == source_thread.id)
        )
        .scalars()
        .first()
    )
    if not source_message:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Source message not found")
    if source_message.role != MessageRole.USER:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Source message must be a user message")

    source_content = source_message.content if isinstance(source_message.content, dict) else {}
    seed = {
        "source_thread_id": source_thread.id,
        "source_message_id": source_message.id,
        "source_text": source_content.get("text", ""),
        "correction": source_content.get("correction"),
    }

    thread = Thread(
        language_space_id=source_thread.language_space_id,
        parent_thread_id=source_thread.id,
        type=ThreadType.EXPLAIN,
        title=payload.title,
        seed=seed,
    )
    db.add(thread)
    db.commit()
    db.refresh(thread)
    logger.info("Explain thread %s created from source thread %s", thread.id, source_thread.id)
    return thread


@router.get("/threads", response_model=ThreadListResponse)
def list_explain_threads(
    limit: int = 50,
    offset: int = 0,
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
):
    base_q = (
        select(Thread)
        .join(LanguageSpace, Thread.language_space_id == LanguageSpace.id)
        .where(LanguageSpace.user_id == user.id)
        .where(Thread.type == ThreadType.EXPLAIN)
    )
    total: int = db.execute(select(func.count()).select_from(base_q.subquery())).scalar_one()
    threads = db.execute(base_q.order_by(Thread.id.desc()).limit(limit).offset(offset)).scalars().all()
    return ThreadListResponse(threads=list(threads), total=total)


@router.get("/threads/{thread_id}/messages", response_model=MessageListResponse)
def list_explain_messages(
    thread_id: int,
    limit: int = 50,
    offset: int = 0,
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
):
    thread = require_user_thread(thread_id, user, db, required_type=ThreadType.EXPLAIN)

    messages = (
        db.execute(
            select(Message)
            .where(Message.thread_id == thread_id)
            .order_by(Message.id.asc())
            .limit(limit)
            .offset(offset)
        )
        .scalars()
        .all()
    )
    return MessageListResponse(messages=list(messages))


@router.post("/threads/{thread_id}/messages", response_model=SendMessageResponse, status_code=status.HTTP_201_CREATED)
def send_explain_message(
    thread_id: int,
    payload: SendMessageRequest,
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
):
    thread = require_user_thread(thread_id, user, db, required_type=ThreadType.EXPLAIN)

    user_msg = Message(
        thread_id=thread_id,
        role=MessageRole.USER,
        content={"text": payload.text, "correction_status": "pending", "correction": None},
    )
    db.add(user_msg)
    db.flush()

    history = (
        db.execute(select(Message).where(Message.thread_id == thread_id).order_by(Message.id.asc()).limit(20))
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

    ai_content = get_explain_turn(
        history=[{"role": m.role.value, "content": m.content} for m in history],
        seed=thread.seed,
        target_language=target_lang_code,
        native_language=native_lang_code,
    )

    user_msg.content = {
        "text": payload.text,
        "correction_status": ai_content.get("status", "failed"),
        "correction": ai_content.get("correction"),
    }

    assistant_msg = Message(
        thread_id=thread_id,
        role=MessageRole.ASSISTANT,
        content={"assistant_response": ai_content.get("assistant_response", "")},
    )
    db.add(assistant_msg)

    thread.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(user_msg)
    db.refresh(assistant_msg)
    logger.info("Explain message pair persisted for thread %s", thread_id)
    return SendMessageResponse(
        user_message=MessageOut.model_validate(user_msg, from_attributes=True),
        assistant_message=MessageOut.model_validate(assistant_msg, from_attributes=True),
    )
