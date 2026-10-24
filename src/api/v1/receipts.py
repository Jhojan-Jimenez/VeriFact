import uuid

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from src.api.schemas.receipt import ReceiptVerificationResponse
from src.core.database import get_session
from src.domain.models import PaymentReceipt
from src.services.verification_service import VerificationService
from src.services.vision_service import VisionService

router = APIRouter(prefix="/receipts", tags=["Receipt Verification"])
vision_service = VisionService()


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
