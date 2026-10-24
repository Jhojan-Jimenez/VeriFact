import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from src.core.exceptions import InsufficientStockError
from src.domain.models import InventoryItem, Order, OrderItem
from src.services.inventory_service import InventoryService


@pytest.mark.asyncio
async def test_inventory_creation_and_deduction(db_session: AsyncSession):
    # 1. Create item
    item = await InventoryService.create_or_update_item(
        session=db_session,
        sku="CAMISA-M",
        name="Camisa de lino",
        unit_price=45000,
        initial_stock=10,
    )
    await db_session.commit()

    assert item.stock == 10

    # 2. Create order with 3 units
    order = Order(
        order_number="ORD-TEST-01",
        total_amount=135000,
        items=[
            OrderItem(sku="CAMISA-M", quantity=3, unit_price=45000),
        ],
    )
    db_session.add(order)
    await db_session.commit()
    await db_session.refresh(order)

    # 3. Deduct stock
    movements = await InventoryService.deduct_order_stock(db_session, order)
    await db_session.commit()

    assert len(movements) == 1
    assert movements[0].quantity_change == -3

    # 4. Verify updated stock
    res = await db_session.execute(select(InventoryItem).where(InventoryItem.sku == "CAMISA-M"))
    updated = res.scalar_one()
    assert updated.stock == 7


@pytest.mark.asyncio
async def test_inventory_insufficient_stock_raises_error(db_session: AsyncSession):
    # Item with only 1 unit
    await InventoryService.create_or_update_item(
        session=db_session,
        sku="PANTALON-32",
        name="Pantalón Slim",
        unit_price=80000,
        initial_stock=1,
    )
    await db_session.commit()

    # Order requesting 5 units
    order = Order(
        order_number="ORD-TEST-02",
        total_amount=400000,
        items=[
            OrderItem(sku="PANTALON-32", quantity=5, unit_price=80000),
        ],
    )
    db_session.add(order)
    await db_session.commit()
    await db_session.refresh(order)

    # Deduction must fail with InsufficientStockError
    with pytest.raises(InsufficientStockError) as exc_info:
        await InventoryService.deduct_order_stock(db_session, order)

    assert exc_info.value.code == "INSUFFICIENT_STOCK"
