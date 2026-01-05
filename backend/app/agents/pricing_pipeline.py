"""
Complete Pricing Pipeline - Orchestrator

This module orchestrates the complete pricing workflow with two modes:

MODE 1 - Product URL (NEW):
1. Extract Product Details → Get complete specs from pivot product
2. Search Strategy Agent (LLM) → Generate optimal search terms
3. HTML Scraping (no LLM) → Extract similar products from ML
4. Product Matching Agent (LLM) → Filter comparable products  
5. Statistical Analysis (no LLM) → Calculate price statistics
6. Pricing Recommendation Agent (LLM) → Generate optimal price

MODE 2 - Product Description (LEGACY):
1. HTML Scraping (no LLM) → Extract products from ML
2. Product Matching Agent (LLM) → Filter comparable products  
3. Statistical Analysis (no LLM) → Calculate price statistics
4. Pricing Recommendation Agent (LLM) → Generate optimal price

This architecture separates data extraction from intelligence.
"""
import asyncio
from typing import Dict, Any, Optional
from datetime import datetime
import re

from app.core.logging import get_logger
from app.core.monitoring import track_agent_execution
from app.mcp_servers.mercadolibre.scraper import MLWebScraper, ProductDetails
from app.mcp_servers.mercadolibre.stats import get_price_recommendation_data
from app.agents.product_matching import ProductMatchingAgent
from app.agents.pricing_intelligence import PricingIntelligenceAgent
from app.agents.search_strategy import SearchStrategyAgent

logger = get_logger(__name__)


