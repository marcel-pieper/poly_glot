import logging
from concurrent.futures import ThreadPoolExecutor

from fastapi import APIRouter, Depends, HTTPException, Response, status
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
    ConversationStarterItem,
    ConversationStartersResponse,
    GenerateThreadTitleResponse,
    MessageListResponse,
    MessageOut,
    SendMessageRequest,
    SendMessageResponse,
    ThreadListResponse,
)
from app.services.chat_starters import ChatStarterError, list_starters_for_api, resolve_starter_message_text
from app.services.openai_service import get_chat_reply, get_chat_thread_title, get_message_correction
from app.services.thread_title import (
    build_conversation_lines_for_title,
    history_has_non_starter_user_message,
)
from app.services.thread_turns import (
    build_correction_context,
    build_llm_history,
    create_pending_user_message,
    finalize_turn,
    load_thread_history,
    resolve_language_codes,
)

router = APIRouter(prefix="/chat", tags=["chat"])
logger = logging.getLogger("polyglot.chat")


@router.get("/conversation-starters", response_model=ConversationStartersResponse)
def get_conversation_starters(
    response: Response,
    _user: User = Depends(current_user),
):
    """Client-facing starters (id + label). Starter prompt text stays server-side."""
    response.headers["Cache-Control"] = "private, max-age=3600"
    rows = list_starters_for_api()
    return ConversationStartersResponse(starters=[ConversationStarterItem(**r) for r in rows])


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
            .where(Message.metadata_json["starter_id"].is_(None))
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


@router.post(
    "/threads/{thread_id}/generate-title",
    response_model=GenerateThreadTitleResponse,
    status_code=status.HTTP_200_OK,
)
def generate_thread_title(
    thread_id: int,
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
):
    thread = require_user_thread(thread_id, user, db, required_type=ThreadType.CHAT)
    if thread.title:
        return GenerateThreadTitleResponse(title=thread.title, generated=False)

    history = load_thread_history(db, thread_id=thread_id, limit=20)
    if not history_has_non_starter_user_message(history):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No user-written messages yet; nothing to title",
        )

    lines = build_conversation_lines_for_title(history)
    title = get_chat_thread_title(lines)
    if not title:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Could not generate a title right now",
        )

    thread.title = title
    db.add(thread)
    db.commit()
    db.refresh(thread)
    return GenerateThreadTitleResponse(title=title, generated=True)


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


@router.delete("/threads/{thread_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_thread(
    thread_id: int,
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
):
    thread = require_user_thread(thread_id, user, db, required_type=ThreadType.CHAT)
    db.delete(thread)
    db.commit()


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

    if payload.thread_id is not None and payload.starter_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="conversation starters can only begin a new thread (omit thread_id)",
        )

    msg_metadata = None
    if payload.starter_id:
        sid = payload.starter_id.strip()
        try:
            effective_text = resolve_starter_message_text(sid)
        except ChatStarterError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="unknown starter_id",
            ) from None
        msg_metadata = {"starter_id": sid}
    else:
        effective_text = (payload.text or "").strip()

    user_msg = create_pending_user_message(
        db,
        thread_id=thread_id,
        text=effective_text,
        metadata=msg_metadata,
    )

    history = load_thread_history(db, thread_id=thread_id, limit=20)
    llm_history = build_llm_history(history)
    target_lang_code, native_lang_code = resolve_language_codes(db, thread=thread, user=user)
    is_starter_turn = isinstance((msg_metadata or {}).get("starter_id"), str)

    logger.info(
        "Calling OpenAI for thread %s (target=%s native=%s starter=%s)",
        thread_id,
        target_lang_code,
        native_lang_code,
        is_starter_turn,
    )

    if is_starter_turn:
        response_result = get_chat_reply(
            history=llm_history,
            target_language=target_lang_code,
            native_language=native_lang_code,
        )
        correction_result = {"correction": None, "status": "complete"}
    else:
        message_to_correct, prior_exchange = build_correction_context(history)
        with ThreadPoolExecutor(max_workers=2) as executor:
            correction_future = executor.submit(
                get_message_correction,
                message_to_correct,
                prior_exchange,
                target_lang_code,
                native_lang_code,
            )
            response_future = executor.submit(
                get_chat_reply,
                llm_history,
                target_lang_code,
                native_lang_code,
            )
            correction_result = correction_future.result()
            response_result = response_future.result()

    logger.info("Correction result: %s", correction_result)
    logger.info("Response result: %s", response_result)

    user_msg, assistant_msg = finalize_turn(
        db,
        thread=thread,
        user_msg=user_msg,
        input_text=effective_text,
        correction_result=correction_result,
        response_result=response_result,
    )

    logger.info("Message pair persisted for thread %s", thread_id)
    return SendMessageResponse(
        thread_id=thread_id,
        user_message=MessageOut.model_validate(user_msg, from_attributes=True),
        assistant_message=MessageOut.model_validate(assistant_msg, from_attributes=True),
    )

