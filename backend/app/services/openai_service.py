from openai import OpenAI

from app.core.config import get_settings

settings = get_settings()


def get_dummy_completion(prompt: str) -> str:
    if not settings.openai_api_key:
        return "OpenAI key not configured yet. Dummy response from Polyglot backend."

    client = OpenAI(api_key=settings.openai_api_key)
    completion = client.responses.create(
        model=settings.openai_model,
        input=f"You are Polyglot's assistant. Keep it short.\n\nUser prompt: {prompt}",
    )
    return completion.output_text or "No response from model."
