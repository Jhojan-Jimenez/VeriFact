import uuid
from datetime import UTC, datetime

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlmodel import select

from src.api.schemas.receipt import ExtractedReceiptData
from src.core.config import settings
from src.core.exceptions import (
    AmountMismatchError,
    DuplicateReceiptError,
    ExpiredReceiptError,
    OrderSettledError,
)
from src.domain.models import (
    Order,
    OrderStatus,
    PaymentReceipt,
    ReceiptVerificationStatus,
)
from src.services.inventory_service import InventoryService


class VerificationService:
    """Orchestrates payment receipt verification, deduplication, and order settlement."""

    @staticmethod
    async def verify_and_settle(
        session: AsyncSession,
        order_id: uuid.UUID,
        extracted: ExtractedReceiptData,
        image_sha256: str,
    ) -> PaymentReceipt:
        # 1. Anti-Fraud Deduplication Check A: Image SHA-256
        stmt_hash = select(PaymentReceipt).where(PaymentReceipt.image_sha256 == image_sha256)
        res_hash = await session.execute(stmt_hash)
        existing_receipt_hash = res_hash.scalar_one_or_none()

        if existing_receipt_hash:
            raise DuplicateReceiptError(
                message="Duplicate image payload: this exact receipt has already been submitted.",
                details={
                    "original_receipt_id": str(existing_receipt_hash.id),
                    "original_order_id": str(existing_receipt_hash.order_id),
                    "bank": existing_receipt_hash.bank_platform,
                    "reference": existing_receipt_hash.reference_number,
                },
            )

        # 2. Anti-Fraud Deduplication Check B: (Bank Platform, Reference Number)
        stmt_ref = select(PaymentReceipt).where(
            PaymentReceipt.bank_platform == extracted.bank_platform,
            PaymentReceipt.reference_number == extracted.reference_number,
            PaymentReceipt.verification_status == ReceiptVerificationStatus.VERIFIED,
        )
        res_ref = await session.execute(stmt_ref)
        existing_receipt_ref = res_ref.scalar_one_or_none()

        if existing_receipt_ref:
            raise DuplicateReceiptError(
                message=f"Duplicate transaction reference '{extracted.reference_number}' already verified for {extracted.bank_platform.value}.",
                details={
                    "original_receipt_id": str(existing_receipt_ref.id),
                    "original_order_id": str(existing_receipt_ref.order_id),
                },
            )

        # 3. Fetch Order with items
        stmt_order = select(Order).where(Order.id == order_id).options(selectinload(Order.items))
        res_order = await session.execute(stmt_order)
        order = res_order.scalar_one_or_none()

        if not order:
            raise ValueError(f"Order {order_id} not found.")

        if order.status != OrderStatus.PENDING:
            raise OrderSettledError(order_id=str(order.id), current_status=order.status.value)

        # 4. Verify Amount Match (Strict integer match in COP)
        if extracted.amount_cop != order.total_amount:
            # Create failed receipt record for audit
            failed_receipt = PaymentReceipt(
                order_id=order.id,
                bank_platform=extracted.bank_platform,
                reference_number=extracted.reference_number,
                extracted_amount=extracted.amount_cop,
                receipt_timestamp=extracted.receipt_timestamp,
                image_sha256=image_sha256,
                verification_status=ReceiptVerificationStatus.REJECTED,
                raw_extracted_text=extracted.raw_text,
                failure_reason=f"Amount mismatch: expected {order.total_amount}, extracted {extracted.amount_cop}",
            )
            session.add(failed_receipt)
            await session.commit()

            raise AmountMismatchError(
                expected=order.total_amount,
                received=extracted.amount_cop,
            )

        # 5. Verify Timestamp Window
        # Tolerance check: receipt timestamp cannot be in the distant past or future
        now_utc = datetime.now(UTC)
        diff_minutes = abs((now_utc - extracted.receipt_timestamp).total_seconds()) / 60
        if diff_minutes > settings.RECEIPT_TIME_TOLERANCE_MINUTES:
            failed_receipt = PaymentReceipt(
                order_id=order.id,
                bank_platform=extracted.bank_platform,
                reference_number=extracted.reference_number,
                extracted_amount=extracted.amount_cop,
                receipt_timestamp=extracted.receipt_timestamp,
                image_sha256=image_sha256,
                verification_status=ReceiptVerificationStatus.REJECTED,
                raw_extracted_text=extracted.raw_text,
                failure_reason=f"Receipt timestamp exceeds {settings.RECEIPT_TIME_TOLERANCE_MINUTES}m window",
            )
            session.add(failed_receipt)
            await session.commit()

            raise ExpiredReceiptError(
                details={"diff_minutes": round(diff_minutes, 1), "tolerance": settings.RECEIPT_TIME_TOLERANCE_MINUTES}
            )

        # 6. Settle Order & Deduct Inventory (Atomic Transaction)
        receipt = PaymentReceipt(
            order_id=order.id,
            bank_platform=extracted.bank_platform,
            reference_number=extracted.reference_number,
            extracted_amount=extracted.amount_cop,
            receipt_timestamp=extracted.receipt_timestamp,
            image_sha256=image_sha256,
            verification_status=ReceiptVerificationStatus.VERIFIED,
            raw_extracted_text=extracted.raw_text,
        )
        session.add(receipt)

        # Transition order to PAID
        order.status = OrderStatus.PAID
        order.updated_at = now_utc

        # Atomically deduct stock
        await InventoryService.deduct_order_stock(session, order)

        await session.commit()
        await session.refresh(receipt)
        return receipt
