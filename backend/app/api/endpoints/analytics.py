from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timedelta
from typing import Optional

from ...database import get_db
from ...models import Product, PriceSnapshot, PricingRecommendation

router = APIRouter()


@router.get("/overview")
async def market_overview(
    db: Session = Depends(get_db),
):
    """
    Vista general del mercado y estado del sistema.
    """
    total_products = db.query(Product).filter(Product.is_active == True).count()
    
    # Recomendaciones pendientes
    pending_recommendations = db.query(PricingRecommendation).filter(
        PricingRecommendation.applied == False
    ).count()
    
    # Snapshots recientes (últimas 24h)
    yesterday = datetime.now() - timedelta(days=1)
    recent_snapshots = db.query(PriceSnapshot).filter(
        PriceSnapshot.snapshot_at >= yesterday
    ).count()
    
    return {
        "total_active_products": total_products,
        "pending_recommendations": pending_recommendations,
        "recent_price_snapshots_24h": recent_snapshots,
        "last_updated": datetime.now(),
    }


@router.get("/product/{product_id}")
async def product_analytics(
    product_id: int,
    days: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db),
):
    """
    Dashboard de análisis para un producto específico.
    """
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    # Snapshots recientes
    cutoff_date = datetime.now() - timedelta(days=days)
    snapshots = db.query(PriceSnapshot).filter(
        PriceSnapshot.louder_product_id == product_id,
        PriceSnapshot.snapshot_at >= cutoff_date
    ).all()
    
    # Última recomendación
    latest_recommendation = db.query(PricingRecommendation).filter(
        PricingRecommendation.product_id == product_id
    ).order_by(PricingRecommendation.generated_at.desc()).first()
    
    return {
        "product": {
            "id": product.id,
            "sku": product.sku,
            "name": product.name,
            "current_price": float(product.current_price) if product.current_price else None,
            "category": product.category,
        },
        "competitors_tracked": len(set(s.competitor_product_id for s in snapshots)),
        "total_price_snapshots": len(snapshots),
        "latest_recommendation": latest_recommendation,
        "date_range": {
            "from": cutoff_date,
            "to": datetime.now()
        }
    }


@router.get("/price-trends/{product_id}")
async def price_trends(
    product_id: int,
    days: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db),
):
    """
    Tendencias de precios de la competencia para un producto.
    """
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    cutoff_date = datetime.now() - timedelta(days=days)
    
    # Obtener snapshots agrupados por fecha
    snapshots = db.query(PriceSnapshot).filter(
        PriceSnapshot.louder_product_id == product_id,
        PriceSnapshot.snapshot_at >= cutoff_date
    ).order_by(PriceSnapshot.snapshot_at).all()
    
    # Calcular estadísticas por día
    from collections import defaultdict
    daily_prices = defaultdict(list)
    
    for snapshot in snapshots:
        day = snapshot.snapshot_at.date()
        daily_prices[day].append(float(snapshot.price))
    
    trends = []
    for day, prices in sorted(daily_prices.items()):
        trends.append({
            "date": day.isoformat(),
            "min": min(prices),
            "max": max(prices),
            "avg": sum(prices) / len(prices),
            "count": len(prices)
        })
    
    return {
        "product_id": product_id,
        "trends": trends
    }
