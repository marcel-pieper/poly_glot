from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.auth import (
    RequestCodeRequest,
    RequestCodeResponse,
    VerifyCodeRequest,
    VerifyCodeResponse,
)
from app.services.auth_service import (
    create_access_token,
    create_verification_code,
    verify_code_and_get_user,
)
from app.services.email_service import send_verification_code_email

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/request-code", response_model=RequestCodeResponse)
def request_code(payload: RequestCodeRequest, db: Session = Depends(get_db)):
    code = create_verification_code(db, payload.email)
    send_verification_code_email(payload.email, code)
    return RequestCodeResponse(message="Verification code generated and logged in backend output.", dev_code=code)


@router.post("/verify-code", response_model=VerifyCodeResponse)
def verify_code(payload: VerifyCodeRequest, db: Session = Depends(get_db)):
    user = verify_code_and_get_user(db, payload.email, payload.code)
    if not user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or expired code")

    token = create_access_token(user.id, user.email)
    return VerifyCodeResponse(access_token=token)
