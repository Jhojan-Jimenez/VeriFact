from datetime import UTC, datetime
from unittest.mock import patch

import pytest
from httpx import AsyncClient

from src.api.schemas.receipt import ExtractedReceiptData
from src.domain.models import BankPlatform


@pytest.mark.asyncio
async def test_full_receipt_verification_lifecycle(client: AsyncClient):
    # 1. Health check
    res_health = await client.get("/health")
    assert res_health.status_code == 200
    assert res_health.json()["status"] == "healthy"

    # 2. Register inventory product
    res_inv = await client.post(
        "/api/v1/inventory",
        json={
            "sku": "CHOMPA-AZUL",
            "name": "Chompa térmica azul",
            "unit_price": 95000,
            "stock": 10,
        },
    )
    assert res_inv.status_code == 201
    assert res_inv.json()["stock"] == 10

    # 3. Create sales order for 2 units ($190.000 COP)
    res_order = await client.post(
        "/api/v1/orders",
        json={
            "order_number": "ORD-2026-999",
            "items": [
                {"sku": "CHOMPA-AZUL", "quantity": 2, "unit_price": 95000},
            ],
        },
    )
    assert res_order.status_code == 201
    order_data = res_order.json()
    order_id = order_data["id"]
    assert order_data["total_amount"] == 190000
    assert order_data["status"] == "PENDING"

    # 4. Prepare Mock Receipt payload (Nequi payment for $190.000)
    mock_extracted = ExtractedReceiptData(
        bank_platform=BankPlatform.NEQUI,
        reference_number="M84729103",
        amount_cop=190000,
        receipt_timestamp=datetime.now(UTC),
        concept="ORD-2026-999",
        raw_text="Nequi ¡Listo! Enviaste $190.000 M84729103",
    )

    dummy_image_bytes = b"fake-receipt-image-content-for-testing-12345" * 4

    with patch("src.api.v1.receipts.vision_service.process_receipt") as mock_vision:
        mock_vision.return_value = (mock_extracted, "mock_sha256_hash_1122334455")

        # 5. Submit receipt verification
        res_verify = await client.post(
            "/api/v1/receipts/verify",
            data={"order_id": order_id},
            files={"file": ("receipt.png", dummy_image_bytes, "image/png")},
        )
        assert res_verify.status_code == 200
        verify_data = res_verify.json()
        assert verify_data["verification_status"] == "VERIFIED"
        assert verify_data["reference_number"] == "M84729103"
        assert verify_data["extracted_amount"] == 190000

    # 6. Verify order status transitioned to PAID
    res_order_check = await client.get(f"/api/v1/orders/{order_id}")
    assert res_order_check.status_code == 200
    assert res_order_check.json()["status"] == "PAID"

    # 7. Verify inventory stock was decremented from 10 to 8
    res_inv_check = await client.get("/api/v1/inventory")
    items = res_inv_check.json()
    chompa = next(i for i in items if i["sku"] == "CHOMPA-AZUL")
    assert chompa["stock"] == 8

    # 8. Verify audit history recorded the movement
    res_history = await client.get("/api/v1/inventory/CHOMPA-AZUL/history")
    assert res_history.status_code == 200
    history = res_history.json()
    assert len(history) == 1
    assert history[0]["quantity_change"] == -2

    # 9. Anti-Fraud Test A: Resubmitting identical image must trigger 409 Conflict
    with patch("src.api.v1.receipts.vision_service.process_receipt") as mock_vision:
        mock_vision.return_value = (mock_extracted, "mock_sha256_hash_1122334455")

        res_duplicate = await client.post(
            "/api/v1/receipts/verify",
            data={"order_id": order_id},
            files={"file": ("receipt.png", dummy_image_bytes, "image/png")},
        )
        assert res_duplicate.status_code == 409
        err = res_duplicate.json()["error"]
        assert err["code"] == "DUPLICATE_RECEIPT"


@pytest.mark.asyncio
async def test_amount_mismatch_rejection(client: AsyncClient):
    # Create inventory & order for $50.000
    await client.post(
        "/api/v1/inventory",
        json={"sku": "LIBRO-PY", "name": "Libro Python", "unit_price": 50000, "stock": 5},
    )
    res_order = await client.post(
        "/api/v1/orders",
        json={"order_number": "ORD-MISMATCH-1", "items": [{"sku": "LIBRO-PY", "quantity": 1, "unit_price": 50000}]},
    )
    order_id = res_order.json()["id"]

    # Client uploads receipt for only $30.000
    mock_extracted = ExtractedReceiptData(
        bank_platform=BankPlatform.DAVIPLATA,
        reference_number="DAV-771122",
        amount_cop=30000,  # Expected 50000!
        receipt_timestamp=datetime.now(UTC),
        raw_text="Daviplata Transacción exitosa $30.000",
    )

    dummy_image_bytes = b"fake-receipt-image-content-for-testing-12345" * 4

    with patch("src.api.v1.receipts.vision_service.process_receipt") as mock_vision:
        mock_vision.return_value = (mock_extracted, "sha256_mismatch_hash_9988")

        res_verify = await client.post(
            "/api/v1/receipts/verify",
            data={"order_id": order_id},
            files={"file": ("receipt.png", dummy_image_bytes, "image/png")},
        )
        assert res_verify.status_code == 422
        err = res_verify.json()["error"]
        assert err["code"] == "AMOUNT_MISMATCH"
        assert err["details"]["expected"] == 50000
        assert err["details"]["received"] == 30000
