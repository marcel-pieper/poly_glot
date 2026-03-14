import logging

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
    ExplainSendMessageRequest,
    MessageListResponse,
    MessageOut,
    SendMessageResponse,
    ThreadListResponse,
)
from app.services.openai_service import get_explain_turn
from app.services.thread_turns import (
    build_llm_history,
    create_pending_user_message,
    finalize_turn,
    load_thread_history,
    resolve_language_codes,
)

router = APIRouter(prefix="/explain", tags=["explain"])
logger = logging.getLogger("polyglot.explain")


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
    require_user_thread(thread_id, user, db, required_type=ThreadType.EXPLAIN)

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


@router.post("/messages", response_model=SendMessageResponse, status_code=status.HTTP_201_CREATED)
def send_explain_message(
    payload: ExplainSendMessageRequest,
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
):
    thread_id = payload.thread_id
    if thread_id is not None:
        if payload.seed is not None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="seed must not be provided when thread_id is set",
            )
        thread = require_user_thread(thread_id, user, db, required_type=ThreadType.EXPLAIN)
    else:
        if payload.seed is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="seed is required when starting a new explain thread",
            )
        source_thread = require_user_thread(
            payload.seed.source_thread_id,
            user,
            db,
            required_type=ThreadType.CHAT,
        )
        source_message = (
            db.execute(
                select(Message)
                .where(Message.id == payload.seed.source_message_id)
                .where(Message.thread_id == source_thread.id)
            )
            .scalars()
            .first()
        )
        if not source_message:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Source message not found")
        if source_message.role != MessageRole.USER:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Source message must be a user message",
            )

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
            title=None,
            seed=seed,
        )
        db.add(thread)
        db.flush()
        thread_id = thread.id
        logger.info("Explain thread %s created from source thread %s", thread.id, source_thread.id)

    user_msg = create_pending_user_message(db, thread_id=thread_id, text=payload.text)
    history = load_thread_history(db, thread_id=thread_id, limit=20)
    target_lang_code, native_lang_code = resolve_language_codes(db, thread=thread, user=user)

    ai_content = get_explain_turn(
        history=build_llm_history(history),
        seed=thread.seed,
        target_language=target_lang_code,
        native_language=native_lang_code,
    )

    user_msg, assistant_msg = finalize_turn(
        db,
        thread=thread,
        user_msg=user_msg,
        input_text=payload.text,
        ai_content=ai_content,
    )
    logger.info("Explain message pair persisted for thread %s", thread_id)
    return SendMessageResponse(
        thread_id=thread_id,
        user_message=MessageOut.model_validate(user_msg, from_attributes=True),
        assistant_message=MessageOut.model_validate(assistant_msg, from_attributes=True),
    )
