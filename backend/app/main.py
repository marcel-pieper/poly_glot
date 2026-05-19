import logging
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request

from app.api.routes_ai import router as ai_router
from app.api.routes_auth import router as auth_router
from app.api.routes_chat import router as chat_router
from app.api.routes_explain import router as explain_router
from app.api.routes_users import router as users_router
from app.core.config import get_settings
from app.core.logging_config import configure_logging

settings = get_settings()
configure_logging(settings)
logger = logging.getLogger("polyglot.api")


@asynccontextmanager
async def lifespan(_: FastAPI):
    logger.info("Starting %s in %s mode", settings.app_name, settings.app_env)
    yield


app = FastAPI(title=settings.app_name, lifespan=lifespan)


@app.middleware("http")
async def log_requests(request: Request, call_next):
    start = time.perf_counter()
    try:
        response = await call_next(request)
    except Exception:
        logger.exception("Request failed: %s %s", request.method, request.url.path)
        raise

    duration_ms = (time.perf_counter() - start) * 1000
    logger.info(
        "%s %s -> %s (%.1fms)",
        request.method,
        request.url.path,
        response.status_code,
        duration_ms,
    )
    return response


@app.get("/health")
def health():
    return {"status": "ok"}


app.include_router(auth_router, prefix="/api")
app.include_router(users_router, prefix="/api")
app.include_router(ai_router, prefix="/api")
app.include_router(chat_router, prefix="/api")
app.include_router(explain_router, prefix="/api")
