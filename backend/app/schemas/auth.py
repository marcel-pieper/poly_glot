from pydantic import BaseModel, EmailStr, Field


class RequestCodeRequest(BaseModel):
    email: EmailStr


class RequestCodeResponse(BaseModel):
    message: str
    dev_code: str | None = None


class VerifyCodeRequest(BaseModel):
    email: EmailStr
    code: str = Field(min_length=6, max_length=6)


class VerifyCodeResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class DummyPromptRequest(BaseModel):
    prompt: str = Field(min_length=1, max_length=500)


class DummyPromptResponse(BaseModel):
    answer: str
