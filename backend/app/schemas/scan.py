from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field
from datetime import datetime


class ScanTrigger(BaseModel):
    """Schema para trigger de scan manual"""
    scan_type: str = Field(..., description="Tipo de scan: full, priority, flash, on-demand")
    product_ids: Optional[List[int]] = Field(None, description="IDs específicos de productos (opcional)")


class ScanLogResponse(BaseModel):
    """Schema para respuesta de log de scan"""
    id: int
    scan_type: str
    products_scanned: Optional[int]
    competitors_found: Optional[int]
    errors: Optional[Dict[str, Any]]
    duration_seconds: Optional[int]
    status: Optional[str]
    started_at: Optional[datetime]
    completed_at: Optional[datetime]

    class Config:
        from_attributes = True
