from fastapi import APIRouter

from src.chat.schemas import ChatRequest, ChatResponse
from src.chat.service import chat


router = APIRouter(
    prefix="/api/v1/chat",
    tags=["Chat"],
)


@router.post("", response_model=ChatResponse)
async def ask_question(request: ChatRequest):
    return await chat(request.message)