"""
Orchestrator Agent - LangGraph implementation.

This is the main agent that coordinates the entire pricing intelligence workflow:
1. MarketResearchAgent -> Find competitors
2. DataExtractorAgent -> Extract structured data
3. PricingIntelligenceAgent -> Generate pricing recommendation
"""
from typing import TypedDict, Optional, Dict, Any
from langgraph.graph import StateGraph, END
from datetime import datetime

from .market_research import MarketResearchAgent
from .data_extractor import DataExtractorAgent
from .pricing_intelligence import PricingIntelligenceAgent

from app.core.logging import get_logger
from app.core.monitoring import track_agent_execution

logger = get_logger(__name__)


class OrchestratorState(TypedDict):
    """Global state for orchestrator agent."""
    # Input
    product_id: str
    product_name: str
    product_attributes: Dict[str, Any]
    cost_price: float
    current_price: Optional[float]
    target_margin_percent: float
    
    # Intermediate results
    market_research_complete: bool
    data_extraction_complete: bool
    pricing_complete: bool
    
    # Results from sub-agents
    competitor_count: int
    competitor_prices: list
    final_recommendation: Optional[Dict[str, Any]]
    
    # Metadata
    started_at: str
    completed_at: Optional[str]
    errors: list


class OrchestratorAgent:
    """
    Main orchestrator agent that coordinates the pricing intelligence workflow.
    
    This agent runs the three specialized agents in sequence:
    1. MarketResearchAgent: Search for competitors on Mercado Libre
    2. DataExtractorAgent: Extract and normalize product data
    3. PricingIntelligenceAgent: Generate optimal pricing recommendation
    """
    
    def __init__(self):
        self.market_research = MarketResearchAgent()
        self.data_extractor = DataExtractorAgent()
        self.pricing_intelligence = PricingIntelligenceAgent()
        self.graph = self._build_graph()
    
    def _build_graph(self) -> StateGraph:
        """Build orchestrator workflow graph."""
        workflow = StateGraph(OrchestratorState)
        
        # Add workflow nodes
        workflow.add_node("research_market", self.research_market)
        workflow.add_node("extract_data", self.extract_data)
        workflow.add_node("generate_pricing", self.generate_pricing)
        workflow.add_node("finalize", self.finalize)
        
        # Define workflow edges
        workflow.set_entry_point("research_market")
        workflow.add_edge("research_market", "extract_data")
        workflow.add_edge("extract_data", "generate_pricing")
        workflow.add_edge("generate_pricing", "finalize")
        workflow.add_edge("finalize", END)
        
        return workflow.compile()
    
    @track_agent_execution("orchestrator_research_market")
    async def research_market(self, state: OrchestratorState) -> OrchestratorState:
        """Execute market research phase."""
        logger.info(
            "Orchestrator: Starting market research",
            product=state["product_name"]
        )
        
        try:
            research_result = await self.market_research.run(
                product_name=state["product_name"],
                product_attributes=state["product_attributes"]
            )
            
            state["competitor_count"] = len(research_result.get("competitor_products", []))
            state["market_research_complete"] = True
            
            # Store raw competitor data for next stage
            # In production, this would be persisted to database
            state["_raw_competitors"] = research_result.get("raw_results", [])
            
            logger.info(
                "Market research complete",
                competitors_found=state["competitor_count"]
            )
            
        except Exception as e:
            logger.error("Market research failed", error=str(e))
            state["errors"].append(f"Market research error: {str(e)}")
            state["market_research_complete"] = False
        
        return state
    
    @track_agent_execution("orchestrator_extract_data")
    async def extract_data(self, state: OrchestratorState) -> OrchestratorState:
        """Execute data extraction phase."""
        logger.info("Orchestrator: Starting data extraction")
        
        if not state.get("market_research_complete"):
            logger.warning("Skipping data extraction - market research incomplete")
            return state
        
        try:
            raw_competitors = state.get("_raw_competitors", [])
            
            extraction_result = await self.data_extractor.run(
                raw_products=raw_competitors
            )
            
            # Extract prices for pricing intelligence
            extracted_products = extraction_result.get("extracted_products", [])
            prices = [p.price for p in extracted_products if p.price > 0]
            
            state["competitor_prices"] = prices
            state["data_extraction_complete"] = True
            
            logger.info(
                "Data extraction complete",
                products_extracted=len(extracted_products),
                prices_extracted=len(prices)
            )
            
        except Exception as e:
            logger.error("Data extraction failed", error=str(e))
            state["errors"].append(f"Data extraction error: {str(e)}")
            state["data_extraction_complete"] = False
        
        return state
    
    @track_agent_execution("orchestrator_generate_pricing")
    async def generate_pricing(self, state: OrchestratorState) -> OrchestratorState:
        """Execute pricing intelligence phase."""
        logger.info("Orchestrator: Starting pricing intelligence")
        
        if not state.get("data_extraction_complete"):
            logger.warning("Skipping pricing - data extraction incomplete")
            return state
        
        try:
            pricing_result = await self.pricing_intelligence.run(
                product_id=state["product_id"],
                product_name=state["product_name"],
                cost_price=state["cost_price"],
                competitor_prices=state["competitor_prices"],
                current_price=state.get("current_price"),
                target_margin_percent=state.get("target_margin_percent", 30.0)
            )
            
            recommendation = pricing_result.get("recommendation")
            if recommendation:
                state["final_recommendation"] = {
                    "recommended_price": recommendation.recommended_price,
                    "confidence": recommendation.confidence,
                    "target_percentile": recommendation.target_percentile,
                    "expected_margin_percent": recommendation.expected_margin_percent,
                    "reasoning": recommendation.reasoning,
                    "alternative_prices": recommendation.alternative_prices,
                    "market_position": recommendation.market_position,
                    "competitor_sample_size": len(state["competitor_prices"])
                }
            
            state["pricing_complete"] = True
            
            logger.info(
                "Pricing intelligence complete",
                recommended_price=recommendation.recommended_price if recommendation else None
            )
            
        except Exception as e:
            logger.error("Pricing intelligence failed", error=str(e))
            state["errors"].append(f"Pricing intelligence error: {str(e)}")
            state["pricing_complete"] = False
        
        return state
    
    @track_agent_execution("orchestrator_finalize")
    async def finalize(self, state: OrchestratorState) -> OrchestratorState:
        """Finalize workflow and cleanup."""
        logger.info("Orchestrator: Finalizing workflow")
        
        state["completed_at"] = datetime.utcnow().isoformat()
        
        # Cleanup temporary state
        if "_raw_competitors" in state:
            del state["_raw_competitors"]
        
        success = (
            state.get("market_research_complete", False) and
            state.get("data_extraction_complete", False) and
            state.get("pricing_complete", False)
        )
        
        logger.info(
            "Workflow complete",
            success=success,
            errors=len(state.get("errors", []))
        )
        
        return state
    
    async def run(
        self,
        product_id: str,
        product_name: str,
        product_attributes: Dict[str, Any],
        cost_price: float,
        current_price: Optional[float] = None,
        target_margin_percent: float = 30.0
    ) -> OrchestratorState:
        """
        Execute the complete pricing intelligence workflow.
        
        Args:
            product_id: Unique product identifier
            product_name: Name of the product
            product_attributes: Product specifications and features
            cost_price: Base cost of the product
            current_price: Current selling price (optional)
            target_margin_percent: Desired profit margin percentage
        
        Returns:
            Final orchestrator state with pricing recommendation
        """
        initial_state: OrchestratorState = {
            "product_id": product_id,
            "product_name": product_name,
            "product_attributes": product_attributes,
            "cost_price": cost_price,
            "current_price": current_price,
            "target_margin_percent": target_margin_percent,
            "market_research_complete": False,
            "data_extraction_complete": False,
            "pricing_complete": False,
            "competitor_count": 0,
            "competitor_prices": [],
            "final_recommendation": None,
            "started_at": datetime.utcnow().isoformat(),
            "completed_at": None,
            "errors": []
        }
        
        logger.info(
            "Starting orchestrator workflow",
            product=product_name,
            product_id=product_id
        )
        
        final_state = await self.graph.ainvoke(initial_state)
        
        logger.info(
            "Orchestrator workflow complete",
            product_id=product_id,
            success=final_state.get("pricing_complete", False),
            recommendation=final_state.get("final_recommendation") is not None
        )
        
        return final_state
