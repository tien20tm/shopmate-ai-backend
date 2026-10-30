from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from src.models import Base


class Customer(Base):
    __tablename__ = "customers"

    id: Mapped[int] = mapped_column(
        primary_key=True
    )
    full_name: Mapped[str] = mapped_column(
        String(150)
    )
    email: Mapped[str] = mapped_column(
        String(255), unique=True
    )