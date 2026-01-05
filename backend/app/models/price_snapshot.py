from sqlalchemy import Column, Integer, ForeignKey, DECIMAL, Boolean, TIMESTAMP, String, JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from ..database import Base


class PriceSnapshot(Base):
    """
    Modelo para snapshots de precios de la competencia.
    Almacena el precio de un producto competidor en un momento específico.
    """
    __tablename__ = "price_snapshots"

    id = Column(Integer, primary_key=True, index=True)
    
    # Relaciones
    louder_product_id = Column(Integer, ForeignKey("products.id"), nullable=False, index=True)
    competitor_product_id = Column(Integer, ForeignKey("competitor_products.id"), nullable=False, index=True)
    
    # Precio y stock
    price = Column(DECIMAL(10, 2), nullable=False)
    stock_available = Column(Integer)
    shipping_free = Column(Boolean)
    
    # Metadata del vendedor
    seller_reputation = Column(JSON)  # {level, transactions, positive_rating, etc.}
    
    # Similarity metrics
    similarity_score = Column(DECIMAL(5, 4))  # 0.0000 - 1.0000
    competition_level = Column(String(20))  # 'direct', 'indirect', 'substitute'
    
    # Timestamp
    snapshot_at = Column(TIMESTAMP, server_default=func.now(), index=True)

    def __repr__(self):
        return f"<PriceSnapshot(louder_product_id={self.louder_product_id}, price={self.price}, similarity={self.similarity_score})>"
