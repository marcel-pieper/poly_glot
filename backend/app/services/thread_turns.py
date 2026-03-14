from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.language_space import LanguageSpace
from app.models.message import Message, MessageRole
from app.models.supported_language import SupportedLanguage
from app.models.thread import Thread
from app.models.user import User


def create_pending_user_message(db: Session, thread_id: int, text: str) -> Message:
    user_msg = Message(
        thread_id=thread_id,
        role=MessageRole.USER,
        content={"text": text, "correction_status": "pending", "correction": None},
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
    ai_content: dict,
) -> tuple[Message, Message]:
    user_msg.content = {
        "text": input_text,
        "correction_status": ai_content.get("status", "failed"),
        "correction": ai_content.get("correction"),
    }

    assistant_msg = Message(
        thread_id=thread.id,
        role=MessageRole.ASSISTANT,
        content={"assistant_response": ai_content.get("assistant_response", "")},
    )
    db.add(assistant_msg)

    thread.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(user_msg)
    db.refresh(assistant_msg)
    return user_msg, assistant_msg
