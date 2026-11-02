from pathlib import Path

from src.knowledge.ingestion import DATA_DIR, get_title
from src.knowledge.schemas import (
    KnowledgeDocumentDetail,
    KnowledgeDocumentSummary,
)


PREVIEW_LENGTH = 160

SOURCES = [
    ("faq", "faq"),
    ("policy", "policies"),
]


def build_preview(content: str) -> str:
    body = " ".join(
        line.strip()
        for line in content.splitlines()
        if line.strip() and not line.startswith("#")
    )

    if len(body) <= PREVIEW_LENGTH:
        return body

    return body[:PREVIEW_LENGTH].rstrip() + "…"


def load_documents(
    data_dir: Path = DATA_DIR,
) -> list[KnowledgeDocumentDetail]:
    documents = []

    for doc_type, folder_name in SOURCES:
        folder = data_dir / folder_name

        if not folder.exists():
            continue

        for file_path in sorted(folder.glob("*.md")):
            content = file_path.read_text(encoding="utf-8")

            # Same format as ingestion, so it matches sources[].document_id.
            document_id = (
                file_path.relative_to(data_dir)
                .with_suffix("")
                .as_posix()
            )

            documents.append(
                KnowledgeDocumentDetail(
                    slug=document_id.replace("/", "-"),
                    document_id=document_id,
                    title=get_title(content, file_path.stem),
                    doc_type=doc_type,
                    content=content,
                )
            )

    return documents


def list_documents() -> list[KnowledgeDocumentSummary]:
    return [
        KnowledgeDocumentSummary(
            slug=doc.slug,
            document_id=doc.document_id,
            title=doc.title,
            doc_type=doc.doc_type,
            preview=build_preview(doc.content),
        )
        for doc in load_documents()
    ]


def get_document(slug: str) -> KnowledgeDocumentDetail | None:
    # Match against known documents; slug never becomes a file path.
    for doc in load_documents():
        if doc.slug == slug:
            return doc

    return None
