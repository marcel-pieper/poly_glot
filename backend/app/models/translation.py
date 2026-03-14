from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Translation(Base):
    __tablename__ = "translations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    language_space_id: Mapped[int] = mapped_column(
        ForeignKey("language_spaces.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    from_text: Mapped[str] = mapped_column(Text, nullable=False)
    to_text: Mapped[str] = mapped_column(Text, nullable=False)
    from_language: Mapped[str] = mapped_column(String(32), nullable=False)
    to_language: Mapped[str] = mapped_column(String(32), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
