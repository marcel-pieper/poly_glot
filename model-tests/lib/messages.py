"""Build OpenAI message lists using the same prompts as production."""

from __future__ import annotations

from app.services.openai_service import (
    _build_chat_openai_messages,
    make_system_chat_prompt,
    make_system_correction_prompt,
)


def correction_messages(
    message_to_correct: str,
    prior_exchange: list[list[str]],
    target_language: str | None,
    native_language: str | None,
) -> list[dict]:
    prior: list[tuple[str, str]] = [(str(p[0]), str(p[1])) for p in prior_exchange]
    cleaned = message_to_correct.strip()
    system_prompt = make_system_correction_prompt(target_language, native_language)
    openai_messages: list[dict] = [{"role": "system", "content": system_prompt}]
    for role, text in prior:
        openai_messages.append({"role": role, "content": text})
    openai_messages.append(
        {
            "role": "user",
            "content": (
                "Correct ONLY the following message. Do not correct any earlier context messages.\n\n"
                f"Message to correct:\n{cleaned}"
            ),
        }
    )
    return openai_messages


def chat_reply_messages(
    history: list[dict],
    target_language: str | None,
    native_language: str | None,
) -> list[dict]:
    system_prompt = make_system_chat_prompt(target_language, native_language)
    openai_messages: list[dict] = [{"role": "system", "content": system_prompt}]
    openai_messages.extend(_build_chat_openai_messages(history))
    return openai_messages


def translation_messages(text: str, to_language: str | None) -> list[dict]:
    cleaned = text.strip()
    system_prompt = (
        "You are a translation engine for Polyglot. "
        "Translate the user's text faithfully and naturally. "
        "Return ONLY valid JSON with schema: "
        '{"translated_text":"..."}'
    )
    user_prompt = (
        f"Target language: {to_language}\n"
        "If the text is already in the target language, keep meaning and return a natural phrasing.\n"
        f"Text:\n{cleaned}"
    )
    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]


def title_messages(conversation_lines: list[str]) -> list[dict]:
    joined = "\n".join(conversation_lines)
    system_prompt = (
        "You name chat threads for a language-learning app. "
        "Given the beginning of a conversation, output a very short title (about 3–7 words) "
        "describing the topic in English. No quotation marks. No trailing punctuation. "
        'Return ONLY valid JSON: {"title": "..."}'
    )
    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": f"Conversation excerpt:\n{joined}"},
    ]
