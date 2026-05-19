from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.language_space import LanguageSpace
from app.models.message import Message, MessageRole
from app.models.supported_language import SupportedLanguage
from app.models.thread import Thread
from app.models.user import User


def create_pending_user_message(
    db: Session,
    thread_id: int,
    *,
    text: str,
    metadata: dict[str, Any] | None = None,
) -> Message:
    starter_id_present = isinstance(metadata, dict) and bool(metadata.get("starter_id"))

    content: dict[str, Any]
    if starter_id_present:
        content = {"text": text}
    else:
        content = {
            "text": text,
            "correction_status": "pending",
            "correction": None,
        }

    user_msg = Message(
        thread_id=thread_id,
        role=MessageRole.USER,
        content=content,
        metadata_json=metadata,
    )
    db.add(user_msg)
    db.flush()
    return user_msg


def load_thread_history(db: Session, thread_id: int, limit: int = 20) -> list[Message]:
    return (
        db.execute(
            select(Message)
            .where(Message.thread_id == thread_id)
            .order_by(Message.id.asc())
            .limit(limit)
        )
        .scalars()
        .all()
    )


def build_llm_history(history: list[Message]) -> list[dict]:
    return [{"role": m.role.value, "content": m.content} for m in history]


def build_correction_context(history: list[Message]) -> tuple[str, list[tuple[str, str]]]:
    """
    Return the latest user text and up to one prior user/assistant exchange for correction context.
    """
    entries: list[tuple[str, str]] = []
    for message in history:
        content = message.content if isinstance(message.content, dict) else {}
        if message.role == MessageRole.USER:
            entries.append(("user", str(content.get("text", ""))))
        elif message.role == MessageRole.ASSISTANT:
            entries.append(("assistant", str(content.get("assistant_response", ""))))

    if not entries or entries[-1][0] != "user":
        return "", []

    message_to_correct = entries[-1][1]
    prior: list[tuple[str, str]] = []
    for role, text in reversed(entries[:-1]):
        prior.insert(0, (role, text))
        if len(prior) >= 2:
            break
    return message_to_correct, prior


def resolve_language_codes(db: Session, thread: Thread, user: User) -> tuple[str | None, str | None]:
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
    return target_lang_code, native_lang_code


def finalize_turn(
    db: Session,
    *,
    thread: Thread,
    user_msg: Message,
    input_text: str,
    correction_result: dict[str, Any],
    response_result: dict[str, Any],
) -> tuple[Message, Message]:
    meta = user_msg.metadata_json or {}
    is_starter_turn = isinstance(meta.get("starter_id"), str)

    if is_starter_turn:
        user_msg.content = {"text": input_text}
    else:
        user_msg.content = {
            "text": input_text,
            "correction_status": correction_result.get("status", "failed"),
            "correction": correction_result.get("correction"),
        }

    assistant_msg = Message(
        thread_id=thread.id,
        role=MessageRole.ASSISTANT,
        content={
            "assistant_response": response_result.get("assistant_response", ""),
            "response_status": response_result.get("status", "failed"),
        },
    )
    db.add(assistant_msg)

    thread.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(user_msg)
    db.refresh(assistant_msg)
    return user_msg, assistant_msg
