from fastapi import APIRouter, HTTPException


order_router = APIRouter(prefix="/orders", tags=["orders"])


@order_router.get("/", response_model=list[str])
async def read_orders():
    return ["foo", "bar"]


@order_router.get("/{item_id}")
async def read_item(item_id: int, skip: int , limit: int = 10, q : str | None = None):
    return {"item_id": item_id, "skip": skip, "limit": limit, "q": q}