from typing import Any


class VeriFactBaseException(Exception):
    """Base exception for VeriFact domain errors."""

    def __init__(self, message: str, code: str, status_code: int = 400, details: Any = None):
        super().__init__(message)
        self.message = message
        self.code = code
        self.status_code = status_code
        self.details = details or {}


class DuplicateReceiptError(VeriFactBaseException):
    def __init__(self, message: str = "Duplicate receipt detected", details: Any = None):
        super().__init__(
            message=message,
            code="DUPLICATE_RECEIPT",
            status_code=409,
            details=details,
        )


class AmountMismatchError(VeriFactBaseException):
    def __init__(self, expected: int, received: int, details: Any = None):
        super().__init__(
            message=f"Amount mismatch: expected COP {expected}, extracted COP {received}",
            code="AMOUNT_MISMATCH",
            status_code=422,
            details={"expected": expected, "received": received, **(details or {})},
        )


class ExpiredReceiptError(VeriFactBaseException):
    def __init__(self, message: str = "Receipt timestamp outside valid order window", details: Any = None):
        super().__init__(
            message=message,
            code="RECEIPT_TIMESTAMP_EXPIRED",
            status_code=422,
            details=details,
        )


class ExtractionFailedError(VeriFactBaseException):
    def __init__(self, message: str = "Failed to extract receipt data", details: Any = None):
        super().__init__(
            message=message,
            code="EXTRACTION_FAILED",
            status_code=422,
            details=details,
        )


class OrderSettledError(VeriFactBaseException):
    def __init__(self, order_id: str, current_status: str):
        super().__init__(
            message=f"Order {order_id} is already settled with status '{current_status}'",
            code="ORDER_ALREADY_SETTLED",
            status_code=409,
            details={"order_id": order_id, "status": current_status},
        )


class InsufficientStockError(VeriFactBaseException):
    def __init__(self, sku: str, requested: int, available: int):
        super().__init__(
            message=f"Insufficient stock for SKU '{sku}': requested {requested}, available {available}",
            code="INSUFFICIENT_STOCK",
            status_code=400,
            details={"sku": sku, "requested": requested, "available": available},
        )
