import uuid
from datetime import UTC, datetime
from enum import Enum

from sqlmodel import Field, Relationship, SQLModel


def utc_now() -> datetime:
    return datetime.now(UTC)


class OrderStatus(str, Enum):
    PENDING = "PENDING"
    PAID = "PAID"
    CANCELLED = "CANCELLED"
    REJECTED = "REJECTED"


class BankPlatform(str, Enum):
    NEQUI = "NEQUI"
    DAVIPLATA = "DAVIPLATA"
    BANCOLOMBIA = "BANCOLOMBIA"
    BRE_B = "BRE_B"
    DIAN_INVOICE = "DIAN_INVOICE"
    UNKNOWN = "UNKNOWN"


class ReceiptVerificationStatus(str, Enum):
    VERIFIED = "VERIFIED"
    REJECTED = "REJECTED"
    DUPLICATE = "DUPLICATE"
    FLAGGED_FRAUD = "FLAGGED_FRAUD"
    UNCONFIRMED = "UNCONFIRMED"


class StockMovementType(str, Enum):
    SALE_DEDUCTION = "SALE_DEDUCTION"
    RESTOCK = "RESTOCK"
    ADJUSTMENT = "ADJUSTMENT"


class InventoryItem(SQLModel, table=True):
    __tablename__ = "inventory_items"

    sku: str = Field(primary_key=True, index=True)
    name: str = Field(index=True)
    unit_price: int = Field(ge=0, description="Price in COP integer")
    stock: int = Field(default=0, ge=0)
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)


class OrderItem(SQLModel, table=True):
    __tablename__ = "order_items"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    order_id: uuid.UUID = Field(foreign_key="orders.id", index=True)
    sku: str = Field(foreign_key="inventory_items.sku")
    quantity: int = Field(gt=0)
    unit_price: int = Field(ge=0)

    # Relationships with eager selectin loading for async compatibility
    order: "Order" = Relationship(back_populates="items", sa_relationship_kwargs={"lazy": "selectin"})


class Order(SQLModel, table=True):
    __tablename__ = "orders"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    order_number: str = Field(unique=True, index=True)
    total_amount: int = Field(ge=0, description="Total amount in COP")
    status: OrderStatus = Field(default=OrderStatus.PENDING, index=True)
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)

    # Relationships with eager selectin loading
    items: list[OrderItem] = Relationship(back_populates="order", sa_relationship_kwargs={"lazy": "selectin"})
    receipts: list["PaymentReceipt"] = Relationship(back_populates="order", sa_relationship_kwargs={"lazy": "selectin"})


class PaymentReceipt(SQLModel, table=True):
    __tablename__ = "payment_receipts"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    order_id: uuid.UUID | None = Field(default=None, foreign_key="orders.id", nullable=True, index=True)
    bank_platform: BankPlatform = Field(default=BankPlatform.UNKNOWN, index=True)
    reference_number: str = Field(index=True)
    extracted_amount: int = Field(ge=0, description="Amount in COP")
    receipt_timestamp: datetime = Field(default_factory=utc_now)
    image_sha256: str = Field(unique=True, index=True)
    verification_status: ReceiptVerificationStatus = Field(default=ReceiptVerificationStatus.UNCONFIRMED, index=True)
    raw_extracted_text: str = Field(default="")
    failure_reason: str | None = Field(default=None, nullable=True)
    created_at: datetime = Field(default_factory=utc_now)

    # Relationships with eager selectin loading
    order: Order | None = Relationship(back_populates="receipts", sa_relationship_kwargs={"lazy": "selectin"})


class StockMovement(SQLModel, table=True):
    __tablename__ = "stock_movements"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    sku: str = Field(foreign_key="inventory_items.sku", index=True)
    order_id: uuid.UUID | None = Field(default=None, foreign_key="orders.id", nullable=True, index=True)
    quantity_change: int = Field(description="Negative for sales, positive for restock")
    movement_type: StockMovementType = Field(default=StockMovementType.SALE_DEDUCTION)
    timestamp: datetime = Field(default_factory=utc_now)
