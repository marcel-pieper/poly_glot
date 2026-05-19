import json
import logging
from concurrent.futures import ThreadPoolExecutor
from typing import Any

from openai import OpenAI

from app.core.config import get_settings

settings = get_settings()
logger = logging.getLogger("polyglot.openai")

def _create_language_context(target_language: str | None = None, native_language: str | None = None) -> str:
    lang_ctx = ""
    if target_language:
        lang_ctx = f"The user is learning {target_language}."
        if native_language:
            lang_ctx += f" Their native language is {native_language}."
    return lang_ctx

def make_system_chat_prompt(target_language: str | None = None, native_language: str | None = None) -> str:
    lang_ctx = _create_language_context(target_language, native_language)

    system_prompt = (
        f"You are a proactive, engaging, and natural language conversation partner for Polyglot. {lang_ctx}\n\n"

        "Your job is to maintain an interesting and natural conversation that makes the user want to reply.\n\n"

        "Core behavior:\n"
        "- You are responsible for the energy and direction of the conversation.\n"
        "- Do not wait for the user to make things interesting.\n"
        "- If the user is vague, passive, short, or low-energy, introduce a more specific, playful, vivid, or thought-provoking direction.\n"
        "- If the user gives a rich or interesting message, follow their lead more naturally.\n"
        "- Prefer specific and vivid prompts over broad generic questions.\n"
        "- Make it easy for the user to answer while still challenging them to use the language.\n"
        "- Vary your style naturally: sometimes playful, sometimes curious, sometimes lightly challenging, sometimes reflective.\n"
        "- Create momentum instead of just reacting.\n\n"

        "How to keep the conversation interesting:\n"
        "- Use concrete scenarios, comparisons, mini challenges, playful assumptions, light opinions, or surprising follow-ups.\n"
        "- Introduce topics yourself when needed.\n"
        "- Ask narrow, engaging questions instead of broad ones.\n"
        "- Sometimes guide the user toward telling a story, choosing between options, defending an opinion, describing something vividly, or imagining a scenario.\n"
        "- Do not make every turn feel like an interview.\n"
        "- In most replies, include at least one of these: a specific hook, a playful angle, a concrete scenario, a meaningful opinion, or a challenge.\n\n"

        "Avoid boring patterns:\n"
        "- Avoid generic filler like: 'That's interesting', 'I understand', 'Tell me more', 'How about you?', 'What do you think?', 'How was your day?'\n"
        "- Avoid repeating the user's message without adding anything new.\n"
        "- Avoid ending every response with a vague open-ended question.\n"
        "- Do not be overly polite, formal, neutral, or assistant-like.\n\n"

        "Language practice:\n"
        "- Adapt difficulty to the user's apparent level.\n"
        "- Prefer clear, natural phrasing.\n"
        "- Encourage the user to produce language, not just answer yes/no.\n"
        "- When useful, invite the user to describe, compare, explain, choose, imagine, justify, or narrate.\n"
        "- Keep the conversation natural first, but always make it good practice.\n\n"

        "Response format:\n"
        "Return ONLY valid JSON using this exact schema:\n"
        "{\n"
        '  "assistant_response": "Conversational reply to the user"\n'
        "}\n\n"
        "Do not include corrections or grammar notes — another system handles that separately."
    )

    return system_prompt


def make_system_correction_prompt(target_language: str | None = None, native_language: str | None = None) -> str:
    lang_ctx = _create_language_context(target_language, native_language)

    return (
        f"You are a language corrector for Polyglot. {lang_ctx}\n\n"
        "Your only job is to correct meaningful mistakes in the user's most recent message.\n\n"
        "Rules:\n"
        "- Correct ONLY the final user message marked as the message to correct.\n"
        "- Do not correct earlier messages in the context, even if they contain errors.\n"
        "- Only correct meaningful errors; ignore minor stylistic differences.\n"
        "- Explanations must be very brief hints, ideally 3-5 words.\n"
        "- Do not repeat the same note unnecessarily.\n"
        "- No full grammar lessons.\n"
        "- If there is only one meaningful mistake, include only one note.\n"
        "- Keep corrections concise and practical.\n\n"
        "Response format:\n"
        "Return ONLY valid JSON using this exact schema:\n"
        "{\n"
        '  "correction": {\n'
        '    "corrected": "Corrected version of the message to correct",\n'
        '    "notes": ["Short explanation 1", "Short explanation 2"]\n'
        "  }\n"
        "}\n\n"
        'If the message to correct contains no meaningful errors, set "correction" to null.'
    )


