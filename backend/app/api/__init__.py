from fastapi import APIRouter
from .endpoints import products, scans, pricing, analytics, agents

api_router = APIRouter()

# Include all routers
api_router.include_router(products.router, prefix="/products", tags=["products"])
api_router.include_router(scans.router, prefix="/scans", tags=["scans"])
api_router.include_router(pricing.router, prefix="/pricing", tags=["pricing"])
api_router.include_router(analytics.router, prefix="/analytics", tags=["analytics"])
api_router.include_router(agents.router, prefix="/agents", tags=["agents"])
