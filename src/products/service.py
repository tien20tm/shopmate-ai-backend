from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.products.models import Product


async def list_products(
    db: AsyncSession,
    limit: int = 20,
    offset: int = 0,
):
    stmt = (
        select(Product)
        .order_by(Product.id)
        .limit(limit)
        .offset(offset)
    )

    result = await db.scalars(stmt)
    return result.all()


async def get_product(
    db: AsyncSession,
    product_id: int,
):
    return await db.get(Product, product_id)