from datetime import datetime

from sqlalchemy import (
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    SmallInteger,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class UserVocab(Base):
    """Per-user (via language_space) vocabulary card with FSRS scheduling state.

    Identity is `(language_space_id, lemma_id)`. Authorization is enforced by
    joining `language_spaces.user_id == current_user.id` — no separate
    `user_id` column is stored.

    FSRS fields mirror `fsrs.Card`:
      - state: 1=Learning, 2=Review, 3=Relearning
      - step: current step index within learning/relearning (nullable in Review)
      - stability / difficulty: FSRS scheduler state (nullable for fresh cards)
      - due: when this card is next scheduled to appear
      - last_review: timestamp of the most recent review (nullable)
    """

    __tablename__ = "user_vocab"
    __table_args__ = (
        UniqueConstraint(
            "language_space_id", "lemma_id", name="uq_user_vocab_space_lemma"
        ),
        Index("ix_user_vocab_space_due", "language_space_id", "due"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    language_space_id: Mapped[int] = mapped_column(
        ForeignKey("language_spaces.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    lemma_id: Mapped[int] = mapped_column(
        ForeignKey("lemmas.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    state: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    step: Mapped[int | None] = mapped_column(SmallInteger, nullable=True)
    stability: Mapped[float | None] = mapped_column(Float, nullable=True)
    difficulty: Mapped[float | None] = mapped_column(Float, nullable=True)
    due: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    last_review: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    review_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    lapse_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )
