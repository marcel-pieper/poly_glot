from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.deps import current_user
from app.db.session import get_db
from app.models.language_space import LanguageSpace
from app.models.supported_language import SupportedLanguage
from app.models.translation import Translation
from app.models.user import User
from app.schemas.ai import (
    TranslateItem,
    TranslateRequest,
    TranslateResponse,
    TranslationListResponse,
    TranslationSummary,
)
from app.schemas.auth import DummyPromptRequest, DummyPromptResponse
from app.services.extraction_service import extract_items, log_extraction, persist_items
from app.services.openai_service import get_dummy_completion, get_translation

router = APIRouter(prefix="/ai", tags=["ai"])


def _get_user_translation(
    db: Session,
    user: User,
    translation_id: int,
) -> Translation:
    row = db.execute(
        select(Translation)
        .join(LanguageSpace, Translation.language_space_id == LanguageSpace.id)
        .where(Translation.id == translation_id)
        .where(LanguageSpace.user_id == user.id)
    ).scalar_one_or_none()
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Translation not found")
    return row


@router.post("/dummy", response_model=DummyPromptResponse)
def dummy_prompt(payload: DummyPromptRequest):
    return DummyPromptResponse(answer=get_dummy_completion(payload.prompt))


@router.get("/translations", response_model=TranslationListResponse)
def list_translations(
    limit: int = 50,
    offset: int = 0,
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
):
    if not user.active_language_space_id:
        return TranslationListResponse(translations=[], total=0)

    base_q = (
        select(Translation)
        .join(LanguageSpace, Translation.language_space_id == LanguageSpace.id)
        .where(LanguageSpace.user_id == user.id)
        .where(Translation.language_space_id == user.active_language_space_id)
    )
    total: int = db.execute(select(func.count()).select_from(base_q.subquery())).scalar_one()
    rows = (
        db.execute(base_q.order_by(Translation.id.desc()).limit(limit).offset(offset))
        .scalars()
        .all()
    )
    return TranslationListResponse(
        translations=[
            TranslationSummary(
                id=row.id,
                source_text=row.from_text,
                translated_text=row.to_text,
                from_language=row.from_language,
                to_language=row.to_language,
                created_at=row.created_at,
            )
            for row in rows
        ],
        total=total,
    )


@router.get("/translations/{translation_id}", response_model=TranslateResponse)
def get_translation_detail(
    translation_id: int,
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
):
    row = _get_user_translation(db, user, translation_id)
    return TranslateResponse(
        translation_id=row.id,
        source_text=row.from_text,
        translated_text=row.to_text,
        status="complete",
        items=[],
    )


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
    translated_text = result.get("translated_text", "")
    translate_status = result.get("status", "failed")

    translation_id: int | None = None
    items: list[dict] = []

    if (
        translate_status == "complete"
        and translated_text
        and user.active_language_space_id
        and learning_language
        and native_language
    ):
        translation_row = Translation(
            language_space_id=user.active_language_space_id,
            from_text=source_text,
            to_text=translated_text,
            from_language=learning_language,
            to_language=native_language,
        )
        db.add(translation_row)
        db.commit()
        db.refresh(translation_row)
        translation_id = translation_row.id

        items = extract_items(
            source_text=source_text,
            translated_text=translated_text,
            source_language=learning_language,
            gloss_language=native_language,
        )

        log_extraction(
            translation_id=translation_id,
            source_language=learning_language,
            gloss_language=native_language,
            source_text=source_text,
            translated_text=translated_text,
            items=items,
        )

        if items:
            persist_items(
                db=db,
                items=items,
                source_language=learning_language,
                gloss_language=native_language,
            )
            db.commit()

    response_items = [
        TranslateItem(
            type=item["type"],
            raw_item=item["raw_item"],
            raw_item_translation=item["raw_item_translation"],
            lemma=item["lemma"],
        )
        for item in items
    ]

    return TranslateResponse(
        translation_id=translation_id,
        source_text=source_text,
        translated_text=translated_text,
        status=translate_status,
        items=response_items,
    )
