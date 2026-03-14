import json
import logging

from openai import OpenAI

from app.core.config import get_settings

settings = get_settings()
logger = logging.getLogger("polyglot.openai")


def get_dummy_completion(prompt: str) -> str:
    if not settings.openai_api_key:
        return "OpenAI key not configured yet. Dummy response from Polyglot backend."

    client = OpenAI(api_key=settings.openai_api_key)
    completion = client.responses.create(
        model=settings.openai_model,
        input=f"You are Polyglot's assistant. Keep it short.\n\nUser prompt: {prompt}",
    )
    return completion.output_text or "No response from model."


def get_chat_turn(
    history: list[dict],
    target_language: str | None = None,
    native_language: str | None = None,
) -> dict:
    """
    Build a chat turn response.

    Returns a dict matching the assistant message content shape:
      {
        "assistant_response": "...",
        "correction": {"corrected": "...", "notes": [...]} | null
      }
    """
    lang_ctx = ""
    if target_language:
        lang_ctx = f"The user is learning {target_language}."
        if native_language:
            lang_ctx += f" Their native language is {native_language}."

    system_prompt = (
        f"You are a language learning assistant for Polyglot. {lang_ctx}\n\n"
        "When the user sends a message, reply naturally AND provide a correction for any "
        "grammatical or vocabulary errors in their message.\n\n"
        "You MUST respond with valid JSON matching this exact schema:\n"
        "{\n"
        '  "assistant_response": "Your natural reply",\n'
        '  "correction": {\n'
        '    "corrected": "The corrected version of what the user wrote",\n'
        '    "notes": ["Explanation of error 1", "Explanation of error 2"]\n'
        "  }\n"
        "}\n\n"
        "If the user's message has no errors, set \"correction\" to null.\n"
        "Respond ONLY with the JSON object, no other text."
    )

    openai_messages: list[dict] = [{"role": "system", "content": system_prompt}]
    for msg in history:
        role = msg.get("role", "user")
        content = msg.get("content", {})
        if role == "user":
            openai_messages.append({"role": "user", "content": content.get("text", "") if isinstance(content, dict) else str(content)})
        elif role == "assistant":
            openai_messages.append({"role": "assistant", "content": content.get("assistant_response", "") if isinstance(content, dict) else str(content)})

    try:
        client = OpenAI(api_key=settings.openai_api_key)
        response = client.chat.completions.create(
            model=settings.openai_model,
            messages=openai_messages,
            response_format={"type": "json_object"},
        )
        raw = response.choices[0].message.content or "{}"
        data = json.loads(raw)
        return {
            "assistant_response": data.get("assistant_response", ""),
            "correction": data.get("correction"),
        }
    except Exception:
        logger.exception("OpenAI chat turn failed")
        return {
            "assistant_response": "Sorry, I couldn't process that. Please try again.",
            "correction": None,
        }
