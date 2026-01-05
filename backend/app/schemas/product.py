from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime
from decimal import Decimal


class ProductBase(BaseModel):
    """Base schema para Product"""
    sku: str = Field(..., description="SKU único del producto")
    ml_id: Optional[str] = Field(None, description="ID en Mercado Libre")
    name: str = Field(..., description="Nombre del producto")
    description: Optional[str] = None
    category: Optional[str] = None
    current_price: Optional[Decimal] = Field(None, ge=0)
    cost: Optional[Decimal] = Field(None, ge=0)
    min_margin_percent: Optional[Decimal] = Field(20.0, ge=0, le=100)
    target_percentile: Optional[int] = Field(50, ge=1, le=100)
    attributes: Optional[Dict[str, Any]] = Field(default_factory=dict)
    search_keywords: Optional[List[str]] = Field(default_factory=list)


class ProductCreate(ProductBase):
    """Schema para crear un producto"""
    pass


class ProductUpdate(BaseModel):
    """Schema para actualizar un producto"""
    ml_id: Optional[str] = None
    name: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    current_price: Optional[Decimal] = None
    cost: Optional[Decimal] = None
    min_margin_percent: Optional[Decimal] = None
    target_percentile: Optional[int] = None
    attributes: Optional[Dict[str, Any]] = None
    search_keywords: Optional[List[str]] = None
    is_active: Optional[bool] = None


class ProductResponse(ProductBase):
    """Schema para respuesta de producto"""
    id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime
    min_price: Optional[float] = None
    current_margin_percent: Optional[float] = None

    class Config:
        from_attributes = True


class ProductList(BaseModel):
    """Schema para lista paginada de productos"""
    total: int
    page: int
    page_size: int
    products: List[ProductResponse]
