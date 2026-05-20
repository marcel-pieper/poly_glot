from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.deps import current_user
from app.db.session import get_db
from app.models.language_space import LanguageSpace
from app.models.lemma import Lemma, LemmaTranslation
from app.models.supported_language import SupportedLanguage
from app.models.user import User
from app.models.user_vocab import UserVocab
from app.schemas.vocab import (
    AddVocabRequest,
    AddVocabResponse,
    VocabItem,
    VocabListResponse,
)
from app.services.extraction_service import get_or_create_lemma
from app.services.fsrs_service import new_card_state

router = APIRouter(prefix="/vocab", tags=["vocab"])


def _require_languages(db: Session, user: User) -> tuple[int, str, str]:
    """Resolve (active_language_space_id, target_language_name, native_language_name).

    The vocab feature is only meaningful once the user has both an active
    language space and a native language set, so we 400 otherwise.
    """
    if not user.active_language_space_id or not user.native_language_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Active language space and native language are required.",
        )
    target_name = db.execute(
        select(SupportedLanguage.name)
        .join(LanguageSpace, LanguageSpace.target_language_id == SupportedLanguage.id)
        .where(LanguageSpace.id == user.active_language_space_id)
        .where(LanguageSpace.user_id == user.id)
    ).scalar_one_or_none()
    native_name = db.execute(
        select(SupportedLanguage.name).where(SupportedLanguage.id == user.native_language_id)
    ).scalar_one_or_none()
    if not target_name or not native_name:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Active language space and native language are required.",
        )
    return user.active_language_space_id, target_name, native_name


def _glosses_for(db: Session, lemma_ids: list[int], gloss_language: str) -> dict[int, list[str]]:
    if not lemma_ids:
        return {}
    rows = db.execute(
        select(LemmaTranslation.lemma_id, LemmaTranslation.translation)
        .where(LemmaTranslation.lemma_id.in_(lemma_ids))
        .where(LemmaTranslation.gloss_language == gloss_language)
        .order_by(LemmaTranslation.id.asc())
    ).all()
    out: dict[int, list[str]] = {}
    for lemma_id, translation in rows:
        out.setdefault(lemma_id, []).append(translation)
    return out


def _as_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def _to_vocab_item(row: UserVocab, lemma: Lemma, glosses: list[str], now: datetime) -> VocabItem:
    due = _as_utc(row.due)
    last_review = _as_utc(row.last_review) if row.last_review is not None else None
    return VocabItem(
        id=row.id,
        lemma_id=lemma.id,
        lemma=lemma.lemma,
        type=lemma.type,
        language=lemma.language,
        glosses=glosses,
        state=row.state,
        due=due,
        last_review=last_review,
        review_count=row.review_count,
        lapse_count=row.lapse_count,
        is_due=due <= now,
    )


@router.get("", response_model=VocabListResponse)
def list_vocab(
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
):
    if not user.active_language_space_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Active language space is required.",
        )
    space_id = user.active_language_space_id
    native: str | None = None
    if user.native_language_id:
        native = db.execute(
            select(SupportedLanguage.name).where(SupportedLanguage.id == user.native_language_id)
        ).scalar_one_or_none()

    rows = db.execute(
        select(UserVocab, Lemma)
        .join(Lemma, Lemma.id == UserVocab.lemma_id)
        .join(LanguageSpace, LanguageSpace.id == UserVocab.language_space_id)
        .where(LanguageSpace.user_id == user.id)
        .where(UserVocab.language_space_id == space_id)
        .order_by(UserVocab.due.asc(), UserVocab.id.desc())
    ).all()

    now = datetime.now(timezone.utc)
    lemma_ids = [lemma.id for _vocab, lemma in rows]
    glosses_by_lemma = _glosses_for(db, lemma_ids, native) if native else {}

    items = [
        _to_vocab_item(vocab, lemma, glosses_by_lemma.get(lemma.id, []), now)
        for vocab, lemma in rows
    ]
    due_count = sum(1 for item in items if item.is_due)
    return VocabListResponse(items=items, total=len(items), due_count=due_count)


@router.post("", response_model=AddVocabResponse, status_code=status.HTTP_201_CREATED)
def add_vocab(
    payload: AddVocabRequest,
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
):
    space_id, target, native = _require_languages(db, user)

    lemma_text = payload.lemma.strip()
    item_type = payload.type.strip().lower()
    if not lemma_text:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Lemma must not be empty.",
        )

    lemma = get_or_create_lemma(
        db,
        language=target,
        lemma=lemma_text,
        type=item_type,
    )

    existing = db.execute(
        select(UserVocab).where(
            UserVocab.language_space_id == space_id,
            UserVocab.lemma_id == lemma.id,
        )
    ).scalar_one_or_none()

    created = False
    if existing is None:
        initial = new_card_state()
        vocab = UserVocab(
            language_space_id=space_id,
            lemma_id=lemma.id,
            **initial.to_columns(),
        )
        db.add(vocab)
        db.commit()
        db.refresh(vocab)
        created = True
    else:
        vocab = existing
        # Ensure any lemma creation above is committed (no-op when existing).
        db.commit()

    glosses = _glosses_for(db, [lemma.id], native).get(lemma.id, [])
    now = datetime.now(timezone.utc)
    return AddVocabResponse(
        item=_to_vocab_item(vocab, lemma, glosses, now),
        created=created,
    )


@router.delete("/{vocab_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_vocab(
    vocab_id: int,
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
):
    row = db.execute(
        select(UserVocab)
        .join(LanguageSpace, LanguageSpace.id == UserVocab.language_space_id)
        .where(UserVocab.id == vocab_id)
        .where(LanguageSpace.user_id == user.id)
    ).scalar_one_or_none()
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Vocab item not found.")
    db.delete(row)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
