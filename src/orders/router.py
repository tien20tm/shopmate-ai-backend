from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.config import settings
from src.database import get_db
from src.orders import service
from src.orders.schemas import OrderResponse


order_router = APIRouter(
    prefix="/api/v1/orders",
    tags=["Orders"],
)


@order_router.get("", response_model=list[OrderResponse])
async def list_orders(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    return await service.list_orders(
        db=db,
        customer_id=settings.DEMO_CUSTOMER_ID,
        limit=limit,
        offset=offset,
    )


@order_router.get("/{order_id}", response_model=OrderResponse)
async def get_order(
    order_id: str,
    db: AsyncSession = Depends(get_db),
):
    order = await service.get_order(
        db=db,
        customer_id=settings.DEMO_CUSTOMER_ID,
        order_id=order_id,
    )

    if order is None:
        raise HTTPException(404, "Order not found")

    return order