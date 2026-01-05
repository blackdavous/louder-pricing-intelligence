from sqlalchemy import Column, Integer, String, Text, Boolean, TIMESTAMP, JSON
from sqlalchemy.sql import func

from ..database import Base


class CompetitorProduct(Base):
    """
    Modelo para productos de la competencia encontrados en Mercado Libre.
    """
    __tablename__ = "competitor_products"

    id = Column(Integer, primary_key=True, index=True)
    ml_id = Column(String(50), unique=True, nullable=False, index=True)
    seller_id = Column(String(50), index=True)
    seller_name = Column(String(255))
    title = Column(String(500))
    category_id = Column(String(50), index=True)
    
    # Attributes del producto (JSON for SQLite/PostgreSQL compatibility)
    attributes = Column(JSON)
    
    # Vector embedding - stored as TEXT in SQLite
    embedding = Column(Text)
    
    # Tracking
    first_seen_at = Column(TIMESTAMP, server_default=func.now())
    last_seen_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())
    is_active = Column(Boolean, default=True)

    def __repr__(self):
        return f"<CompetitorProduct(id={self.id}, ml_id='{self.ml_id}', title='{self.title[:30]}...')>"
