from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.api.deps import current_user
from app.db.session import get_db
from app.models.email_verification_code import EmailVerificationCode
from app.models.language_space import LanguageSpace
from app.models.supported_language import SupportedLanguage
from app.models.user import User
from app.schemas.user import LanguagesResponse, SupportedLanguageOut, UserOut, UserUpdateRequest

router = APIRouter(tags=["users"])


@router.get("/me", response_model=UserOut)
def me(user: User = Depends(current_user)):
    return user


@router.get("/languages", response_model=LanguagesResponse)
def languages(user: User = Depends(current_user), db: Session = Depends(get_db)):
    supported_languages = db.execute(select(SupportedLanguage).order_by(SupportedLanguage.name)).scalars().all()
    native_language = None
    active_language = None

    if user.native_language_id:
        native_language = db.execute(
            select(SupportedLanguage).where(SupportedLanguage.id == user.native_language_id)
        ).scalar_one_or_none()
        if native_language:
            native_language = SupportedLanguageOut.model_validate(native_language, from_attributes=True)

    if user.active_language_space_id:
        active_language = db.execute(
            select(SupportedLanguage)
            .join(LanguageSpace, LanguageSpace.target_language_id == SupportedLanguage.id)
            .where(LanguageSpace.id == user.active_language_space_id)
            .where(LanguageSpace.user_id == user.id)
        ).scalar_one_or_none()
        if active_language:
            active_language = SupportedLanguageOut.model_validate(active_language, from_attributes=True)

    return LanguagesResponse(
        native_language=native_language,
        active_language=active_language,
        all_available_languages=[
            SupportedLanguageOut.model_validate(language, from_attributes=True) for language in supported_languages
        ],
    )


@router.patch("/me", response_model=UserOut)
def update_me(payload: UserUpdateRequest, user: User = Depends(current_user), db: Session = Depends(get_db)):
    if "native_language" in payload.model_fields_set:
        if payload.native_language is None:
            user.native_language_id = None
        else:
            native_language = db.execute(
                select(SupportedLanguage).where(SupportedLanguage.id == payload.native_language)
            ).scalar_one_or_none()
            if not native_language:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid native_language id")
            user.native_language_id = native_language.id

    if "active_language" in payload.model_fields_set:
        if payload.active_language is None:
            user.active_language_space_id = None
        else:
            active_language = db.execute(
                select(SupportedLanguage).where(SupportedLanguage.id == payload.active_language)
            ).scalar_one_or_none()
            if not active_language:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid active_language id")
            if not active_language.learning_enabled:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="active_language is not enabled")

            space = db.execute(
                select(LanguageSpace)
                .where(LanguageSpace.user_id == user.id)
                .where(LanguageSpace.target_language_id == active_language.id)
            ).scalar_one_or_none()
            if not space:
                space = LanguageSpace(user_id=user.id, target_language_id=active_language.id)
                db.add(space)
                db.flush()
            user.active_language_space_id = space.id

    db.commit()
    db.refresh(user)
    return user


@router.delete("/me", status_code=status.HTTP_204_NO_CONTENT)
def delete_me(user: User = Depends(current_user), db: Session = Depends(get_db)):
    # Remove transient auth artifacts keyed by email before deleting the user.
    db.execute(delete(EmailVerificationCode).where(EmailVerificationCode.email == user.email))
    db.delete(user)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
