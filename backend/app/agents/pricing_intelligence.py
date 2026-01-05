"""
Pricing Intelligence Agent - LangGraph implementation.

This agent generates optimal pricing recommendations:
1. Analyzes competitor price distributions
2. Calculates target percentiles
3. Considers profit margins and market position
"""
from typing import TypedDict, List, Dict, Any, Optional
from langgraph.graph import StateGraph, END
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field
import numpy as np
from datetime import datetime

from app.core.config import settings
from app.core.logging import get_logger
from app.core.monitoring import track_agent_execution
from app.mcp_servers.analytics import generate_recommendation_tool, calculate_stats_tool

logger = get_logger(__name__)


class PriceStatistics(BaseModel):
    """Statistical analysis of competitor prices."""
    min_price: float
    max_price: float
    mean_price: float
    median_price: float
    p25: float  # 25th percentile
    p75: float  # 75th percentile
    std_dev: float
    sample_size: int


class PricingRecommendation(BaseModel):
    """Pricing recommendation with reasoning."""
    recommended_price: float
    confidence: str = Field(description="low, medium, high")
    target_percentile: float
    expected_margin_percent: float
    reasoning: str
    alternative_prices: List[float] = Field(default_factory=list)
    market_position: str = Field(description="premium, competitive, budget")


class PricingIntelligenceState(TypedDict):
    """State for pricing intelligence agent."""
    product_id: str
    product_name: str
    cost_price: float
    current_price: Optional[float]
    competitor_prices: List[float]
    price_statistics: Optional[PriceStatistics]
    recommendation: Optional[PricingRecommendation]
    target_margin_percent: float
    target_percentile: float


