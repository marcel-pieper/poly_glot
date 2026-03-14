import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.deps import current_user
from app.api.thread_access import require_user_thread
from app.db.session import get_db
from app.models.language_space import LanguageSpace
from app.models.message import Message, MessageRole
from app.models.thread import Thread, ThreadType
from app.models.user import User
from app.schemas.chat import (
    MessageListResponse,
    MessageOut,
    SendMessageRequest,
    SendMessageResponse,
    ThreadListResponse,
)
from app.services.openai_service import get_chat_turn
from app.services.thread_turns import (
    build_llm_history,
    create_pending_user_message,
    finalize_turn,
    load_thread_history,
    resolve_language_codes,
)

router = APIRouter(prefix="/chat", tags=["chat"])
logger = logging.getLogger("polyglot.chat")


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
        .where(
            select(Message.id)
            .where(Message.thread_id == Thread.id)
            .where(Message.role == MessageRole.USER)
            .exists()
        )
    )
    total: int = db.execute(select(func.count()).select_from(base_q.subquery())).scalar_one()
    threads = (
        db.execute(base_q.order_by(Thread.id.desc()).limit(limit).offset(offset))
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
    require_user_thread(thread_id, user, db, required_type=ThreadType.CHAT)
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
def send_message(
    payload: SendMessageRequest,
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
):
    thread_id = payload.thread_id
    if thread_id is not None:
        thread = require_user_thread(thread_id, user, db, required_type=ThreadType.CHAT)
    else:
        if not user.active_language_space_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Set an active learning language before starting a chat",
            )
        thread = Thread(
            language_space_id=user.active_language_space_id,
            type=ThreadType.CHAT,
            title=None,
        )
        db.add(thread)
        db.flush()
        thread_id = thread.id
        logger.info("Thread %s created for user %s", thread_id, user.id)

    user_msg = create_pending_user_message(db, thread_id=thread_id, text=payload.text)
    history = load_thread_history(db, thread_id=thread_id, limit=20)
    target_lang_code, native_lang_code = resolve_language_codes(db, thread=thread, user=user)

    logger.info(
        "Calling OpenAI for thread %s (target=%s native=%s)",
        thread_id,
        target_lang_code,
        native_lang_code,
    )
    ai_content = get_chat_turn(
        history=build_llm_history(history),
        target_language=target_lang_code,
        native_language=native_lang_code,
    )
    logger.info("AI content: %s", ai_content)

    user_msg, assistant_msg = finalize_turn(
        db,
        thread=thread,
        user_msg=user_msg,
        input_text=payload.text,
        ai_content=ai_content,
    )

    logger.info("Message pair persisted for thread %s", thread_id)
    return SendMessageResponse(
        thread_id=thread_id,
        user_message=MessageOut.model_validate(user_msg, from_attributes=True),
        assistant_message=MessageOut.model_validate(assistant_msg, from_attributes=True),
    )
