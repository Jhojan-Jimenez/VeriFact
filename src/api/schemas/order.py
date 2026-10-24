import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from src.domain.models import OrderStatus


class OrderItemCreate(BaseModel):
    sku: str
    quantity: int = Field(gt=0)
    unit_price: int = Field(ge=0)


class OrderCreate(BaseModel):
    order_number: str
    items: list[OrderItemCreate] = Field(min_length=1)


class OrderQuickCreate(BaseModel):
    order_number: str
    total_amount: int = Field(gt=0, description="Total amount in COP")


class OrderItemResponse(BaseModel):
    id: uuid.UUID
    sku: str
    quantity: int
    unit_price: int


class OrderResponse(BaseModel):
    id: uuid.UUID
    order_number: str
    total_amount: int
    status: OrderStatus
    created_at: datetime
    items: list[OrderItemResponse] = []
