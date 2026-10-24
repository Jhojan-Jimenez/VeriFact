import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel

from src.domain.models import BankPlatform, ReceiptVerificationStatus


class ExtractedReceiptData(BaseModel):
    bank_platform: BankPlatform
    reference_number: str
    amount_cop: int
    receipt_timestamp: datetime
    concept: str | None = None
    raw_text: str = ""


class ReceiptVerificationResponse(BaseModel):
    id: uuid.UUID
    order_id: uuid.UUID | None
    bank_platform: BankPlatform
    reference_number: str
    extracted_amount: int
    receipt_timestamp: datetime
    verification_status: ReceiptVerificationStatus
    image_sha256: str
    failure_reason: str | None = None
    created_at: datetime


class ReceiptInspectionResponse(BaseModel):
    bank_platform: BankPlatform
    reference_number: str
    amount_cop: int
    receipt_timestamp: datetime
    concept: str | None = None
    image_sha256: str
    raw_text_snippet: str
    is_duplicate: bool
    duplicate_info: dict[str, Any] | None = None
