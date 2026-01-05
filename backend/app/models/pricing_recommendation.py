from sqlalchemy import Column, Integer, ForeignKey, DECIMAL, Text, Boolean, TIMESTAMP, String, JSON
from sqlalchemy.sql import func

from ..database import Base


class PricingRecommendation(Base):
    """
    Modelo para recomendaciones de pricing generadas por el sistema.
    """
    __tablename__ = "pricing_recommendations"

    id = Column(Integer, primary_key=True, index=True)
    
    # Relación con producto
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False, index=True)
    
    # Pricing
    recommended_price = Column(DECIMAL(10, 2), nullable=False)
    current_price = Column(DECIMAL(10, 2), nullable=False)
    
    # Análisis de posición
    current_percentile = Column(DECIMAL(5, 2))  # Percentil actual (0-100)
    target_percentile = Column(Integer)  # Percentil objetivo
    
    # Estadísticas de competencia
    competitors_analyzed = Column(Integer)
    price_stats = Column(JSON)  # {min, max, mean, median, std, p10, p25, p50, p75, p90}
    
    # Justificación
    reasoning = Column(Text)  # Explicación generada por LLM
    confidence = Column(String(20))  # 'high', 'medium', 'low'
    
    # Status
    applied = Column(Boolean, default=False)
    
    # Timestamp
    generated_at = Column(TIMESTAMP, server_default=func.now(), index=True)

    def __repr__(self):
        return f"<PricingRecommendation(product_id={self.product_id}, current={self.current_price}, recommended={self.recommended_price}, confidence='{self.confidence}')>"

    @property
    def price_change_percent(self):
        """Calcula el cambio porcentual recomendado"""
        if self.current_price and float(self.current_price) > 0:
            return ((float(self.recommended_price) - float(self.current_price)) / float(self.current_price)) * 100
        return None

    @property
    def price_change_absolute(self):
        """Calcula el cambio absoluto recomendado"""
        if self.current_price and self.recommended_price:
            return float(self.recommended_price) - float(self.current_price)
        return None
