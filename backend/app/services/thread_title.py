from __future__ import annotations

from app.models.message import Message, MessageRole


def user_message_is_starter_turn(msg: Message) -> bool:
    if msg.role != MessageRole.USER:
        return False
    meta = msg.metadata_json
    return isinstance(meta, dict) and bool(meta.get("starter_id"))


def history_has_non_starter_user_message(history: list[Message]) -> bool:
    return any(m.role == MessageRole.USER and not user_message_is_starter_turn(m) for m in history)


def build_conversation_lines_for_title(history: list[Message]) -> list[str]:
    """Turn the first chunk of thread messages into labeled lines for the title model."""
    lines: list[str] = []
    for m in history:
        if m.role == MessageRole.USER:
            if user_message_is_starter_turn(m):
                continue
            content = m.content if isinstance(m.content, dict) else {}
            text = str(content.get("text") or "").strip()
            if text:
                lines.append(f"User: {text}")
        elif m.role == MessageRole.ASSISTANT:
            content = m.content if isinstance(m.content, dict) else {}
            text = str(content.get("assistant_response") or "").strip()
            if text:
                lines.append(f"Assistant: {text}")
    return lines
