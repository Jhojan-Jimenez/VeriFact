import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlmodel import select

from src.api.schemas.order import OrderCreate, OrderItemResponse, OrderResponse
from src.core.database import get_session
from src.domain.models import InventoryItem, Order, OrderItem

router = APIRouter(prefix="/orders", tags=["Orders"])


@router.post("", response_model=OrderResponse, status_code=status.HTTP_201_CREATED)
async def create_order(
    payload: OrderCreate,
    session: AsyncSession = Depends(get_session),
):
    """Create a new sales order."""
    # Check if order_number already exists
    existing = await session.execute(select(Order).where(Order.order_number == payload.order_number))
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Order with number '{payload.order_number}' already exists",
        )

    # Validate items and calculate total amount
    total_amount = 0
    order_items: list[OrderItem] = []

    for item in payload.items:
        # Check SKU exists
        res = await session.execute(select(InventoryItem).where(InventoryItem.sku == item.sku))
        inv_item = res.scalar_one_or_none()
        if not inv_item:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Product with SKU '{item.sku}' not found in inventory",
            )

        item_total = item.quantity * item.unit_price
        total_amount += item_total

        order_items.append(
            OrderItem(
                sku=item.sku,
                quantity=item.quantity,
                unit_price=item.unit_price,
            )
        )

    order = Order(
        order_number=payload.order_number,
        total_amount=total_amount,
        items=order_items,
    )
    session.add(order)
    await session.commit()
    await session.refresh(order)

    # Return response with items
    return OrderResponse(
        id=order.id,
        order_number=order.order_number,
        total_amount=order.total_amount,
        status=order.status,
        created_at=order.created_at,
        items=[
            OrderItemResponse(
                id=oi.id,
                sku=oi.sku,
                quantity=oi.quantity,
                unit_price=oi.unit_price,
            )
            for oi in order.items
        ],
    )


@router.get("/{order_id}", response_model=OrderResponse)
async def get_order(
    order_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
):
    """Retrieve an order with its items and status."""
    stmt = select(Order).where(Order.id == order_id).options(selectinload(Order.items))
    res = await session.execute(stmt)
    order = res.scalar_one_or_none()

    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")

    return OrderResponse(
        id=order.id,
        order_number=order.order_number,
        total_amount=order.total_amount,
        status=order.status,
        created_at=order.created_at,
        items=[
            OrderItemResponse(
                id=oi.id,
                sku=oi.sku,
                quantity=oi.quantity,
                unit_price=oi.unit_price,
            )
            for oi in order.items
        ],
    )
