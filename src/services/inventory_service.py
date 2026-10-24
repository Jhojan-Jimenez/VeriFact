from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from src.core.exceptions import InsufficientStockError
from src.domain.models import InventoryItem, Order, StockMovement, StockMovementType


class InventoryService:
    """Manages inventory items and stock movements."""

    @staticmethod
    async def create_or_update_item(
        session: AsyncSession, sku: str, name: str, unit_price: int, initial_stock: int = 0
    ) -> InventoryItem:
        statement = select(InventoryItem).where(InventoryItem.sku == sku)
        result = await session.execute(statement)
        item = result.scalar_one_or_none()

        if item:
            item.name = name
            item.unit_price = unit_price
            item.stock += initial_stock
        else:
            item = InventoryItem(
                sku=sku,
                name=name,
                unit_price=unit_price,
                stock=initial_stock,
            )
            session.add(item)

        await session.flush()
        return item

    @staticmethod
    async def deduct_order_stock(session: AsyncSession, order: Order) -> list[StockMovement]:
        """Atomically deduct stock for all items in an order."""
        movements: list[StockMovement] = []

        # Iterate over order items
        for order_item in order.items:
            statement = select(InventoryItem).where(InventoryItem.sku == order_item.sku)
            result = await session.execute(statement)
            inv_item = result.scalar_one_or_none()

            if not inv_item or inv_item.stock < order_item.quantity:
                available = inv_item.stock if inv_item else 0
                raise InsufficientStockError(
                    sku=order_item.sku,
                    requested=order_item.quantity,
                    available=available,
                )

            # Decrement stock
            inv_item.stock -= order_item.quantity

            # Register Kardex stock movement
            movement = StockMovement(
                sku=order_item.sku,
                order_id=order.id,
                quantity_change=-order_item.quantity,
                movement_type=StockMovementType.SALE_DEDUCTION,
            )
            session.add(movement)
            movements.append(movement)

        await session.flush()
        return movements
