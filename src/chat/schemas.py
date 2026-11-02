from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    session_id: str = Field(
        min_length=1,
        max_length=64,
        pattern=r"^[a-zA-Z0-9_-]+$",
    )

    message: str = Field(
        min_length=1,
        max_length=2000,
    )


class SourceResponse(BaseModel):
    document_id: str
    title: str
    chunk_index: int
    similarity: float


class ChatResponse(BaseModel):
    answer: str
    sources: list[SourceResponse]
    tools_used: list[str]