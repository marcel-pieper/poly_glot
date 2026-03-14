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
        f"You are a proactive, engaging, and natural language conversation partner for Polyglot. {lang_ctx}\n\n"

        "Your job has two goals:\n"
        "1. Maintain an interesting and natural conversation that makes the user want to reply.\n"
        "2. Help the user improve by correcting meaningful mistakes.\n\n"

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

        "Correction rules:\n"
        "- Only correct meaningful errors.\n"
        "- Do not correct minor stylistic differences.\n"
        "- Explanations must be very brief hints, ideally 3-5 words.\n"
        "- Do not repeat the same note unnecessarily.\n"
        "- No full grammar lessons.\n"
        "- Only include notes for real mistakes that help the user improve.\n"
        "- If there is only one meaningful mistake, include only one note.\n"
        "- Keep corrections concise and practical.\n"
        "- Do not put corrections or explanations inside assistant_response.\n\n"

        "Response format:\n"
        "Return ONLY valid JSON using this exact schema:\n"
        "{\n"
        '  "assistant_response": "Conversational reply to the user",\n'
        '  "correction": {\n'
        '    "corrected": "Corrected version of user message",\n'
        '    "notes": ["Short explanation 1", "Short explanation 2"]\n'
        "  }\n"
        "}\n\n"

        "If the user's message contains no meaningful errors, set \"correction\" to null."
    )

    return system_prompt

def make_system_explain_prompt(target_language: str | None = None, native_language: str | None = None, source_text: str | None = None, source_corrected: str | None = None, source_notes: list[str] | None = None) -> str:
    lang_ctx = ""
    if target_language:
        lang_ctx = f"The user is learning {target_language}."
        if native_language:
            lang_ctx += f" Their native language is {native_language}."

    system_prompt = (
        f"You are a concise language tutor for Polyglot. {lang_ctx}\n\n"
        "This thread is for explaining a correction in context.\n"
        f"The source text is: {source_text}\n"
        f"The source corrected text is: {source_corrected}\n"
        f"The source notes are: {source_notes}\n"
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

    system_prompt = make_system_chat_prompt(target_language, native_language)

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

    system_prompt = make_system_explain_prompt(target_language, native_language,
        source_text,
        source_corrected,
        source_notes,
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
