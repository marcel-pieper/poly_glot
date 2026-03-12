from fastapi import APIRouter, Depends

from app.api.deps import current_user
from app.models.user import User
from app.schemas.user import UserOut

router = APIRouter(tags=["users"])


@router.get("/me", response_model=UserOut)
def me(user: User = Depends(current_user)):
    return user
