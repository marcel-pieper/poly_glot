import json
import logging

from openai import OpenAI

from app.core.config import get_settings

settings = get_settings()
logger = logging.getLogger("polyglot.openai")

def make_system_chat_prompt(target_language: str | None = None, native_language: str | None = None) -> str:
    lang_ctx = ""
    if target_language:
        lang_ctx = f"The user is learning {target_language}."
        if native_language:
            lang_ctx += f" Their native language is {native_language}."
    
    system_prompt = (
        f"You are an engaging language conversation partner for Polyglot. {lang_ctx}\n\n"

        "Your job has two goals:\n"
        "1. Keep a natural conversation going.\n"
        "2. Help the user improve by correcting mistakes.\n\n"

        "Conversation rules:\n"
        "- Respond naturally to the user's message.\n"
        "- Show curiosity and engagement.\n"
        "- Ask follow-up questions when appropriate.\n"
        "- Keep responses relatively concise.\n\n"

        "Correction rules:\n"
        "- Only correct meaningful errors.\n"
        "- Do not correct minor stylistic differences.\n"
        "- Explanations must be very brief hints (3–5 words).\n"
        "- Do not repeat yourself.\n"
        "- No full grammar explanations.\n\n"

        "Language level:\n"
        "- Adapt difficulty to the user's level.\n"
        "- Prefer clear, natural phrasing.\n\n"

        "Return ONLY valid JSON using this schema:\n"
        "{\n"
        '  "assistant_response": "Conversational reply to the user",\n'
        '  "correction": {\n'
        '    "corrected": "Corrected version of user message",\n'
        '    "notes": ["Short Explanation of error 1", "Short Explanation of error 2"]\n'
        "  }\n"
        "}\n\n"

        "If the user's message contains no errors, set \"correction\" to null."
        " Do not put any corrections or explanations in `assistant_response`,"
        " that is exclusively for the continuation of the conversation."
    )
    return system_prompt


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

    Returns a dict with assistant content and user correction payload:
      {
        "assistant_response": "...",
        "correction": {"corrected": "...", "notes": [...]} | null,
        "status": "complete" | "failed"
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
            "status": "complete",
        }
    except Exception:
        logger.exception("OpenAI chat turn failed")
        return {
            "assistant_response": "Sorry, I couldn't process that. Please try again.",
            "correction": None,
            "status": "failed",
        }


def get_explain_turn(
    history: list[dict],
    seed: dict | None,
    target_language: str | None = None,
    native_language: str | None = None,
) -> dict:
    """
    Build an explain-thread turn response.

    Returns a dict with assistant content and user correction payload:
      {
        "assistant_response": "...",
        "correction": {"corrected": "...", "notes": [...]} | null,
        "status": "complete" | "failed"
      }
    """
    lang_ctx = ""
    if target_language:
        lang_ctx = f"The user is learning {target_language}."
        if native_language:
            lang_ctx += f" Their native language is {native_language}."

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

    system_prompt = (
        f"You are a concise language tutor for Polyglot. {lang_ctx}\n\n"
        "This thread is for explaining a correction in context.\n"
        f'Original sentence: "{source_text}"\n'
        f'Corrected sentence: "{source_corrected}"\n'
        f"Correction notes: {source_notes}\n\n"
        "When the user asks a question, provide a short, clear explanation with one practical example.\n"
        "Also correct the user's newest question if needed.\n\n"
        "You MUST respond with valid JSON matching this exact schema:\n"
        "{\n"
        '  "assistant_response": "Short explanation response",\n'
        '  "correction": {\n'
        '    "corrected": "Corrected version of user question",\n'
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
            openai_messages.append(
                {"role": "user", "content": content.get("text", "") if isinstance(content, dict) else str(content)}
            )
        elif role == "assistant":
            openai_messages.append(
                {
                    "role": "assistant",
                    "content": content.get("assistant_response", "") if isinstance(content, dict) else str(content),
                }
            )

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
            "status": "complete",
        }
    except Exception:
        logger.exception("OpenAI explain turn failed")
        return {
            "assistant_response": "Sorry, I couldn't explain that right now. Please try again.",
            "correction": None,
            "status": "failed",
        }
