from typing import Optional, Dict, Any
from pydantic import BaseModel
from datetime import datetime


class CompetitorProductResponse(BaseModel):
    """Schema para respuesta de producto competidor"""
    id: int
    ml_id: str
    seller_id: Optional[str]
    seller_name: Optional[str]
    title: Optional[str]
    category_id: Optional[str]
    attributes: Optional[Dict[str, Any]]
    first_seen_at: datetime
    last_seen_at: datetime
    is_active: bool

    class Config:
        from_attributes = True
