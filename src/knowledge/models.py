from sqlalchemy import (
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column
from pgvector.sqlalchemy import VECTOR

from src.models import Base


class KnowledgeChunk(Base):
    __tablename__ = "knowledge_chunks"

    __table_args__ = (
        UniqueConstraint(
            "document_id",
            "chunk_index",
            name="uq_document_chunk",
        ),
    )

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
    )

    document_id: Mapped[str] = mapped_column(
        String(255),
    )

    doc_type: Mapped[str] = mapped_column(
        String(20),
    )

    title: Mapped[str] = mapped_column(
        String(255),
    )

    chunk_index: Mapped[int] = mapped_column(
        Integer,
    )

    content: Mapped[str] = mapped_column(
        Text,
    )

    content_hash: Mapped[str] = mapped_column(
        String(64),
    )

    embedding: Mapped[list[float]] = mapped_column(
        VECTOR(1536),
    )