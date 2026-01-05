"""
Data models for Mercado Libre scraping and analysis.
Extracted from agente_precios_ml_gagr.ipynb
"""
from dataclasses import dataclass
from typing import Optional, List, Dict, Any


@dataclass
class IdentifiedProduct:
    """Producto identificado a partir de descripción."""
    brand: Optional[str]
    model: Optional[str]
    model_norm: Optional[str]  # Normalized model (alphanumeric only)
    signature: str  # Unique identifier for the product


@dataclass
class Offer:
    """Oferta individual de un producto en Mercado Libre."""
    title: str
    price: float
    condition: str  # new, used, unknown
    url: str
    item_id: str
    source: str  # preloaded_state, jsonld
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "title": self.title,
            "price": self.price,
            "condition": self.condition,
            "url": self.url,
            "item_id": self.item_id,
            "source": self.source
        }


@dataclass
class PriceStatistics:
    """Estadísticas de precios para un grupo de ofertas."""
    n: int
    min: float
    max: float
    mean: float
    median: float
    q1: Optional[float] = None
    q3: Optional[float] = None
    iqr: Optional[float] = None
    outliers_removed: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "n": self.n,
            "min": self.min,
            "max": self.max,
            "mean": self.mean,
            "median": self.median,
            "q1": self.q1,
            "q3": self.q3,
            "iqr": self.iqr,
            "outliers_removed": self.outliers_removed
        }


@dataclass
class ScrapingResult:
    """Resultado completo del scraping de Mercado Libre."""
    identified_product: IdentifiedProduct
    strategy: str  # preloaded_state, jsonld, no_offers
    listing_url: str
    offers: List[Offer]
    timestamp: str
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "identified_product": {
                "brand": self.identified_product.brand,
                "model": self.identified_product.model,
                "model_norm": self.identified_product.model_norm,
                "signature": self.identified_product.signature
            },
            "strategy": self.strategy,
            "listing_url": self.listing_url,
            "offers_count": len(self.offers),
            "offers": [o.to_dict() for o in self.offers],
            "timestamp": self.timestamp
        }
