from pydantic import BaseModel


class KnowledgeDocumentSummary(BaseModel):
    slug: str
    document_id: str
    title: str
    doc_type: str
    preview: str


class KnowledgeDocumentDetail(BaseModel):
    slug: str
    document_id: str
    title: str
    doc_type: str
    content: str
