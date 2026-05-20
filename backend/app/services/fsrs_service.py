"""Thin wrapper around `fsrs.Scheduler` so callers never import FSRS directly.

We persist FSRS state as native columns on `UserVocab` (state/step/stability/
difficulty/due/last_review), and reconstruct an `fsrs.Card` on demand to feed
the scheduler. This isolates the library so the scheduler can be swapped or
upgraded without touching routes.

The scheduler itself is stateless across calls (parameters are immutable), so
a single module-level instance is safe to share.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from fsrs import Card, Rating, Scheduler, State

_scheduler = Scheduler()


@dataclass(frozen=True)
class CardState:
    """Mirror of the FSRS-owned columns on `UserVocab`."""

    state: int
    step: int | None
    stability: float | None
    difficulty: float | None
    due: datetime
    last_review: datetime | None

    def to_columns(self) -> dict[str, Any]:
        return {
            "state": self.state,
            "step": self.step,
            "stability": self.stability,
            "difficulty": self.difficulty,
            "due": self.due,
            "last_review": self.last_review,
        }


def _card_to_state(card: Card) -> CardState:
    return CardState(
        state=int(card.state.value),
        step=card.step,
        stability=card.stability,
        difficulty=card.difficulty,
        due=card.due,
        last_review=card.last_review,
    )


def new_card_state() -> CardState:
    """Initial FSRS state for a brand-new card. Due immediately upon creation."""
    return _card_to_state(Card())


def load_card(*, state: int, step: int | None, stability: float | None,
               difficulty: float | None, due: datetime, last_review: datetime | None) -> Card:
    """Rebuild an `fsrs.Card` from the columns we store on `UserVocab`.

    Datetimes coming back from Postgres are timezone-aware UTC; FSRS requires
    UTC, so we coerce defensively in case a row was inserted naive somehow.
    """

    def _ensure_utc(value: datetime | None) -> datetime | None:
        if value is None:
            return None
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc)

    return Card(
        state=State(state),
        step=step,
        stability=stability,
        difficulty=difficulty,
        due=_ensure_utc(due) or datetime.now(timezone.utc),
        last_review=_ensure_utc(last_review),
    )


def apply_review(card: Card, rating: Rating) -> tuple[CardState, dict[str, Any]]:
    """Score a review and return the updated state plus a serializable log entry.

    The log dict is what a future review-history endpoint would store; today we
    just return it so callers can persist it whenever that feature lands.
    """
    updated_card, review_log = _scheduler.review_card(card, rating)
    return _card_to_state(updated_card), review_log.to_dict()


__all__ = [
    "Rating",
    "State",
    "CardState",
    "new_card_state",
    "load_card",
    "apply_review",
]
