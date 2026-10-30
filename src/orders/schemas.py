from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict

from src.products.schemas import ProductResponse


class OrderItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    product: ProductResponse
    quantity: int
    unit_price: Decimal


class OrderResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    status: str
    created_at: datetime
    delivered_at: datetime | None
    items: list[OrderItemResponse]