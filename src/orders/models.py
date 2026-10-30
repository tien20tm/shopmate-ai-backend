from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    String,
    ForeignKey,
    DateTime,
    Numeric,
    CheckConstraint,
    func,
)
from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    relationship,
)

from src.models import Base
from src.products.models import Product


class Order(Base):
    __tablename__ = "orders"

    __table_args__ = (
        CheckConstraint(
            "status IN ('pending', 'processing', "
            "'shipped', 'delivered', 'cancelled')",
            name="ck_orders_status",
        ),
    )

    id: Mapped[str] = mapped_column(
        String(30), primary_key=True
    )
    customer_id: Mapped[int] = mapped_column(
        ForeignKey("customers.id"), index=True
    )
    status: Mapped[str] = mapped_column(
        String(30)
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
    delivered_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    items: Mapped[list["OrderItem"]] = relationship(
        back_populates="order",
        cascade="all, delete-orphan",
    )


class OrderItem(Base):
    __tablename__ = "order_items"

    id: Mapped[int] = mapped_column(
        primary_key=True
    )
    order_id: Mapped[str] = mapped_column(
        ForeignKey("orders.id"), index=True
    )
    product_id: Mapped[int] = mapped_column(
        ForeignKey("products.id")
    )
    quantity: Mapped[int] = mapped_column()
    unit_price: Mapped[Decimal] = mapped_column(
        Numeric(12, 2)
    )

    order: Mapped["Order"] = relationship(
        back_populates="items"
    )
    product: Mapped["Product"] = relationship()