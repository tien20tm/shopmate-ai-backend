from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.orders.models import Order, OrderItem


def order_options():
    return selectinload(Order.items).selectinload(
        OrderItem.product
    )


async def list_orders(
    db: AsyncSession,
    customer_id: int,
    limit: int = 20,
    offset: int = 0,
):
    stmt = (
        select(Order)
        .where(Order.customer_id == customer_id)
        .options(order_options())
        .order_by(Order.created_at.desc(), Order.id)
        .limit(limit)
        .offset(offset)
    )

    result = await db.scalars(stmt)
    return result.all()


async def get_order(
    db: AsyncSession,
    customer_id: int,
    order_id: str,
):
    stmt = (
        select(Order)
        .where(
            Order.id == order_id,
            Order.customer_id == customer_id,
        )
        .options(order_options())
    )

    result = await db.scalars(stmt)
    return result.one_or_none()