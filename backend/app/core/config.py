from functools import lru_cache
from typing import Self

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "Polyglot API"
    app_env: str = "development"

    database_url: str = "postgresql+psycopg://polyglot:polyglot@localhost:5433/polyglot"
    jwt_secret: str = "change-me-in-production"
    jwt_expire_minutes: int = 60 * 24 * 7
    verification_code_ttl_minutes: int = 10

    openai_api_key: str | None = None
    # Shared baseline for all OpenAI tasks; omit to fall back to OPENAI_MODEL, then gpt-4o-mini.
    openai_model_default: str | None = Field(default=None)
    openai_model_chat: str | None = None
    openai_model_explain: str | None = None
    openai_model_translation: str | None = None
    openai_model_thread_title: str | None = None

    @model_validator(mode="after")
    def _resolve_openai_models(self) -> Self:
        d = self.openai_model_default or "gpt-4o-mini"
        object.__setattr__(self, "openai_model_chat", self.openai_model_chat or d)
        object.__setattr__(self, "openai_model_explain", self.openai_model_explain or d)
        object.__setattr__(self, "openai_model_translation", self.openai_model_translation or d)
        object.__setattr__(self, "openai_model_thread_title", self.openai_model_thread_title or d)
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()