def _user_text(content: dict | str | Any) -> str:
    if isinstance(content, dict):
        return str(content.get("text", ""))
    return str(content)


def _assistant_text(content: dict | str | Any) -> str:
    if isinstance(content, dict):
        return str(content.get("assistant_response", ""))
    return str(content)


def _build_chat_openai_messages(history: list[dict]) -> list[dict]:
    openai_messages: list[dict] = []
    for msg in history:
        role = msg.get("role", "user")
        content = msg.get("content", {})
        if role == "user":
            openai_messages.append({"role": "user", "content": _user_text(content)})
        elif role == "assistant":
            openai_messages.append({"role": "assistant", "content": _assistant_text(content)})
    return openai_messages


def get_dummy_completion(prompt: str) -> str:
    if not settings.openai_api_key:
        return "OpenAI key not configured yet. Dummy response from Polyglot backend."

    client = OpenAI(api_key=settings.openai_api_key)
    completion = client.responses.create(
        model=settings.openai_model_chat,
        input=f"You are Polyglot's assistant. Keep it short.\n\nUser prompt: {prompt}",
    )
    return completion.output_text or "No response from model."


def get_translation(
    text: str,
    from_language: str | None = None,
    to_language: str | None = None,
    native_language: str | None = None,
) -> dict:
    """
    Translate free text and return a normalized payload:
      {
        "translated_text": "...",
        "status": "complete" | "failed"
      }
    """
    cleaned = text.strip()
    if not cleaned:
        return {"translated_text": "", "status": "failed"}

    if not settings.openai_api_key:
        return {
            "translated_text": "OpenAI key not configured yet. Translation unavailable.",
            "status": "failed",
        }

    logger.info("Translating text to %s", to_language)
    logger.info("Text: %s", cleaned)
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

    try:
        client = OpenAI(api_key=settings.openai_api_key)
        response = client.chat.completions.create(
            model=settings.openai_model_translation,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            response_format={"type": "json_object"},
        )
        raw = response.choices[0].message.content or "{}"
        data = json.loads(raw)
        translated = str(data.get("translated_text") or "").strip()
        if not translated:
            return {
                "translated_text": "Sorry, I couldn't translate that right now. Please try again.",
                "status": "failed",
            }
        return {"translated_text": translated, "status": "complete"}
    except Exception:
        logger.exception("OpenAI translation failed")
        return {
            "translated_text": "Sorry, I couldn't translate that right now. Please try again.",
            "status": "failed",
        }


def get_message_correction(
    message_to_correct: str,
    prior_exchange: list[tuple[str, str]],
    target_language: str | None = None,
    native_language: str | None = None,
) -> dict:
    """
    Correct the latest user message with optional prior exchange for context.

    Returns:
      {
        "correction": {"corrected": "...", "notes": [...]} | null,
        "status": "complete" | "failed"
      }
    """
    cleaned = message_to_correct.strip()
    if not cleaned:
        return {"correction": None, "status": "failed"}

    system_prompt = make_system_correction_prompt(target_language, native_language)
    openai_messages: list[dict] = [{"role": "system", "content": system_prompt}]
    for role, text in prior_exchange:
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

    try:
        client = OpenAI(api_key=settings.openai_api_key)
        response = client.chat.completions.create(
            model=settings.openai_model_correct,
            messages=openai_messages,
            response_format={"type": "json_object"},
        )
        raw = response.choices[0].message.content or "{}"
        data = json.loads(raw)
        return {
            "correction": data.get("correction"),
            "status": "complete",
        }
    except Exception:
        logger.exception("OpenAI message correction failed")
        return {"correction": None, "status": "failed"}


