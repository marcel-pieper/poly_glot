from pydantic import BaseModel, Field


class TranslateRequest(BaseModel):
    text: str = Field(min_length=1, max_length=4000)


class TranslateResponse(BaseModel):
    source_text: str
    translated_text: str
    status: str
