from sqlalchemy import Column, Integer, String, Text, DECIMAL, Boolean, TIMESTAMP, JSON
from sqlalchemy.sql import func

from ..database import Base


class Product(Base):
    """
    Modelo para productos Louder.
    Representa el catálogo de productos propios que se monitorean.
    """
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    sku = Column(String(50), unique=True, nullable=False, index=True)
    ml_id = Column(String(50), unique=True, nullable=True, index=True)  # ID en Mercado Libre
    name = Column(String(255), nullable=False)
    description = Column(Text)
    category = Column(String(100), index=True)
    
    # Pricing
    current_price = Column(DECIMAL(10, 2))
    cost = Column(DECIMAL(10, 2))
    min_margin_percent = Column(DECIMAL(5, 2), default=20.0)
    target_percentile = Column(Integer, default=50)  # Percentil objetivo (1-100)
    
    # Attributes y metadata (JSON para compatibilidad SQLite/PostgreSQL)
    attributes = Column(JSON)  # {size, power, impedance, color, etc.}
    search_keywords = Column(Text)  # Stored as comma-separated string for SQLite
    
    # Vector embedding - stored as TEXT in SQLite, will convert to list in Python
    embedding = Column(Text)  # JSON string of vector for SQLite compatibility
    
    # Status
    is_active = Column(Boolean, default=True)
    
    # Timestamps
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())

    def __repr__(self):
        return f"<Product(id={self.id}, sku='{self.sku}', name='{self.name}', price={self.current_price})>"

    @property
    def min_price(self):
        """Calcula el precio mínimo basado en costo y margen mínimo"""
        if self.cost and self.min_margin_percent:
            return float(self.cost) * (1 + float(self.min_margin_percent) / 100)
        return None

    @property
    def current_margin_percent(self):
        """Calcula el margen actual en porcentaje"""
        if self.cost and self.current_price and float(self.cost) > 0:
            return ((float(self.current_price) - float(self.cost)) / float(self.cost)) * 100
        return None
