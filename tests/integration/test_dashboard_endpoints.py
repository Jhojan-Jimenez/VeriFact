from datetime import UTC

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_dashboard_static_and_order_endpoints(client: AsyncClient):
    # 1. Test Static UI endpoint
    res_root = await client.get("/")
    assert res_root.status_code == 200
    assert "VeriFact" in res_root.text

    # 2. Test Quick Order Creation
    res_quick = await client.post(
        "/api/v1/orders/quick",
        json={"order_number": "ORD-QUICK-101", "total_amount": 75000},
    )
    assert res_quick.status_code == 201
    quick_data = res_quick.json()
    assert quick_data["order_number"] == "ORD-QUICK-101"
    assert quick_data["total_amount"] == 75000
    assert quick_data["status"] == "PENDING"

    # 3. Test Listing Orders with PENDING status
    res_orders = await client.get("/api/v1/orders?status_filter=PENDING")
    assert res_orders.status_code == 200
    orders_list = res_orders.json()
    assert len(orders_list) >= 1
    assert any(o["order_number"] == "ORD-QUICK-101" for o in orders_list)

    # 4. Test Receipts list endpoint
    res_receipts = await client.get("/api/v1/receipts")
    assert res_receipts.status_code == 200
    assert isinstance(res_receipts.json(), list)

    # 5. Test Inspect endpoint without order
    from datetime import datetime
    from unittest.mock import patch

    from src.api.schemas.receipt import ExtractedReceiptData
    from src.domain.models import BankPlatform

    mock_extracted = ExtractedReceiptData(
        bank_platform=BankPlatform.NEQUI,
        reference_number="M99881122",
        amount_cop=45000,
        receipt_timestamp=datetime.now(UTC),
        raw_text="Nequi ¡Listo! $45.000",
    )

    with patch("src.api.v1.receipts.vision_service.process_receipt") as mock_v:
        mock_v.return_value = (mock_extracted, "inspect_hash_123")
        res_inspect = await client.post(
            "/api/v1/receipts/inspect",
            files={"file": ("receipt.png", b"dummy-receipt-bytes-content-for-inspection" * 3, "image/png")},
        )
        assert res_inspect.status_code == 200
        inspect_data = res_inspect.json()
        assert inspect_data["bank_platform"] == "NEQUI"
        assert inspect_data["amount_cop"] == 45000
        assert inspect_data["is_duplicate"] is False
