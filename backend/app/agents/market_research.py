"""
Market Research Agent - LangGraph implementation.

This agent performs competitive research on Mercado Libre:
1. Searches for similar products using keywords
2. Analyzes product titles and descriptions
3. Identifies direct competitors
"""
from typing import TypedDict, Annotated, List, Dict, Any
from langgraph.graph import StateGraph, END
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from pydantic import BaseModel, Field

from app.core.config import settings
from app.core.logging import get_logger
from app.core.monitoring import track_agent_execution
from app.mcp_servers.mercadolibre import search_products_tool

logger = get_logger(__name__)


class SearchQuery(BaseModel):
    """Structured search query for ML API."""
    keywords: List[str] = Field(description="List of search keywords")
    category: str = Field(description="Product category")
    min_price: float = Field(description="Minimum price filter")
    max_price: float = Field(description="Maximum price filter")


class CompetitorProduct(BaseModel):
    """Competitor product information."""
    ml_id: str = Field(description="Mercado Libre product ID")
    title: str = Field(description="Product title")
    price: float = Field(description="Current price")
    seller_id: str = Field(description="Seller ID")
    relevance_score: float = Field(description="Similarity score 0-1")
    
    
class MarketResearchState(TypedDict):
    """State for market research agent."""
    product_name: str
    product_attributes: Dict[str, Any]
    search_queries: List[SearchQuery]
    raw_results: List[Dict[str, Any]]
    competitor_products: List[CompetitorProduct]
    total_found: int
    errors: List[str]


