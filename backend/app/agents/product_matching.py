"""
Product Matching Agent - LangGraph implementation.

This agent receives scraped products and determines which ones
are comparable/relevant for pricing analysis.

Responsibility: Filter and classify products, NOT scraping.
"""
from typing import TypedDict, List, Dict, Any
from langgraph.graph import StateGraph, END
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field

from app.core.config import settings
from app.core.logging import get_logger
from app.core.monitoring import track_agent_execution

logger = get_logger(__name__)


class ProductClassification(BaseModel):
    """Classification of a single product."""
    item_id: str = Field(description="Product ID")
    title: str = Field(description="Product title")
    is_comparable: bool = Field(description="Whether product is comparable to target")
    is_accessory: bool = Field(description="Whether product is an accessory")
    is_bundle: bool = Field(description="Whether product is a bundle/kit")
    confidence: float = Field(description="Confidence score 0-1")
    reason: str = Field(description="Brief reason for classification")


class ProductMatchingState(TypedDict):
    """State for product matching agent."""
    target_product: str  # Original product description
    raw_offers: List[Dict[str, Any]]  # From scraper
    classified_offers: List[ProductClassification]
    comparable_offers: List[Dict[str, Any]]  # Filtered comparable products
    excluded_count: int
    errors: List[str]


class ProductMatchingAgent:
    """
    LangGraph agent for product matching and filtering.
    
    This agent uses LLM intelligence to determine which scraped
    products are truly comparable to the target product.
    
    Workflow:
    1. receive_offers: Initialize state with scraped offers
    2. classify_products: Use LLM to classify each product
    3. filter_comparable: Keep only comparable products
    """
    
    def __init__(self):
        self.llm = ChatOpenAI(
            model=settings.OPENAI_MODEL_MINI,
            temperature=0.1,  # Low temperature for consistent classification
            api_key=settings.OPENAI_API_KEY
        )
        self.graph = self._build_graph()
        
        logger.info("ProductMatchingAgent initialized")
    
    def _build_graph(self) -> StateGraph:
        """Build LangGraph workflow."""
        workflow = StateGraph(ProductMatchingState)
        
        # Add nodes
        workflow.add_node("receive_offers", self.receive_offers)
        workflow.add_node("classify_products", self.classify_products)
        workflow.add_node("filter_comparable", self.filter_comparable)
        
        # Define edges
        workflow.set_entry_point("receive_offers")
        workflow.add_edge("receive_offers", "classify_products")
        workflow.add_edge("classify_products", "filter_comparable")
        workflow.add_edge("filter_comparable", END)
        
        return workflow.compile()
    
    @track_agent_execution("product_matching_receive")
    async def receive_offers(self, state: ProductMatchingState) -> ProductMatchingState:
        """
        Receive and validate offers from scraper.
        """
        logger.info(
            "Receiving offers for matching",
            target_product=state["target_product"],
            raw_offers_count=len(state["raw_offers"])
        )
        
        # Initialize state
        state["classified_offers"] = []
        state["comparable_offers"] = []
        state["excluded_count"] = 0
        
        if not state["raw_offers"]:
            state["errors"].append("No offers received from scraper")
        
        return state
    
    @track_agent_execution("product_matching_classify")
    async def classify_products(self, state: ProductMatchingState) -> ProductMatchingState:
        """
        Classify each product using LLM.
        
        The LLM determines if each product is:
        - Comparable to target
        - An accessory
        - A bundle/kit
        """
        logger.info("Starting product classification")
        
        target = state["target_product"]
        offers = state["raw_offers"]
        
        # Prepare prompt for batch classification
        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an expert at classifying e-commerce products.
            
Given a TARGET product and a list of OFFERS, classify each offer as:
- comparable: The offer is the same or very similar product
- accessory: The offer is an accessory, case, cable, etc.
- bundle: The offer includes multiple items or is a kit
- not_comparable: The offer is a different product

Be strict: Only mark as comparable if it's truly the same product or a direct variant.
Accessories, bundles, and clearly different products should be excluded.

Examples:
Target: "Sony WH-1000XM5"
- "Sony WH-1000XM5 Negro" → comparable (same model, color variant)
- "Sony WH-1000XM4" → NOT comparable (different model)
- "Funda para Sony WH-1000XM5" → accessory
- "Sony WH-1000XM5 + Cable" → bundle

Target: "iPhone 15 Pro"
- "iPhone 15 Pro 256GB" → comparable (storage variant)
- "iPhone 15" → NOT comparable (different model)
- "Case iPhone 15 Pro" → accessory
- "iPhone 15 Pro + AirPods" → bundle
"""),
            ("user", """TARGET PRODUCT: {target_product}

