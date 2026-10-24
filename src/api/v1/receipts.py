import uuid

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from src.api.schemas.receipt import ReceiptInspectionResponse, ReceiptVerificationResponse
from src.core.database import get_session
from src.domain.models import PaymentReceipt, ReceiptVerificationStatus
from src.services.verification_service import VerificationService
from src.services.vision_service import VisionService

router = APIRouter(prefix="/receipts", tags=["Receipt Verification"])
vision_service = VisionService()


@router.post("/inspect", response_model=ReceiptInspectionResponse, status_code=status.HTTP_200_OK)
async def inspect_receipt(
    file: UploadFile = File(..., description="Receipt image file to inspect without requiring an order"),
    session: AsyncSession = Depends(get_session),
):
    """Simulate and inspect a receipt: extract financial details without order dependency."""
    contents = await file.read()
    if not contents or len(contents) < 50:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file is empty or corrupted",
        )

    # 1. Run Vision OCR extraction
    extracted_data, image_sha256 = vision_service.process_receipt(contents)

    # 2. Check duplicate status in background without rejecting
    stmt = select(PaymentReceipt).where(
        (PaymentReceipt.image_sha256 == image_sha256)
        | (
            (PaymentReceipt.bank_platform == extracted_data.bank_platform)
            & (PaymentReceipt.reference_number == extracted_data.reference_number)
            & (PaymentReceipt.verification_status == ReceiptVerificationStatus.VERIFIED)
        )
    )
    res = await session.execute(stmt)
    existing = res.scalar_one_or_none()

    is_duplicate = existing is not None
    dup_info = None
    if existing:
        dup_info = {
            "existing_receipt_id": str(existing.id),
            "existing_order_id": str(existing.order_id) if existing.order_id else None,
            "bank": existing.bank_platform.value,
            "reference": existing.reference_number,
        }

    return ReceiptInspectionResponse(
        bank_platform=extracted_data.bank_platform,
        reference_number=extracted_data.reference_number,
        amount_cop=extracted_data.amount_cop,
        receipt_timestamp=extracted_data.receipt_timestamp,
        concept=extracted_data.concept,
        image_sha256=image_sha256,
        raw_text_snippet=extracted_data.raw_text[:400] if extracted_data.raw_text else "",
        is_duplicate=is_duplicate,
        duplicate_info=dup_info,
    )


@router.get("", response_model=list[ReceiptVerificationResponse])
async def list_receipts(
    verification_status: ReceiptVerificationStatus | None = None,
    limit: int = 50,
    session: AsyncSession = Depends(get_session),
):
    """List processed payment receipts ordered by creation timestamp descending."""
    stmt = select(PaymentReceipt).order_by(PaymentReceipt.created_at.desc()).limit(limit)
    if verification_status:
        stmt = stmt.where(PaymentReceipt.verification_status == verification_status)

    res = await session.execute(stmt)
    receipts = res.scalars().all()

    return [
        ReceiptVerificationResponse(
            id=r.id,
            order_id=r.order_id,
            bank_platform=r.bank_platform,
            reference_number=r.reference_number,
            extracted_amount=r.extracted_amount,
            receipt_timestamp=r.receipt_timestamp,
            verification_status=r.verification_status,
            image_sha256=r.image_sha256,
            failure_reason=r.failure_reason,
            created_at=r.created_at,
        )
        for r in receipts
    ]


@router.post("/verify", response_model=ReceiptVerificationResponse, status_code=status.HTTP_200_OK)
async def verify_receipt(
    order_id: uuid.UUID = Form(..., description="ID of the sales order to reconcile"),
    file: UploadFile = File(..., description="Receipt image file (JPEG, PNG, WEBP)"),
    session: AsyncSession = Depends(get_session),
):
    """Upload a payment slip/voucher image and reconcile against an existing order."""
    # 1. Read binary content
    contents = await file.read()
    if not contents or len(contents) < 50:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file is empty or corrupted",
        )

    # 2. Extract financial details using Vision Service
    extracted_data, image_sha256 = vision_service.process_receipt(contents)

    # 3. Verify against order and settle transaction atomically
    receipt = await VerificationService.verify_and_settle(
        session=session,
        order_id=order_id,
        extracted=extracted_data,
        image_sha256=image_sha256,
    )

    return ReceiptVerificationResponse(
        id=receipt.id,
        order_id=receipt.order_id,
        bank_platform=receipt.bank_platform,
        reference_number=receipt.reference_number,
        extracted_amount=receipt.extracted_amount,
        receipt_timestamp=receipt.receipt_timestamp,
        verification_status=receipt.verification_status,
        image_sha256=receipt.image_sha256,
        failure_reason=receipt.failure_reason,
        created_at=receipt.created_at,
    )


@router.get("/{receipt_id}", response_model=ReceiptVerificationResponse)
async def get_receipt(
    receipt_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
):
    """Retrieve details and audit information for a specific payment receipt."""
    stmt = select(PaymentReceipt).where(PaymentReceipt.id == receipt_id)
    res = await session.execute(stmt)
    receipt = res.scalar_one_or_none()

    if not receipt:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Receipt not found")

    return ReceiptVerificationResponse(
        id=receipt.id,
        order_id=receipt.order_id,
        bank_platform=receipt.bank_platform,
        reference_number=receipt.reference_number,
        extracted_amount=receipt.extracted_amount,
        receipt_timestamp=receipt.receipt_timestamp,
        verification_status=receipt.verification_status,
        image_sha256=receipt.image_sha256,
        failure_reason=receipt.failure_reason,
        created_at=receipt.created_at,
    )