class MarketResearchAgent:
    """
    LangGraph agent for market research on Mercado Libre.
    
    Workflow:
    1. generate_queries: Create search queries from product info
    2. execute_searches: Call ML API with queries
    3. analyze_results: Filter and score competitors
    """
    
    def __init__(self):
        self.llm = ChatOpenAI(
            model=settings.OPENAI_MODEL_MINI,
            temperature=0.3,
            api_key=settings.OPENAI_API_KEY
        )
        self.graph = self._build_graph()
        
        # Check if ML API is enabled
        logger.info(
            "Initializing MarketResearchAgent",
            ml_api_enabled=settings.ML_API_ENABLED
        )
    
    def _build_graph(self) -> StateGraph:
        """Build LangGraph workflow."""
        workflow = StateGraph(MarketResearchState)
        
        # Add nodes
        workflow.add_node("generate_queries", self.generate_queries)
        workflow.add_node("execute_searches", self.execute_searches)
        workflow.add_node("analyze_results", self.analyze_results)
        
        # Define edges
        workflow.set_entry_point("generate_queries")
        workflow.add_edge("generate_queries", "execute_searches")
        workflow.add_edge("execute_searches", "analyze_results")
        workflow.add_edge("analyze_results", END)
        
        return workflow.compile()
    
    @track_agent_execution("market_research_generate_queries")
    async def generate_queries(self, state: MarketResearchState) -> MarketResearchState:
        """
        Generate intelligent search queries from product information.
        Uses LLM to create multiple search variations.
        """
        logger.info(
            "Generating search queries",
            product_name=state["product_name"]
        )
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an expert at creating Mercado Libre search queries.
            Given a product name and attributes, generate 3-5 search query variations
            that will find similar competitor products.
            
            Include variations with:
            - Exact brand/model names
            - Generic product category
            - Technical specifications
            - Common synonyms
            
            Return a JSON array of search queries."""),
            ("human", """Product: {product_name}
            Attributes: {attributes}
            
            Generate search queries as JSON array with format:
            [{{"keywords": ["word1", "word2"], "category": "category", "min_price": 0, "max_price": 10000}}]""")
        ])
        
        parser = PydanticOutputParser(pydantic_object=SearchQuery)
        
        try:
            chain = prompt | self.llm
            result = await chain.ainvoke({
                "product_name": state["product_name"],
                "attributes": str(state["product_attributes"])
            })
            
            # Parse LLM output to SearchQuery objects
            # For now, create basic queries
            queries = [
                SearchQuery(
                    keywords=[state["product_name"]],
                    category="audio",
                    min_price=0,
                    max_price=50000
                )
            ]
            
            state["search_queries"] = queries
            logger.info(f"Generated {len(queries)} search queries")
            
        except Exception as e:
            logger.error("Error generating queries", error=str(e))
            state["errors"].append(f"Query generation failed: {str(e)}")
        
        return state
    
    @track_agent_execution("market_research_execute_searches")
    async def execute_searches(self, state: MarketResearchState) -> MarketResearchState:
        """
        Execute searches on Mercado Libre API.
        Uses MCP server for ML API integration.
        
        Falls back to sample data if ML_API_ENABLED is False.
        """
        logger.info(
            "Executing ML searches",
            query_count=len(state.get("search_queries", [])),
            ml_api_enabled=settings.ML_API_ENABLED
        )
        
        # Check if API is enabled
        if not settings.ML_API_ENABLED:
            logger.warning(
                "ML API disabled - Using sample data for testing",
                product=state.get("product_name")
            )
            # Return sample/mock data for testing without real API
            state["raw_results"] = []
            state["total_found"] = 0
            state["errors"].append(
                "ML API not configured - Enable ML_API_ENABLED in .env when ready"
            )
            return state
        
        all_results = []
        
        for query in state.get("search_queries", []):
            try:
                # Use MCP search_products_tool
                result = await search_products_tool(
                    query=" ".join(query.keywords),
                    category=query.category if query.category != "audio" else None,
                    min_price=query.min_price if query.min_price > 0 else None,
                    max_price=query.max_price if query.max_price < 50000 else None,
                    limit=50
                )
                
                if result.get("success"):
                    all_results.extend(result.get("results", []))
                    logger.info(
                        "Search completed",
                        query=" ".join(query.keywords),
                        results=len(result.get("results", []))
                    )
                else:
                    error_msg = result.get("error", "Unknown error")
                    logger.error("Search failed", error=error_msg)
                    state["errors"].append(f"Search error: {error_msg}")
                    
            except Exception as e:
                logger.error("Search exception", error=str(e))
                state["errors"].append(f"Search exception: {str(e)}")
        
        state["raw_results"] = all_results
        state["total_found"] = len(all_results)
        
        logger.info(f"Total products found: {len(all_results)}")
        
        return state
    
    @track_agent_execution("market_research_analyze_results")
    async def analyze_results(self, state: MarketResearchState) -> MarketResearchState:
        """
        Analyze search results and score competitors.
        Uses simple title matching for relevance scoring.
        """
        logger.info(
            "Analyzing results",
            result_count=len(state.get("raw_results", []))
        )
        
        competitors = []
        product_name_lower = state["product_name"].lower()
        
        for result in state.get("raw_results", []):
            try:
                title = result.get("title", "").lower()
                
                # Simple relevance scoring based on keyword matching
                relevance = 0.5  # Base score
                
                # Boost if product name keywords appear in title
                for word in product_name_lower.split():
                    if len(word) > 3 and word in title:
                        relevance += 0.1
                
                relevance = min(relevance, 1.0)
                
                competitor = CompetitorProduct(
                    ml_id=result.get("id", ""),
                    title=result.get("title", ""),
                    price=float(result.get("price", 0)),
                    seller_id=str(result.get("seller_id", "")),
                    relevance_score=round(relevance, 2)
                )
                
                competitors.append(competitor)
                
            except Exception as e:
                logger.error("Error analyzing result", error=str(e))
                state["errors"].append(f"Analysis error: {str(e)}")
        
        # Sort by relevance
        competitors.sort(key=lambda x: x.relevance_score, reverse=True)
        
        state["competitor_products"] = competitors
        
        logger.info(f"Analyzed {len(competitors)} competitor products")
        
        return state
    
    async def run(
        self,
        product_name: str,
        product_attributes: Dict[str, Any]
    ) -> MarketResearchState:
        """
        Execute the market research workflow.
        
        Args:
            product_name: Name of product to research
            product_attributes: Dict of product attributes
            
        Returns:
            Final state with competitor products
        """
        initial_state: MarketResearchState = {
            "product_name": product_name,
            "product_attributes": product_attributes,
            "search_queries": [],
            "raw_results": [],
            "competitor_products": [],
            "total_found": 0,
            "errors": []
        }
        
        logger.info("Starting market research workflow", product=product_name)
        
        final_state = await self.graph.ainvoke(initial_state)
        
        logger.info(
            "Market research completed",
            competitors_found=len(final_state.get("competitor_products", [])),
            errors=len(final_state.get("errors", []))
        )
        
        return final_state
    
    async def run(
        self,
        product_name: str,
        product_attributes: Dict[str, Any]
    ) -> MarketResearchState:
        """
        Execute the market research workflow.
        
        Args:
            product_name: Name of the product to research
            product_attributes: Product specifications and features
        
        Returns:
            Final state with competitor products
        """
        initial_state: MarketResearchState = {
            "product_name": product_name,
            "product_attributes": product_attributes,
            "search_queries": [],
            "raw_results": [],
            "competitor_products": [],
            "total_found": 0,
            "errors": []
        }
        
        logger.info(
            "Starting market research",
            product=product_name
        )
        
        final_state = await self.graph.ainvoke(initial_state)
        
        logger.info(
            "Market research complete",
            competitors_found=len(final_state.get("competitor_products", [])),
            errors=len(final_state.get("errors", []))
        )
        
        return final_state
