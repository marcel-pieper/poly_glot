from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.language_space import LanguageSpace
from app.models.thread import Thread, ThreadType
from app.models.user import User


def require_user_thread(
    thread_id: int,
    user: User,
    db: Session,
    required_type: ThreadType | None = None,
) -> Thread:
    thread = db.get(Thread, thread_id)
    if not thread:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Thread not found")

    space = db.get(LanguageSpace, thread.language_space_id)
    if not space or space.user_id != user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    if required_type and thread.type != required_type:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Thread is not a {required_type.value} thread",
        )

    return thread
