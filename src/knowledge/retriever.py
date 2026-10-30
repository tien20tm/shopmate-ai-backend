from sqlalchemy import select

from src.database import AsyncSessionLocal
from src.knowledge.embeddings import get_embeddings
from src.knowledge.models import KnowledgeChunk


async def search_knowledge(
    query: str,
    top_k: int = 4,
)-> list[dict]:
    if not query.strip():
        raise ValueError("Query cannot be empty")

    if not 1 <= top_k <= 20:
        raise ValueError("top_k must be between 1 and 20")

    embedder = get_embeddings()

    # 1. Embed user query
    query_vector = await embedder.aembed_query(query)

    # 2. Calculate cosine distance
    distance = KnowledgeChunk.embedding.cosine_distance(
        query_vector
    )

    # 3. Find nearest chunks
    stmt = (
        select(
            KnowledgeChunk.document_id,
            KnowledgeChunk.title,
            KnowledgeChunk.content,
            (1 - distance).label("similarity"),
            KnowledgeChunk.chunk_index,
        )
        .order_by(distance)
        .limit(top_k)
    )

    async with AsyncSessionLocal() as db:
        result = await db.execute(stmt)
        rows = result.all()

    return [
        {
            "document_id": row.document_id,
            "title": row.title,
            "content": row.content,
            "similarity": float(row.similarity),
            "chunk_index": row.chunk_index,
        }
        for row in rows
    ]