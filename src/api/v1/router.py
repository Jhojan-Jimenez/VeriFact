from fastapi import APIRouter

from src.api.v1.inventory import router as inventory_router
from src.api.v1.orders import router as orders_router
from src.api.v1.receipts import router as receipts_router

api_v1_router = APIRouter(prefix="/api/v1")
api_v1_router.include_router(orders_router)
api_v1_router.include_router(receipts_router)
api_v1_router.include_router(inventory_router)
