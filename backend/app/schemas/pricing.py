from typing import Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime
from decimal import Decimal


class PricingStats(BaseModel):
    """Estadísticas de precios"""
    min: Decimal
    max: Decimal
    mean: Decimal
    median: Decimal
    std_dev: Decimal
    p10: Decimal
    p25: Decimal
    p50: Decimal
    p75: Decimal
    p90: Decimal


class PricingRecommendationResponse(BaseModel):
    """Schema para respuesta de recomendación de pricing"""
    id: int
    product_id: int
    recommended_price: Decimal
    current_price: Decimal
    current_percentile: Optional[Decimal]
    target_percentile: Optional[int]
    competitors_analyzed: Optional[int]
    price_stats: Optional[Dict[str, Any]]
    reasoning: Optional[str]
    confidence: Optional[str]
    applied: bool
    generated_at: datetime
    price_change_percent: Optional[float] = None
    price_change_absolute: Optional[float] = None

    class Config:
        from_attributes = True
