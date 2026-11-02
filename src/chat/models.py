from datetime import date

from sqlalchemy import Date, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from src.models import Base


class ChatUsage(Base):
    __tablename__ = "chat_usage"

    day: Mapped[date] = mapped_column(
        Date,
        primary_key=True,
    )

    scope: Mapped[str] = mapped_column(
        String(80),
        primary_key=True,
    )

    count: Mapped[int] = mapped_column(
        Integer,
    )
