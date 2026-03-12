import hashlib
import random
from datetime import UTC, datetime, timedelta

import jwt
from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.email_verification_code import EmailVerificationCode
from app.models.user import User

settings = get_settings()


def generate_code() -> str:
    return f"{random.randint(0, 999999):06d}"


def hash_code(email: str, code: str) -> str:
    digest_input = f"{email.lower()}:{code}:{settings.jwt_secret}"
    return hashlib.sha256(digest_input.encode("utf-8")).hexdigest()


def create_verification_code(db: Session, email: str) -> str:
    normalized_email = email.lower().strip()
    code = generate_code()
    db_code = EmailVerificationCode(
        email=normalized_email,
        code_hash=hash_code(normalized_email, code),
        expires_at=datetime.now(UTC) + timedelta(minutes=settings.verification_code_ttl_minutes),
    )
    db.add(db_code)
    db.commit()
    return code


def verify_code_and_get_user(db: Session, email: str, code: str) -> User | None:
    normalized_email = email.lower().strip()
    query = (
        select(EmailVerificationCode)
        .where(EmailVerificationCode.email == normalized_email)
        .where(EmailVerificationCode.consumed_at.is_(None))
        .order_by(desc(EmailVerificationCode.created_at))
    )
    db_code = db.execute(query).scalars().first()
    if not db_code:
        return None

    if db_code.expires_at < datetime.now(UTC):
        return None

    if db_code.code_hash != hash_code(normalized_email, code):
        return None

    db_code.consumed_at = datetime.now(UTC)
    user = db.execute(select(User).where(User.email == normalized_email)).scalars().first()
    if not user:
        user = User(email=normalized_email, is_verified=True)
        db.add(user)
    else:
        user.is_verified = True

    db.commit()
    db.refresh(user)
    return user


def create_access_token(user_id: int, email: str) -> str:
    expires_at = datetime.now(UTC) + timedelta(minutes=settings.jwt_expire_minutes)
    payload = {"sub": str(user_id), "email": email, "exp": expires_at}
    return jwt.encode(payload, settings.jwt_secret, algorithm="HS256")


def get_current_user(db: Session, token: str) -> User | None:
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=["HS256"])
        user_id = int(payload.get("sub"))
    except (jwt.PyJWTError, TypeError, ValueError):
        return None

    return db.execute(select(User).where(User.id == user_id)).scalars().first()
