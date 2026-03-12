from fastapi import APIRouter

from app.schemas.auth import DummyPromptRequest, DummyPromptResponse
from app.services.openai_service import get_dummy_completion

router = APIRouter(prefix="/ai", tags=["ai"])


@router.post("/dummy", response_model=DummyPromptResponse)
def dummy_prompt(payload: DummyPromptRequest):
    return DummyPromptResponse(answer=get_dummy_completion(payload.prompt))
