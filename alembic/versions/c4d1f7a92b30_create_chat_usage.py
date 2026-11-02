"""create chat usage

Revision ID: c4d1f7a92b30
Revises: e09d89ca701c
Create Date: 2026-11-03 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c4d1f7a92b30'
down_revision: Union[str, Sequence[str], None] = 'e09d89ca701c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "chat_usage",
        sa.Column("day", sa.Date(), nullable=False),
        sa.Column("scope", sa.String(80), nullable=False),
        sa.Column("count", sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint("day", "scope"),
    )


def downgrade() -> None:
    op.drop_table("chat_usage")
