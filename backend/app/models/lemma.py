from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Lemma(Base):
    __tablename__ = "lemmas"
    __table_args__ = (
        UniqueConstraint("language", "lemma", "type", name="uq_lemmas_language_lemma_type"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    language: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    lemma: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    type: Mapped[str] = mapped_column(String(32), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class LemmaTranslation(Base):
    __tablename__ = "lemma_translations"
    __table_args__ = (
        UniqueConstraint(
            "lemma_id",
            "gloss_language",
            "translation",
            name="uq_lemma_translations_lemma_gloss_translation",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    lemma_id: Mapped[int] = mapped_column(
        ForeignKey("lemmas.id", ondelete="CASCADE"), nullable=False, index=True
    )
    gloss_language: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    translation: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
