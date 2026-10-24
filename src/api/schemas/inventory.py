import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from src.domain.models import StockMovementType


class InventoryItemCreate(BaseModel):
    sku: str
    name: str
    unit_price: int = Field(ge=0)
    stock: int = Field(default=0, ge=0)


class InventoryItemResponse(BaseModel):
    sku: str
    name: str
    unit_price: int
    stock: int
    is_active: bool
    created_at: datetime


class StockMovementResponse(BaseModel):
    id: uuid.UUID
    sku: str
    order_id: uuid.UUID | None
    quantity_change: int
    movement_type: StockMovementType
    timestamp: datetime
