from typing import Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime
from decimal import Decimal


class PriceSnapshotCreate(BaseModel):
    """Schema para crear un snapshot de precio"""
    louder_product_id: int
    competitor_product_id: int
    price: Decimal = Field(..., ge=0)
    stock_available: Optional[int] = None
    shipping_free: Optional[bool] = None
    seller_reputation: Optional[Dict[str, Any]] = None
    similarity_score: Optional[Decimal] = Field(None, ge=0, le=1)
    competition_level: Optional[str] = None


class PriceSnapshotResponse(PriceSnapshotCreate):
    """Schema para respuesta de snapshot"""
    id: int
    snapshot_at: datetime

    class Config:
        from_attributes = True
