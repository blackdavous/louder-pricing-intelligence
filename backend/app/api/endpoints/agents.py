"""
API endpoints para ejecutar agentes de LangGraph.
"""
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import Optional
from pydantic import BaseModel, Field

from app.database import get_db
from app.models.product import Product
from app.models.pricing_recommendation import PricingRecommendation
from app.agents import OrchestratorAgent
from app.core.logging import get_logger
from app.core.monitoring import ml_searches_total, pricing_recommendations_total

logger = get_logger(__name__)
router = APIRouter(prefix="/agents", tags=["agents"])


class PricingWorkflowRequest(BaseModel):
    """Request body para ejecutar pricing workflow."""
    product_id: int = Field(..., description="ID del producto Louder")
    force_refresh: bool = Field(default=False, description="Forzar nuevo scan de competidores")
    target_margin_percent: Optional[float] = Field(default=None, description="Margen objetivo (override)")


class PricingWorkflowResponse(BaseModel):
    """Response del pricing workflow."""
    success: bool
    product_id: int
    product_name: str
    competitor_count: int
    recommendation: Optional[dict]
    errors: list[str]
    duration_seconds: float


@router.post("/pricing-workflow", response_model=PricingWorkflowResponse)
async def run_pricing_workflow(
    request: PricingWorkflowRequest,
    db: Session = Depends(get_db)
):
    """
    Ejecuta el workflow completo de pricing intelligence:
    1. Market Research: Buscar competidores en ML
    2. Data Extraction: Extraer y normalizar datos
    3. Pricing Intelligence: Generar recomendación de precio
    
    Returns:
        PricingWorkflowResponse con recomendación de pricing
    """
    import time
    start_time = time.time()
    
    logger.info(
        "Starting pricing workflow",
        product_id=request.product_id,
        force_refresh=request.force_refresh
    )
    
    # Get product from database
    product = db.query(Product).filter(Product.id == request.product_id).first()
    
    if not product:
        logger.error("Product not found", product_id=request.product_id)
        raise HTTPException(status_code=404, detail=f"Product {request.product_id} not found")
    
    if not product.cost or product.cost <= 0:
        logger.error("Product has invalid cost", product_id=request.product_id, cost=product.cost)
        raise HTTPException(
            status_code=400,
            detail=f"Product {request.product_id} has invalid cost: {product.cost}"
        )
    
    # Initialize orchestrator agent
    orchestrator = OrchestratorAgent()
    
    try:
        # Run the complete workflow
        result = await orchestrator.run(
            product_id=str(product.id),
            product_name=product.name,
            product_attributes=product.attributes or {},
            cost_price=float(product.cost),
            current_price=float(product.current_price) if product.current_price else None,
            target_margin_percent=request.target_margin_percent or float(product.min_margin_percent or 30.0)
        )
        
        duration = time.time() - start_time
        
        # Record metrics
        ml_searches_total.labels(
            status="success" if result.get("market_research_complete") else "error"
        ).inc()
        
        if result.get("final_recommendation"):
            rec = result["final_recommendation"]
            pricing_recommendations_total.labels(
                confidence=rec.get("confidence", "unknown")
            ).inc()
            
            # Save recommendation to database
            db_recommendation = PricingRecommendation(
                product_id=product.id,
                recommended_price=rec["recommended_price"],
                current_price=float(product.current_price) if product.current_price else 0.0,
                current_percentile=None,  # TODO: Calculate from current price
                target_percentile=int(rec["target_percentile"]),
                competitors_analyzed=rec.get("competitor_sample_size", 0),
                price_stats=rec,  # Store full recommendation as JSON
                reasoning=rec.get("reasoning", ""),
                confidence=rec.get("confidence", "unknown"),
                applied=False
            )
            db.add(db_recommendation)
            db.commit()
            
            logger.info(
                "Pricing workflow completed successfully",
                product_id=product.id,
                recommended_price=rec["recommended_price"],
                confidence=rec["confidence"],
                duration_seconds=duration
            )
        
        return PricingWorkflowResponse(
            success=result.get("pricing_complete", False),
            product_id=product.id,
            product_name=product.name,
            competitor_count=result.get("competitor_count", 0),
            recommendation=result.get("final_recommendation"),
            errors=result.get("errors", []),
            duration_seconds=round(duration, 2)
        )
        
    except Exception as e:
        duration = time.time() - start_time
        logger.error(
            "Pricing workflow failed",
            product_id=product.id,
            error=str(e),
            duration_seconds=duration
        )
        
        ml_searches_total.labels(status="error").inc()
        
        raise HTTPException(
            status_code=500,
            detail=f"Pricing workflow failed: {str(e)}"
        )


@router.get("/status")
async def agent_status():
    """
    Get status of agent system.
    """
    return {
        "status": "operational",
        "agents": {
            "market_research": "ready",
            "data_extractor": "ready",
            "pricing_intelligence": "ready",
            "orchestrator": "ready"
        },
        "openai_configured": True,  # TODO: Check actual config
        "ml_api_configured": True   # TODO: Check actual config
    }