def get_chat_reply(
    history: list[dict],
    target_language: str | None = None,
    native_language: str | None = None,
) -> dict:
    """
    Build a conversational reply for the chat thread.

    Returns:
      {
        "assistant_response": "...",
        "status": "complete" | "failed"
      }
    """
    system_prompt = make_system_chat_prompt(target_language, native_language)
    openai_messages: list[dict] = [{"role": "system", "content": system_prompt}]
    openai_messages.extend(_build_chat_openai_messages(history))

    try:
        client = OpenAI(api_key=settings.openai_api_key)
        response = client.chat.completions.create(
            model=settings.openai_model_chat,
            messages=openai_messages,
            response_format={"type": "json_object"},
        )
        raw = response.choices[0].message.content or "{}"
        data = json.loads(raw)
        return {
            "assistant_response": data.get("assistant_response", ""),
            "status": "complete",
        }
    except Exception:
        logger.exception("OpenAI chat reply failed")
        return {
            "assistant_response": "Sorry, I couldn't process that. Please try again.",
            "status": "failed",
        }


def get_explain_correction(
    history: list[dict],
    seed: dict | None,
    target_language: str | None = None,
    native_language: str | None = None,
) -> dict:
    """Returns {"correction": ... | null, "status": "complete" | "failed"}."""
    message_to_correct, prior = _explain_turn_parts(history, seed)
    cleaned = message_to_correct.strip()
    if not cleaned:
        return {"correction": None, "status": "failed"}

    lang_ctx = _create_language_context(target_language, native_language)
    source_text, source_corrected, source_notes = _explain_seed_fields(seed)
    system_prompt = (
        f"You are a language corrector for Polyglot explain threads. {lang_ctx}\n\n"
        "This thread explains a prior chat correction.\n"
        f"Original source text: {source_text}\n"
        f"Source corrected text: {source_corrected}\n"
        f"Source notes: {source_notes}\n\n"
        "Correct ONLY the final user question marked below.\n"
        "Do not correct earlier context messages.\n"
        "Only correct meaningful errors in the user's question.\n"
        "Notes must be very brief hints, ideally 3-5 words.\n\n"
        "Return ONLY valid JSON:\n"
        "{\n"
        '  "correction": {\n'
        '    "corrected": "Corrected version of the question",\n'
        '    "notes": ["Short explanation 1"]\n'
        "  }\n"
        "}\n\n"
        'If the question has no meaningful errors, set "correction" to null.'
    )

    openai_messages: list[dict] = [{"role": "system", "content": system_prompt}]
    for role, text in prior:
        openai_messages.append({"role": role, "content": text})
    openai_messages.append(
        {
            "role": "user",
            "content": (
                "Correct ONLY the following question. Do not correct any earlier context messages.\n\n"
                f"Question to correct:\n{cleaned}"
            ),
        }
    )

    try:
        client = OpenAI(api_key=settings.openai_api_key)
        response = client.chat.completions.create(
            model=settings.openai_model_correct,
            messages=openai_messages,
            response_format={"type": "json_object"},
        )
        raw = response.choices[0].message.content or "{}"
        data = json.loads(raw)
        return {
            "correction": data.get("correction"),
            "status": "complete",
        }
    except Exception:
        logger.exception("OpenAI explain correction failed")
        return {"correction": None, "status": "failed"}


def get_explain_reply(
    history: list[dict],
    seed: dict | None,
    target_language: str | None = None,
    native_language: str | None = None,
) -> dict:
    """Returns {"assistant_response": "...", "status": "complete" | "failed"}."""
    system_prompt = _make_system_explain_reply_prompt(
        target_language,
        native_language,
        seed,
    )
    openai_messages: list[dict] = [{"role": "system", "content": system_prompt}]
    openai_messages.extend(_build_chat_openai_messages(history))

    try:
        client = OpenAI(api_key=settings.openai_api_key)
        response = client.chat.completions.create(
            model=settings.openai_model_explain,
            messages=openai_messages,
            response_format={"type": "json_object"},
        )
        raw = response.choices[0].message.content or "{}"
        data = json.loads(raw)
        return {
            "assistant_response": data.get("assistant_response", ""),
            "status": "complete",
        }
    except Exception:
        logger.exception("OpenAI explain reply failed")
        return {
            "assistant_response": "Sorry, I couldn't explain that right now. Please try again.",
            "status": "failed",
        }


