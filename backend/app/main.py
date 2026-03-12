from fastapi import FastAPI

from app.api.routes_ai import router as ai_router
from app.api.routes_auth import router as auth_router
from app.api.routes_users import router as users_router
from app.core.config import get_settings

settings = get_settings()
app = FastAPI(title=settings.app_name)


@app.get("/health")
def health():
    return {"status": "ok"}


app.include_router(auth_router, prefix=settings.api_v1_prefix)
app.include_router(users_router, prefix=settings.api_v1_prefix)
app.include_router(ai_router, prefix=settings.api_v1_prefix)
