from pydantic import BaseModel, Field, field_validator


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=2000)

    @field_validator("message")
    @classmethod
    def validate_message(cls, value: str) -> str:
        value = value.strip()

        if not value:
            raise ValueError("Message cannot be empty")

        return value


class SourceResponse(BaseModel):
    ref: str
    document_id: str
    title: str
    chunk_index: int
    similarity: float


class ChatResponse(BaseModel):
    answer: str
    sources: list[SourceResponse]