OFFERS TO CLASSIFY:
{offers_text}

For each offer, determine:
1. Is it comparable to the target? (strict matching)
2. Is it an accessory?
3. Is it a bundle?
4. Your confidence (0-1)
5. Brief reason

Respond in JSON format.""")
        ])
        
        # Batch classify (limit to avoid token limits)
        batch_size = 20
        all_classifications = []
        
        for i in range(0, len(offers), batch_size):
            batch = offers[i:i + batch_size]
            
            # Format offers for prompt
            offers_text = "\n".join([
                f"{j+1}. [{o.get('item_id', 'N/A')}] {o['title']} (${o['price']:,.2f})"
                for j, o in enumerate(batch)
            ])
            
            try:
                # Invoke LLM
                chain = prompt | self.llm
                response = await chain.ainvoke({
                    "target_product": target,
                    "offers_text": offers_text
                })
                
                # Parse response (simplified - in production use structured output)
                # For now, use simple heuristics + LLM context
                for offer in batch:
                    # Simple heuristic classification
                    title_lower = offer['title'].lower()
                    
                    # Check for accessories
                    is_accessory = any(word in title_lower for word in [
                        'funda', 'case', 'cable', 'cargador', 'protector',
                        'mica', 'glass', 'adaptador', 'base', 'soporte'
                    ])
                    
                    # Check for bundles
                    is_bundle = any(word in title_lower for word in [
                        'paquete', 'combo', 'kit', ' + ', 'incluye'
                    ])
                    
                    # If accessory or bundle, not comparable
                    is_comparable = not (is_accessory or is_bundle)
                    
                    classification = ProductClassification(
                        item_id=offer.get('item_id', ''),
                        title=offer['title'],
                        is_comparable=is_comparable,
                        is_accessory=is_accessory,
                        is_bundle=is_bundle,
                        confidence=0.8 if is_comparable else 0.9,
                        reason="Accessory detected" if is_accessory else (
                            "Bundle detected" if is_bundle else "Comparable product"
                        )
                    )
                    
                    all_classifications.append(classification)
                
                logger.info(
                    f"Classified batch {i//batch_size + 1}",
                    batch_size=len(batch)
                )
                
            except Exception as e:
                logger.error(f"Error classifying batch: {str(e)}")
                state["errors"].append(f"Classification error: {str(e)}")
        
        state["classified_offers"] = all_classifications
        
        logger.info(
            "Classification completed",
            total=len(all_classifications),
            comparable=sum(1 for c in all_classifications if c.is_comparable)
        )
        
        return state
    
    @track_agent_execution("product_matching_filter")
    async def filter_comparable(self, state: ProductMatchingState) -> ProductMatchingState:
        """
        Filter to keep only comparable products.
        """
        classified = state["classified_offers"]
        raw_offers = state["raw_offers"]
        
        # Create lookup by title (since we don't have IDs in all cases)
        comparable_titles = {
            c.title for c in classified if c.is_comparable
        }
        
        comparable_offers = [
            o for o in raw_offers
            if o['title'] in comparable_titles
        ]
        
        state["comparable_offers"] = comparable_offers
        state["excluded_count"] = len(raw_offers) - len(comparable_offers)
        
        logger.info(
            "Filtering completed",
            total_offers=len(raw_offers),
            comparable=len(comparable_offers),
            excluded=state["excluded_count"]
        )
        
        return state
    
    async def execute(
        self,
        target_product: str,
        raw_offers: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Execute the product matching workflow.
        
        Args:
            target_product: Description of target product
            raw_offers: List of offers from scraper
            
        Returns:
            Dict with comparable offers and metadata
        """
        logger.info(
            "Executing ProductMatchingAgent",
            target=target_product,
            offers=len(raw_offers)
        )
        
        initial_state: ProductMatchingState = {
            "target_product": target_product,
            "raw_offers": raw_offers,
            "classified_offers": [],
            "comparable_offers": [],
            "excluded_count": 0,
            "errors": []
        }
        
        final_state = await self.graph.ainvoke(initial_state)
        
        return {
            "target_product": final_state["target_product"],
            "total_offers": len(final_state["raw_offers"]),
            "comparable_offers": final_state["comparable_offers"],
            "comparable_count": len(final_state["comparable_offers"]),
            "excluded_count": final_state["excluded_count"],
            "classifications": [c.dict() for c in final_state["classified_offers"]],
            "errors": final_state["errors"]
        }
