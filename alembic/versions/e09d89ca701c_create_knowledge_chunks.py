"""create knowledge chunks

Revision ID: e09d89ca701c
Revises: b8cf6ac16998
Create Date: 2026-10-30 21:18:08.607652

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e09d89ca701c'
down_revision: Union[str, Sequence[str], None] = 'b8cf6ac16998'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass


import sqlalchemy as sa
from alembic import op
from pgvector.sqlalchemy import VECTOR


def upgrade() -> None:
    op.execute(
        "CREATE EXTENSION IF NOT EXISTS vector"
    )

    op.create_table(
        "knowledge_chunks",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "document_id",
            sa.String(255),
            nullable=False,
        ),
        sa.Column(
            "doc_type",
            sa.String(20),
            nullable=False,
        ),
        sa.Column(
            "title",
            sa.String(255),
            nullable=False,
        ),
        sa.Column(
            "chunk_index",
            sa.Integer(),
            nullable=False,
        ),
        sa.Column(
            "content",
            sa.Text(),
            nullable=False,
        ),
        sa.Column(
            "content_hash",
            sa.String(64),
            nullable=False,
        ),
        sa.Column(
            "embedding",
            VECTOR(1536),
            nullable=False,
        ),
        sa.UniqueConstraint(
            "document_id",
            "chunk_index",
            name="uq_document_chunk",
        ),
    )


def downgrade() -> None:
    op.drop_table("knowledge_chunks")