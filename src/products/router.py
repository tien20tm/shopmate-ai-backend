from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import get_db
from src.products import service
from src.products.schemas import ProductResponse


router = APIRouter(
    prefix="/api/v1/products",
    tags=["Products"],
)


@router.get("", response_model=list[ProductResponse])
async def list_products(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    return await service.list_products(db, limit, offset)


@router.get("/{product_id}", response_model=ProductResponse)
async def get_product(
    product_id: int,
    db: AsyncSession = Depends(get_db),
):
    product = await service.get_product(db, product_id)

    if not product:
        raise HTTPException(404, "Product not found")

    return product