class PricingIntelligenceAgent:
    """
    LangGraph agent for intelligent pricing recommendations.
    
    Workflow:
    1. calculate_statistics: Analyze price distribution
    2. determine_position: Assess market positioning
    3. generate_recommendation: Create pricing strategy
    """
    
    def __init__(self):
        self.llm = ChatOpenAI(
            model=settings.OPENAI_MODEL_MINI,
            temperature=0.2,
            api_key=settings.OPENAI_API_KEY
        )
        self.graph = self._build_graph()
    
    def _build_graph(self) -> StateGraph:
        """Build LangGraph workflow."""
        workflow = StateGraph(PricingIntelligenceState)
        
        workflow.add_node("calculate_statistics", self.calculate_statistics)
        workflow.add_node("determine_position", self.determine_position)
        workflow.add_node("generate_recommendation", self.generate_recommendation)
        
        workflow.set_entry_point("calculate_statistics")
        workflow.add_edge("calculate_statistics", "determine_position")
        workflow.add_edge("determine_position", "generate_recommendation")
        workflow.add_edge("generate_recommendation", END)
        
        return workflow.compile()
    
    @track_agent_execution("pricing_intelligence_calculate_statistics")
    async def calculate_statistics(
        self, 
        state: PricingIntelligenceState
    ) -> PricingIntelligenceState:
        """Calculate statistical measures from competitor prices using MCP Analytics."""
        logger.info(
            "Calculating price statistics",
            product=state["product_name"],
            sample_size=len(state["competitor_prices"])
        )
        
        if len(state["competitor_prices"]) == 0:
            logger.warning("No competitor prices available")
            state["price_statistics"] = None
            return state
        
        try:
            # Use MCP calculate_stats_tool
            stats_result = await calculate_stats_tool(state["competitor_prices"])
            
            if stats_result.get("success"):
                stats = PriceStatistics(
                    min_price=stats_result["min"],
                    max_price=stats_result["max"],
                    mean_price=stats_result["mean"],
                    median_price=stats_result["median"],
                    p25=stats_result["q1"],
                    p75=stats_result["q3"],
                    std_dev=stats_result["std_dev"],
                    sample_size=stats_result["sample_size"]
                )
                
                state["price_statistics"] = stats
                
                logger.info(
                    "Statistics calculated via MCP",
                    median=stats.median_price,
                    mean=stats.mean_price,
                    range=(stats.min_price, stats.max_price)
                )
            else:
                logger.error("Stats calculation failed", error=stats_result.get("error"))
                state["price_statistics"] = None
                
        except Exception as e:
            logger.error("Stats calculation exception", error=str(e))
            state["price_statistics"] = None
        
        return state
    
    @track_agent_execution("pricing_intelligence_determine_position")
    async def determine_position(
        self, 
        state: PricingIntelligenceState
    ) -> PricingIntelligenceState:
        """Determine optimal market position based on cost and competition."""
        logger.info("Determining market position")
        
        stats = state.get("price_statistics")
        if not stats:
            return state
        
        cost = state["cost_price"]
        target_margin = state["target_margin_percent"]
        
        # Calculate minimum viable price with target margin
        min_viable_price = cost * (1 + target_margin / 100)
        
        # Determine if we can be competitive with desired margin
        if min_viable_price <= stats.p25:
            position = "budget"
            target_percentile = 25.0
        elif min_viable_price <= stats.median_price:
            position = "competitive"
            target_percentile = 50.0
        else:
            position = "premium"
            target_percentile = 75.0
        
        # Store in state
        state["target_percentile"] = target_percentile
        
        logger.info(
            "Market position determined",
            position=position,
            target_percentile=target_percentile,
            min_viable_price=min_viable_price
        )
        
        return state
    
    @track_agent_execution("pricing_intelligence_generate_recommendation")
    async def generate_recommendation(
        self, 
        state: PricingIntelligenceState
    ) -> PricingIntelligenceState:
        """Generate final pricing recommendation using MCP Analytics."""
        logger.info("Generating pricing recommendation")
        
        if not state.get("price_statistics"):
            logger.warning("No statistics available for recommendation")
            state["recommendation"] = None
            return state
        
        try:
            # Use MCP generate_recommendation_tool
            rec_result = await generate_recommendation_tool(
                cost_price=state["cost_price"],
                competitor_prices=state["competitor_prices"],
                target_margin_percent=state.get("target_margin_percent", 30.0),
                target_percentile=state.get("target_percentile"),
                current_price=state.get("current_price")
            )
            
            if rec_result.get("success"):
                recommendation = PricingRecommendation(
                    recommended_price=rec_result["recommended_price"],
                    confidence=rec_result["confidence"],
                    target_percentile=rec_result["target_percentile"],
                    expected_margin_percent=rec_result["margin_percent"],
                    reasoning=rec_result["reasoning"],
                    alternative_prices=rec_result.get("alternatives", []),
                    market_position=rec_result["market_position"]
                )
                
                state["recommendation"] = recommendation
                
                logger.info(
                    "Recommendation generated via MCP",
                    price=recommendation.recommended_price,
                    margin=recommendation.expected_margin_percent,
                    position=recommendation.market_position
                )
            else:
                logger.error("Recommendation generation failed", error=rec_result.get("error"))
                state["recommendation"] = None
                
        except Exception as e:
            logger.error("Recommendation generation exception", error=str(e))
            state["recommendation"] = None
        
        return state
    
    async def run(
        self,
        product_id: str,
        product_name: str,
        cost_price: float,
        competitor_prices: List[float],
        current_price: Optional[float] = None,
        target_margin_percent: float = 30.0
    ) -> PricingIntelligenceState:
        """
        Execute the pricing intelligence workflow.
        
        Args:
            product_id: Product identifier
            product_name: Product name
            cost_price: Product cost
            competitor_prices: List of competitor prices
            current_price: Current selling price (optional)
            target_margin_percent: Target profit margin
            
        Returns:
            Final state with pricing recommendation
        """
        initial_state: PricingIntelligenceState = {
            "product_id": product_id,
            "product_name": product_name,
            "cost_price": cost_price,
            "current_price": current_price,
            "competitor_prices": competitor_prices,
            "price_statistics": None,
            "recommendation": None,
            "target_margin_percent": target_margin_percent,
            "target_percentile": 50.0  # Will be auto-determined
        }
        
        logger.info(
            "Starting pricing intelligence workflow",
            product=product_name,
            competitors=len(competitor_prices)
        )
        
        final_state = await self.graph.ainvoke(initial_state)
        
        logger.info(
            "Pricing intelligence completed",
            recommended_price=final_state.get("recommendation").recommended_price if final_state.get("recommendation") else None
        )
        
        return final_state
    
    async def execute(
        self,
        target_product: str,
        statistics: Dict[str, Any],
        comparable_count: int
    ) -> Dict[str, Any]:
        """
        Execute pricing recommendation from market statistics.
        
        Wrapper method for new pipeline architecture.
        
        Args:
            target_product: Product description
            statistics: Market statistics from stats module
            comparable_count: Number of comparable products
            
        Returns:
            Dict with recommendation and metadata
        """
        logger.info(
            "Executing PricingIntelligenceAgent (new architecture)",
            product=target_product,
            comparable_count=comparable_count
        )
        
        # Extract prices from statistics
        overall = statistics.get("overall", {})
        clean_stats = overall.get("stats_clean", overall.get("stats_all", {}))
        
        median = clean_stats.get("median", 0)
        mean = clean_stats.get("mean", 0)
        q1 = clean_stats.get("q1", median * 0.85 if median else 0)
        q3 = clean_stats.get("q3", median * 1.15 if median else 0)
        min_price = clean_stats.get("min", 0)
        max_price = clean_stats.get("max", 0)
        
        # Determine strategy based on market spread
        spread = q3 - q1 if (q1 and q3) else 0
        spread_ratio = spread / median if median > 0 else 0
        
        if spread_ratio < 0.2:
            strategy = "competitive"
            recommended_price = median
            confidence = 0.85
            reasoning = f"Mercado competitivo con poca variación de precios (IQR: ${spread:,.2f}). Precio recomendado cercano a la mediana de ${median:,.2f} MXN."
        elif spread_ratio > 0.5:
            strategy = "value"
            recommended_price = q1 * 1.05  # 5% arriba del Q1
            confidence = 0.70
            reasoning = f"Mercado con amplia variación de precios (IQR: ${spread:,.2f}). Estrategia de valor posicionándose cerca del Q1 (${q1:,.2f} MXN)."
        else:
            strategy = "competitive"
            recommended_price = median
            confidence = 0.80
            reasoning = f"Mercado moderadamente competitivo. Precio recomendado en la mediana de ${median:,.2f} MXN con {comparable_count} productos comparables."
        
        # Calculate market position
        if q1 and q3 and q3 > q1:
            position_pct = ((recommended_price - q1) / (q3 - q1) * 100)
            market_position = f"Positioned at {position_pct:.0f}% within the interquartile range"
        else:
            market_position = "Standard market position"
        
        # Alternative scenarios
        alternatives = {
            "aggressive": round(q1 * 0.95, 2) if q1 else recommended_price * 0.90,
            "conservative": round(median, 2) if median else recommended_price,
            "premium": round(q3 * 0.95, 2) if q3 else recommended_price * 1.15
        }
        
        # Risk factors
        risk_factors = []
        outliers_removed = overall.get("outliers_removed", 0)
        
        if outliers_removed > 3:
            risk_factors.append("⚠️ Mercado con precios atípicos detectados (outliers removidos)")
        else:
            risk_factors.append("✅ Datos de mercado estables")
        
        if comparable_count < 5:
            risk_factors.append("⚠️ Muestra pequeña de productos comparables")
        
        risk_factors.extend([
            "Considerar tendencias estacionales",
            "Monitorear cambios de precios de competidores"
        ])
        
        recommendation = {
            "recommended_price": round(recommended_price, 2),
            "confidence": confidence,
            "strategy": strategy,
            "reasoning": reasoning,
            "market_position": market_position,
            "risk_factors": risk_factors,
            "alternative_prices": alternatives
        }
        
        return {
            "target_product": target_product,
            "recommendation": recommendation,
            "errors": [],
            "success": True
        }
