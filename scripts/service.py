from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.orders.models import Order


async def list_orders(
    db: AsyncSession,
    customer_id: int,
    limit: int = 20,
    offset: int = 0,
):
    stmt = (
        select(Order)
        .where(Order.customer_id == customer_id)
        .options(selectinload(Order.items))
        .order_by(Order.created_at.desc())
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
        .options(selectinload(Order.items))
    )

    result = await db.scalars(stmt)
    return result.one_or_none()