from fastapi import APIRouter, HTTPException

from src.knowledge import documents
from src.knowledge.schemas import (
    KnowledgeDocumentDetail,
    KnowledgeDocumentSummary,
)


router = APIRouter(
    prefix="/api/v1/knowledge",
    tags=["Knowledge"],
)


@router.get(
    "/documents",
    response_model=list[KnowledgeDocumentSummary],
)
async def list_documents():
    return documents.list_documents()


@router.get(
    "/documents/{slug}",
    response_model=KnowledgeDocumentDetail,
)
async def get_document(slug: str):
    document = documents.get_document(slug)

    if document is None:
        raise HTTPException(404, "Document not found")

    return document
