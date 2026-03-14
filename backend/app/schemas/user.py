from datetime import datetime
from pydantic import BaseModel, EmailStr


class UserOut(BaseModel):
    id: int
    email: EmailStr
    native_language_id: int | None = None
    active_language_space_id: int | None = None
    is_verified: bool
    created_at: datetime


class SupportedLanguageOut(BaseModel):
    id: int
    code: str
    name: str
    native_name: str | None = None
    learning_enabled: bool


class LanguagesResponse(BaseModel):
    native_language: SupportedLanguageOut | None = None
    active_language: SupportedLanguageOut | None = None
    all_available_languages: list[SupportedLanguageOut]


class UserUpdateRequest(BaseModel):
    native_language: int | None = None
    active_language: int | None = None
