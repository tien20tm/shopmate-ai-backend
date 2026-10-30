from decimal import Decimal

from sqlalchemy import String, Numeric
from sqlalchemy.orm import Mapped, mapped_column

from src.models import Base


class Product(Base):
    __tablename__ = "products"

    id: Mapped[int] = mapped_column(
        primary_key=True
    )
    sku: Mapped[str] = mapped_column(
        String(50), unique=True
    )
    name: Mapped[str] = mapped_column(
        String(255)
    )
    price: Mapped[Decimal] = mapped_column(
        Numeric(12, 2)
    )