#!/usr/bin/env bash
set -euo pipefail

BASE_URL="${1:-http://localhost:8000}"

echo "🔍 Testing VeriFact API at ${BASE_URL}..."

# 1. Healthcheck
echo "👉 1. GET /health"
curl -s -f "${BASE_URL}/health" | grep -q "healthy" && echo "✅ Healthcheck OK" || { echo "❌ Healthcheck failed"; exit 1; }

# 2. Register inventory
echo "👉 2. POST /api/v1/inventory"
curl -s -f -X POST "${BASE_URL}/api/v1/inventory" \
  -H "Content-Type: application/json" \
  -d '{"sku": "SMOKE-01", "name": "Producto Smoke Test", "unit_price": 50000, "stock": 20}' > /dev/null
echo "✅ Inventory item created"

# 3. Create order
echo "👉 3. POST /api/v1/orders"
ORDER_RESP=$(curl -s -f -X POST "${BASE_URL}/api/v1/orders" \
  -H "Content-Type: application/json" \
  -d '{"order_number": "ORD-SMOKE-'"$(date +%s)"'", "items": [{"sku": "SMOKE-01", "quantity": 1, "unit_price": 50000}]}')
ORDER_ID=$(echo "${ORDER_RESP}" | grep -o '"id":"[^"]*' | cut -d'"' -f4)
echo "✅ Order created with ID: ${ORDER_ID}"

echo "🎉 All baseline smoke tests passed successfully!"
