from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import current_user
from app.db.session import get_db
from app.models.language_space import LanguageSpace
from app.models.supported_language import SupportedLanguage
from app.models.user import User
from app.schemas.ai import TranslateRequest, TranslateResponse
from app.schemas.auth import DummyPromptRequest, DummyPromptResponse
from app.services.openai_service import get_dummy_completion, get_translation

router = APIRouter(prefix="/ai", tags=["ai"])


@router.post("/dummy", response_model=DummyPromptResponse)
def dummy_prompt(payload: DummyPromptRequest):
    return DummyPromptResponse(answer=get_dummy_completion(payload.prompt))


@router.post("/translate", response_model=TranslateResponse)
def translate_text(
    payload: TranslateRequest,
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
):
    source_text = payload.text.strip()
    if not source_text:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Text must not be empty",
        )

    learning_language: str | None = None
    native_language: str | None = None

    if user.active_language_space_id:
        learning_language = db.execute(
            select(SupportedLanguage.name)
            .join(LanguageSpace, LanguageSpace.target_language_id == SupportedLanguage.id)
            .where(LanguageSpace.id == user.active_language_space_id)
            .where(LanguageSpace.user_id == user.id)
        ).scalar_one_or_none()

    if user.native_language_id:
        native_language = db.execute(
            select(SupportedLanguage.name).where(SupportedLanguage.id == user.native_language_id)
        ).scalar_one_or_none()

    result = get_translation(
        text=source_text,
        from_language=learning_language,
        to_language=native_language,
    )
    return TranslateResponse(
        source_text=source_text,
        translated_text=result.get("translated_text", ""),
        status=result.get("status", "failed"),
    )
