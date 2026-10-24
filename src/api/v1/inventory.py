from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from src.api.schemas.inventory import (
    InventoryItemCreate,
    InventoryItemResponse,
    StockMovementResponse,
)
from src.core.database import get_session
from src.domain.models import InventoryItem, StockMovement
from src.services.inventory_service import InventoryService

router = APIRouter(prefix="/inventory", tags=["Inventory"])


@router.post("", response_model=InventoryItemResponse, status_code=status.HTTP_201_CREATED)
async def create_or_update_inventory_item(
    payload: InventoryItemCreate,
    session: AsyncSession = Depends(get_session),
):
    """Register or restock an inventory item."""
    item = await InventoryService.create_or_update_item(
        session=session,
        sku=payload.sku,
        name=payload.name,
        unit_price=payload.unit_price,
        initial_stock=payload.stock,
    )
    await session.commit()
    await session.refresh(item)
    return item


@router.get("", response_model=list[InventoryItemResponse])
async def list_inventory(
    session: AsyncSession = Depends(get_session),
):
    """List all inventory items."""
    stmt = select(InventoryItem)
    res = await session.execute(stmt)
    return res.scalars().all()


@router.get("/{sku}/history", response_model=list[StockMovementResponse])
async def get_sku_movement_history(
    sku: str,
    session: AsyncSession = Depends(get_session),
):
    """Retrieve audit trail of stock movements for a specific SKU."""
    item_res = await session.execute(select(InventoryItem).where(InventoryItem.sku == sku))
    if not item_res.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"SKU '{sku}' not found")

    stmt = select(StockMovement).where(StockMovement.sku == sku).order_by(StockMovement.timestamp.desc())
    res = await session.execute(stmt)
    return res.scalars().all()
