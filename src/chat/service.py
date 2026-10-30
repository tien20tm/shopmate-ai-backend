from src.knowledge.rag import answer_from_knowledge


async def chat(message: str) -> dict:
    return await answer_from_knowledge(
        question=message,
        top_k=4,
    )