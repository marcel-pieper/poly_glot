from __future__ import annotations

from datetime import datetime
from enum import Enum

from sqlalchemy import DateTime, Enum as SqlEnum, ForeignKey, Integer, String, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class ThreadType(str, Enum):
    CHAT = "chat"
    EXPLAIN = "explain"
    PRACTICE = "practice"


class Thread(Base):
    __tablename__ = "threads"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    parent_thread_id: Mapped[int | None] = mapped_column(
        ForeignKey("threads.id", ondelete="SET NULL"), nullable=True, index=True
    )
    title: Mapped[str | None] = mapped_column(String(255), nullable=True)
    type: Mapped[ThreadType] = mapped_column(
        SqlEnum(ThreadType, name="thread_type_enum"),
        nullable=False,
        index=True,
    )
    seed: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    parent_thread: Mapped["Thread | None"] = relationship(remote_side=[id], backref="child_threads")
