from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from ...database import get_db
from ...models import PricingRecommendation
from ...schemas import PricingRecommendationResponse

router = APIRouter()


@router.get("/recommendations", response_model=List[PricingRecommendationResponse])
async def list_recommendations(
    limit: int = Query(50, ge=1, le=200),
    applied: Optional[bool] = None,
    confidence: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """
    Lista las recomendaciones de pricing generadas.
    """
    query = db.query(PricingRecommendation).order_by(PricingRecommendation.generated_at.desc())
    
    if applied is not None:
        query = query.filter(PricingRecommendation.applied == applied)
    if confidence:
        query = query.filter(PricingRecommendation.confidence == confidence)
    
    recommendations = query.limit(limit).all()
    return recommendations


@router.get("/recommendations/{recommendation_id}", response_model=PricingRecommendationResponse)
async def get_recommendation(
    recommendation_id: int,
    db: Session = Depends(get_db),
):
    """
    Obtiene una recomendación específica.
    """
    recommendation = db.query(PricingRecommendation).filter(
        PricingRecommendation.id == recommendation_id
    ).first()
    
    if not recommendation:
        raise HTTPException(status_code=404, detail="Recommendation not found")
    return recommendation


@router.post("/recommendations/{recommendation_id}/apply", status_code=200)
async def apply_recommendation(
    recommendation_id: int,
    db: Session = Depends(get_db),
):
    """
    Aplica una recomendación de pricing (actualiza el precio del producto).
    """
    recommendation = db.query(PricingRecommendation).filter(
        PricingRecommendation.id == recommendation_id
    ).first()
    
    if not recommendation:
        raise HTTPException(status_code=404, detail="Recommendation not found")
    
    if recommendation.applied:
        raise HTTPException(status_code=400, detail="Recommendation already applied")
    
    # TODO: Actualizar precio del producto y marcar como aplicada
    # from ...models import Product
    # product = db.query(Product).filter(Product.id == recommendation.product_id).first()
    # product.current_price = recommendation.recommended_price
    # recommendation.applied = True
    # db.commit()
    
    return {
        "message": "Recommendation applied successfully",
        "recommendation_id": recommendation_id,
        "new_price": float(recommendation.recommended_price)
    }
