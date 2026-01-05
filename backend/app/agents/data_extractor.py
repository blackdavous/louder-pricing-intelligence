"""
Data Extractor Agent - LangGraph implementation.

This agent extracts structured data from competitor listings:
1. Parses product titles and descriptions
2. Extracts technical specifications
3. Normalizes pricing information
"""
from typing import TypedDict, List, Dict, Any, Optional
from langgraph.graph import StateGraph, END
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field

from app.core.config import settings
from app.core.logging import get_logger
from app.core.monitoring import track_agent_execution
from app.mcp_servers.mercadolibre import batch_get_prices_tool, get_product_details_tool

logger = get_logger(__name__)


class ProductSpecification(BaseModel):
    """Structured product specifications."""
    brand: Optional[str] = Field(None, description="Brand name")
    model: Optional[str] = Field(None, description="Model number")
    power_watts: Optional[float] = Field(None, description="Power in watts")
    size_inches: Optional[float] = Field(None, description="Size in inches")
    impedance_ohms: Optional[float] = Field(None, description="Impedance in ohms")
    frequency_range: Optional[str] = Field(None, description="Frequency range")
    features: List[str] = Field(default_factory=list, description="Additional features")


class ExtractedProduct(BaseModel):
    """Extracted and normalized product data."""
    ml_id: str
    original_title: str
    normalized_title: str
    price: float
    currency: str
    specifications: ProductSpecification
    condition: str
    shipping_free: bool
    seller_reputation: Optional[float] = None


class DataExtractorState(TypedDict):
    """State for data extractor agent."""
    raw_products: List[Dict[str, Any]]
    extracted_products: List[ExtractedProduct]
    extraction_errors: List[str]


class DataExtractorAgent:
    """
    LangGraph agent for extracting structured data from ML listings.
    
    Workflow:
    1. parse_listings: Extract basic product info
    2. extract_specs: Use LLM to parse technical specs
    3. normalize_data: Standardize formats and units
    """
    
    def __init__(self):
        self.llm = ChatOpenAI(
            model=settings.OPENAI_MODEL_MINI,
            temperature=0.1,
            api_key=settings.OPENAI_API_KEY
        )
        self.graph = self._build_graph()
    
    def _build_graph(self) -> StateGraph:
        """Build LangGraph workflow."""
        workflow = StateGraph(DataExtractorState)
        
        workflow.add_node("parse_listings", self.parse_listings)
        workflow.add_node("extract_specs", self.extract_specs)
        workflow.add_node("normalize_data", self.normalize_data)
        
        workflow.set_entry_point("parse_listings")
        workflow.add_edge("parse_listings", "extract_specs")
        workflow.add_edge("extract_specs", "normalize_data")
        workflow.add_edge("normalize_data", END)
        
        return workflow.compile()
    
    @track_agent_execution("data_extractor_parse_listings")
    async def parse_listings(self, state: DataExtractorState) -> DataExtractorState:
        """Parse basic information from raw ML listings."""
        logger.info("Parsing listings", count=len(state["raw_products"]))
        
        # Extract product IDs for batch fetching
        product_ids = [p.get("id") for p in state["raw_products"] if p.get("id")]
        
        if not product_ids:
            logger.warning("No product IDs found in raw products")
            state["extracted_products"] = []
            return state
        
        # Use MCP batch_get_prices_tool for efficient data fetching
        try:
            batch_result = await batch_get_prices_tool(product_ids)
            
            if batch_result.get("success"):
                extracted = []
                
                for product in batch_result.get("products", []):
                    try:
                        extracted_product = ExtractedProduct(
                            ml_id=product.get("id", ""),
                            original_title=product.get("title", ""),
                            normalized_title=product.get("title", "").lower(),
                            price=float(product.get("price", 0)),
                            currency=product.get("currency_id", "MXN"),
                            specifications=ProductSpecification(),
                            condition=product.get("condition", "unknown"),
                            shipping_free=False  # Not included in batch response
                        )
                        extracted.append(extracted_product)
                        
                    except Exception as e:
                        logger.error("Error parsing product", error=str(e))
                        state["extraction_errors"].append(f"Parse error: {str(e)}")
                
                state["extracted_products"] = extracted
                logger.info(f"Extracted {len(extracted)} products from batch")
            else:
                logger.error("Batch fetch failed", error=batch_result.get("error"))
                state["extraction_errors"].append(f"Batch fetch error: {batch_result.get('error')}")
                state["extracted_products"] = []
                
        except Exception as e:
            logger.error("Batch fetch exception", error=str(e))
            state["extraction_errors"].append(f"Batch exception: {str(e)}")
            state["extracted_products"] = []
        
        return state
    
    @track_agent_execution("data_extractor_extract_specs")
    async def extract_specs(self, state: DataExtractorState) -> DataExtractorState:
        """
        Use LLM to extract technical specifications from titles.
        Batch process for efficiency.
        """
        logger.info("Extracting specifications", count=len(state["extracted_products"]))
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an expert at extracting technical specifications 
            from audio equipment product titles. Extract: brand, model, power (watts), 
            size (inches), impedance (ohms), frequency range, and features.
            
            Return JSON with these fields. If a field is not found, use null."""),
            ("human", "Product title: {title}\n\nExtract specifications as JSON:")
        ])
        
        for product in state["extracted_products"]:
            try:
                chain = prompt | self.llm
                result = await chain.ainvoke({"title": product.original_title})
                
                # TODO: Parse LLM response to ProductSpecification
                # For now, keep empty specs
                
            except Exception as e:
                logger.error("Error extracting specs", error=str(e), product=product.ml_id)
                state["extraction_errors"].append(f"Spec extraction error: {str(e)}")
        
        return state
    
    @track_agent_execution("data_extractor_normalize_data")
    async def normalize_data(self, state: DataExtractorState) -> DataExtractorState:
        """Normalize units, formats, and standardize data."""
        logger.info("Normalizing data", count=len(state["extracted_products"]))
        
        for product in state["extracted_products"]:
            # Normalize title (remove emojis, extra spaces, etc.)
            product.normalized_title = " ".join(product.original_title.split())
            
            # Convert prices to MXN if needed
            if product.currency != "MXN":
                # TODO: Currency conversion
                pass
        
        return state
    
    async def run(self, raw_products: List[Dict[str, Any]]) -> DataExtractorState:
        """
        Execute the data extraction workflow.
        
        Args:
            raw_products: Raw product data from ML API
        
        Returns:
            Final state with extracted and normalized products
        """
        initial_state: DataExtractorState = {
            "raw_products": raw_products,
            "extracted_products": [],
            "extraction_errors": []
        }
        
        logger.info("Starting data extraction", product_count=len(raw_products))
        
        final_state = await self.graph.ainvoke(initial_state)
        
        logger.info(
            "Data extraction complete",
            extracted=len(final_state["extracted_products"]),
            errors=len(final_state["extraction_errors"])
        )
        
        return final_state