def _explain_seed_fields(seed: dict | None) -> tuple[str, str, list[str]]:
    source_text = ""
    source_corrected = ""
    source_notes: list[str] = []
    if isinstance(seed, dict):
        source_text = str(seed.get("source_text") or "")
        seed_correction = seed.get("correction")
        if isinstance(seed_correction, dict):
            source_corrected = str(seed_correction.get("corrected") or "")
            notes = seed_correction.get("notes")
            if isinstance(notes, list):
                source_notes = [str(note) for note in notes]
    return source_text, source_corrected, source_notes


def _explain_turn_parts(
    history: list[dict],
    seed: dict | None,
) -> tuple[str, list[tuple[str, str]]]:
    entries: list[tuple[str, str]] = []
    for msg in history:
        role = msg.get("role", "user")
        content = msg.get("content", {})
        if role == "user":
            entries.append(("user", _user_text(content)))
        elif role == "assistant":
            entries.append(("assistant", _assistant_text(content)))

    if not entries or entries[-1][0] != "user":
        return "", []

    message_to_correct = entries[-1][1]
    prior: list[tuple[str, str]] = []
    for role, text in reversed(entries[:-1]):
        prior.insert(0, (role, text))
        if len(prior) >= 2:
            break
    return message_to_correct, prior


def _make_system_explain_reply_prompt(
    target_language: str | None,
    native_language: str | None,
    seed: dict | None,
) -> str:
    lang_ctx = _create_language_context(target_language, native_language)
    source_text, source_corrected, source_notes = _explain_seed_fields(seed)

    return (
        f"You are a concise language tutor for Polyglot. {lang_ctx}\n\n"
        "This thread is for explaining a correction in context.\n"
        f"The source text is: {source_text}\n"
        f"The source corrected text is: {source_corrected}\n"
        f"The source notes are: {source_notes}\n"
        "When the user asks a question, provide a short, clear explanation with one practical example.\n"
        "Do not correct the user's question here — another system handles that separately.\n\n"
        "You MUST respond with valid JSON matching this exact schema:\n"
        "{\n"
        '  "assistant_response": "Short explanation response"\n'
        "}\n\n"
        "Respond ONLY with the JSON object, no other text."
    )


from concurrent.futures import ThreadPoolExecutor


def get_explain_turn(
    history: list[dict],
    seed: dict | None,
    target_language: str | None = None,
    native_language: str | None = None,
) -> tuple[dict, dict]:
    """
    Build an explain-thread turn as separate correction and reply results.

    Returns (correction_result, response_result).
    """
    with ThreadPoolExecutor(max_workers=2) as executor:
        correction_future = executor.submit(
            get_explain_correction,
            history,
            seed,
            target_language,
            native_language,
        )
        response_future = executor.submit(
            get_explain_reply,
            history,
            seed,
            target_language,
            native_language,
        )
        return correction_future.result(), response_future.result()


def get_chat_thread_title(conversation_lines: list[str]) -> str | None:
    """
    Produce a short list title from an abbreviated transcript (first messages).
    Returns None if the API is unavailable or the model returns nothing usable.
    """
    if not conversation_lines:
        return None

    if not settings.openai_api_key:
        logger.warning("OpenAI key not configured; skipping thread title generation")
        return None

    joined = "\n".join(conversation_lines)
    system_prompt = (
        "You name chat threads for a language-learning app. "
        "Given the beginning of a conversation, output a very short title (about 3–7 words) "
        "describing the topic in English. No quotation marks. No trailing punctuation. "
        "Return ONLY valid JSON: {\"title\": \"...\"}"
    )
    user_prompt = f"Conversation excerpt:\n{joined}"

    try:
        client = OpenAI(api_key=settings.openai_api_key)
        response = client.chat.completions.create(
            model=settings.openai_model_thread_title,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            response_format={"type": "json_object"},
        )
        raw = response.choices[0].message.content or "{}"
        data = json.loads(raw)
        title = str(data.get("title") or "").strip()
        if not title:
            return None
        return title[:255]
    except Exception:
        logger.exception("OpenAI thread title generation failed")
        return None