class PricingPipeline:
    """
    Complete pricing analysis pipeline with support for pivot product URLs.
    
    Workflow (with pivot product):
    ┌─────────────────────────────────────┐
    │ 0. Extract Product Details          │
    │    - Get specs from your product    │
    └──────────────┬──────────────────────┘
                   ↓
    ┌──────────────┴──────────────────────┐
    │ 1. Search Strategy (LLM Agent)      │
    │    - Analyze characteristics        │
    │    - Generate search terms          │
    └──────────────┬──────────────────────┘
                   ↓
    ┌──────────────┴──────────────────────┐
    │ 2. Scrape HTML (MLWebScraper)       │
    │    - Search with optimized terms    │
    │    - Extract competitor products    │
    └──────────────┬──────────────────────┘
                   ↓
    ┌──────────────┴──────────────────────┐
    │ 3. Match Products (LLM Agent)       │
    │    - Filter by key specifications   │
    │    - Remove accessories/bundles     │
    └──────────────┬──────────────────────┘
                   ↓
    ┌──────────────┴──────────────────────┐
    │ 4. Calculate Stats (Pure Math)      │
    │    - IQR outlier removal            │
    │    - Group by condition             │
    └──────────────┬──────────────────────┘
                   ↓
    ┌──────────────┴──────────────────────┐
    │ 5. Recommend Price (LLM Agent)      │
    │    - Analyze market position        │
    │    - Generate pricing strategy      │
    └─────────────────────────────────────┘
    """
    
    def __init__(self):
        self.scraper = MLWebScraper()
        self.search_strategy_agent = SearchStrategyAgent()
        self.matching_agent = ProductMatchingAgent()
        self.pricing_agent = PricingIntelligenceAgent()
        
        logger.info("PricingPipeline initialized")
    
    def _is_product_url(self, input_str: str) -> bool:
        """Check if input is a Mercado Libre product URL."""
        return bool(re.search(r"mercadolibre\.com\.", input_str))
    
    @track_agent_execution("pricing_pipeline_full")
    async def analyze_product(
        self,
        product_input: str,
        max_offers: int = 25
    ) -> Dict[str, Any]:
        """
        Complete pricing analysis for a product.
        
        Args:
            product_input: Either:
                - Product URL (https://www.mercadolibre.com.mx/.../p/MLM...)
                - Product description ("Sony WH-1000XM5")
            max_offers: Maximum offers to scrape
            
        Returns:
            Complete analysis with recommendation
        """
        # Determine if input is URL or description
        is_url = self._is_product_url(product_input)
        
        if is_url:
            return await self._analyze_from_url(product_input, max_offers)
        else:
            return await self._analyze_from_description(product_input, max_offers)
    
    async def _analyze_from_url(
        self,
        product_url: str,
        max_offers: int = 25
    ) -> Dict[str, Any]:
        """
        Analyze product starting from a product URL (new workflow).
        
        This is the preferred method for branded products where you want to
        find similar items with different brands.
        """
        logger.info(
            "Starting pricing analysis from product URL",
            url=product_url,
            max_offers=max_offers
        )
        
        start_time = datetime.now()
        result = {
            "product_url": product_url,
            "timestamp": start_time.isoformat(),
            "pipeline_steps": {},
            "final_recommendation": None,
            "errors": []
        }
        
        try:
            # Step 0: Extract pivot product details
            logger.info("Step 0/5: Extracting pivot product details")
            pivot_product = self.scraper.extract_product_details(product_url)
            
            if not pivot_product:
                error_msg = "Failed to extract product details from URL"
                logger.error(error_msg)
                result["errors"].append(error_msg)
                return result
            
            result["pipeline_steps"]["pivot_product"] = {
                "status": "completed",
                "product_id": pivot_product.product_id,
                "title": pivot_product.title,
                "price": pivot_product.price,
                "brand": pivot_product.brand,
                "attributes": pivot_product.attributes
            }
            
            # Step 1: Generate search strategy
            logger.info("Step 1/5: Generating search strategy")
            search_strategy = self.search_strategy_agent.generate_search_terms(pivot_product)
            
            result["pipeline_steps"]["search_strategy"] = {
                "status": "completed",
                "primary_search": search_strategy.get("primary_search"),
                "alternative_searches": search_strategy.get("alternative_searches"),
                "key_specs": search_strategy.get("key_specs"),
                "reasoning": search_strategy.get("reasoning")
            }
            
            # Step 2: Scrape products using optimized search
            logger.info("Step 2/5: Scraping Mercado Libre with optimized search")
            search_term = search_strategy.get("primary_search")
            scraping_result = self.scraper.search_products(
                description=search_term,
                max_offers=max_offers
            )
            
            result["pipeline_steps"]["scraping"] = {
                "status": "completed",
                "search_term": search_term,
                "strategy": scraping_result.strategy,
                "offers_found": len(scraping_result.offers),
                "url": scraping_result.listing_url
            }
            
            if not scraping_result.offers:
                error_msg = "No offers found"
                logger.warning(error_msg)
                result["errors"].append(error_msg)
                return result
            
            # Step 3: Filter comparable products
            logger.info("Step 3/5: Filtering comparable products")
            matching_result = await self.matching_agent.execute(
                target_product=pivot_product.title,
                offers=scraping_result.offers
            )
            
            result["pipeline_steps"]["matching"] = {
                "status": "completed",
                "total_offers": len(scraping_result.offers),
                "comparable": len(matching_result["comparable_offers"]),
                "excluded": len(matching_result["excluded_offers"])
            }
            
            comparable_offers = matching_result["comparable_offers"]
            if not comparable_offers:
                error_msg = "No comparable products found after filtering"
                logger.warning(error_msg)
                result["errors"].append(error_msg)
                return result
            
            # Step 4: Calculate statistics
            logger.info("Step 4/5: Calculating price statistics")
            statistics = get_price_recommendation_data(comparable_offers)
            
            result["pipeline_steps"]["statistics"] = {
                "status": "completed",
                "total_offers": statistics.get("total_offers"),
                "outliers_removed": statistics.get("outliers_removed"),
                "price_distribution": statistics.get("price_distribution"),
                "by_condition": statistics.get("by_condition")
            }
            
            # Step 5: Generate pricing recommendation
            logger.info("Step 5/5: Generating pricing recommendation")
            recommendation = self.pricing_agent.execute(
                target_product=pivot_product.title,
                statistics=statistics,
                comparable_count=len(comparable_offers)
            )
            
            result["pipeline_steps"]["recommendation"] = {
                "status": "completed"
            }
            result["final_recommendation"] = recommendation
            
        except Exception as e:
            error_msg = f"Pipeline error: {str(e)}"
            logger.error(error_msg, exc_info=True)
            result["errors"].append(error_msg)
        
        # Calculate duration
        duration = (datetime.now() - start_time).total_seconds()
        result["duration_seconds"] = duration
        
        logger.info(
            "Pricing analysis completed",
            duration=duration,
            errors_count=len(result["errors"]),
            has_recommendation=result["final_recommendation"] is not None
        )
        
        return result
    
    async def _analyze_from_description(
        self,
        product_description: str,
        max_offers: int = 25
    ) -> Dict[str, Any]:
        """
        Analyze product from description (legacy workflow).
        """
        logger.info(
            "Starting complete pricing analysis",
            product=product_description,
            max_offers=max_offers
        )
        
        start_time = datetime.now()
        result = {
            "product": product_description,
            "timestamp": start_time.isoformat(),
            "pipeline_steps": {},
            "final_recommendation": None,
            "errors": []
        }
        
        try:
            # Step 1: Scrape products from HTML
            logger.info("Step 1/4: Scraping Mercado Libre")
            scraping_result = self.scraper.search_products(
                description=product_description,
                max_offers=max_offers
            )
            
            result["pipeline_steps"]["1_scraping"] = {
                "status": "completed",
                "strategy": scraping_result.strategy,
                "offers_found": len(scraping_result.offers),
                "url": scraping_result.listing_url
            }
            
            if not scraping_result.offers:
                result["errors"].append("No products found in scraping")
                logger.warning("No offers found, stopping pipeline")
                return result
            
            # Convert offers to dict for agent
            raw_offers = [o.to_dict() for o in scraping_result.offers]
            
            # Step 2: Filter comparable products using LLM
            logger.info("Step 2/4: Filtering comparable products")
            matching_result = await self.matching_agent.execute(
                target_product=product_description,
                raw_offers=raw_offers
            )
            
            result["pipeline_steps"]["2_matching"] = {
                "status": "completed",
                "total_offers": matching_result["total_offers"],
                "comparable_count": matching_result["comparable_count"],
                "excluded_count": matching_result["excluded_count"]
            }
            
            if matching_result["comparable_count"] < 3:
                result["errors"].append(
                    f"Too few comparable products: {matching_result['comparable_count']}"
                )
                logger.warning("Insufficient comparable products")
            
            # Step 3: Calculate statistics (no LLM)
            logger.info("Step 3/4: Calculating price statistics")
            
            # Convert back to Offer objects for stats
            from app.mcp_servers.mercadolibre.models import Offer
            comparable_offers = [
                Offer(**offer_dict) 
                for offer_dict in matching_result["comparable_offers"]
            ]
            
            statistics = get_price_recommendation_data(comparable_offers)
            
            result["pipeline_steps"]["3_statistics"] = {
                "status": "completed",
                "analysis": statistics
            }
            
            # Step 4: Generate pricing recommendation using LLM
            logger.info("Step 4/4: Generating pricing recommendation")
            pricing_result = await self.pricing_agent.execute(
                target_product=product_description,
                statistics=statistics,
                comparable_count=matching_result["comparable_count"]
            )
            
            result["pipeline_steps"]["4_recommendation"] = {
                "status": "completed" if pricing_result["success"] else "failed",
                "recommendation": pricing_result["recommendation"]
            }
            
            result["final_recommendation"] = pricing_result["recommendation"]
            
            if pricing_result["errors"]:
                result["errors"].extend(pricing_result["errors"])
            
        except Exception as e:
            logger.error(f"Pipeline error: {str(e)}", exc_info=True)
            result["errors"].append(f"Pipeline failure: {str(e)}")
        
        # Calculate duration
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        result["duration_seconds"] = duration
        
        logger.info(
            "Pricing analysis completed",
            duration=duration,
            has_recommendation=result["final_recommendation"] is not None,
            errors_count=len(result["errors"])
        )
        
        return result
    
    async def analyze_multiple_products(
        self,
        product_descriptions: list[str],
        max_offers_per_product: int = 25
    ) -> Dict[str, Any]:
        """
        Analyze multiple products in parallel.
        
        Args:
            product_descriptions: List of products to analyze
            max_offers_per_product: Max offers per product
            
        Returns:
            Results for all products
        """
        logger.info(
            "Starting batch analysis",
            products_count=len(product_descriptions)
        )
        
        # Run analyses in parallel
        tasks = [
            self.analyze_product(desc, max_offers_per_product)
            for desc in product_descriptions
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Process results
        successful = [r for r in results if isinstance(r, dict) and not r.get("errors")]
        failed = [r for r in results if not isinstance(r, dict) or r.get("errors")]
        
        return {
            "total_products": len(product_descriptions),
            "successful": len(successful),
            "failed": len(failed),
            "results": results
        }


# Convenience function for quick analysis
async def quick_price_analysis(product: str) -> Dict[str, Any]:
    """
    Quick pricing analysis for a single product.
    
    Args:
        product: Product description
        
    Returns:
        Analysis result
    """
    pipeline = PricingPipeline()
    return await pipeline.analyze_product(product)
