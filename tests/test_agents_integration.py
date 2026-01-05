"""
Integration test for LangGraph Agents with MCP Servers.

This test validates the complete workflow:
1. MarketResearchAgent → MCP Mercado Libre (search_products)
2. DataExtractorAgent → MCP Mercado Libre (batch_get_prices)
3. PricingIntelligenceAgent → MCP Analytics (stats + recommendation)
"""
import pytest
import asyncio
from typing import List, Dict, Any

from app.agents.market_research import MarketResearchAgent
from app.agents.data_extractor import DataExtractorAgent
from app.agents.pricing_intelligence import PricingIntelligenceAgent


@pytest.mark.asyncio
class TestAgentsIntegration:
    """Integration tests for agents with MCP servers."""
    
    async def test_market_research_agent_with_mcp(self):
        """Test MarketResearchAgent with MCP Mercado Libre integration."""
        agent = MarketResearchAgent()
        
        # Run market research for a real product
        result = await agent.run(
            product_name="Parlante JBL Flip 6",
            product_attributes={
                "brand": "JBL",
                "model": "Flip 6",
                "category": "audio"
            }
        )
        
        # Validations
        assert result is not None
        assert result["product_name"] == "Parlante JBL Flip 6"
        assert len(result.get("search_queries", [])) > 0
        
        # Should find products on ML (if API credentials are set)
        if result.get("total_found", 0) > 0:
            assert len(result.get("raw_results", [])) > 0
            assert len(result.get("competitor_products", [])) > 0
            
            # Check competitor structure
            first_competitor = result["competitor_products"][0]
            assert first_competitor.ml_id is not None
            assert first_competitor.price > 0
            assert 0 <= first_competitor.relevance_score <= 1.0
    
    async def test_data_extractor_agent_with_mcp(self):
        """Test DataExtractorAgent with MCP batch_get_prices."""
        agent = DataExtractorAgent()
        
        # Mock raw products (structure from ML API)
        raw_products = [
            {
                "id": "MLM123456",
                "title": "Parlante JBL Flip 6 Bluetooth",
                "price": 2499,
                "currency_id": "MXN"
            },
            {
                "id": "MLM789012",
                "title": "JBL Charge 5 Parlante Portátil",
                "price": 3299,
                "currency_id": "MXN"
            }
        ]
        
        result = await agent.run(raw_products)
        
        # Validations
        assert result is not None
        assert len(result["raw_products"]) == 2
        
        # With MCP, batch_get_prices should return products
        # (may fail if ML API credentials not set)
        if len(result.get("extracted_products", [])) > 0:
            first_product = result["extracted_products"][0]
            assert first_product.ml_id in ["MLM123456", "MLM789012"]
            assert first_product.price > 0
            assert first_product.currency == "MXN"
    
    async def test_pricing_intelligence_agent_with_mcp(self):
        """Test PricingIntelligenceAgent with MCP Analytics."""
        agent = PricingIntelligenceAgent()
        
        # Sample competitor prices
        competitor_prices = [
            2499.0, 2699.0, 2450.0, 2799.0, 2350.0,
            2650.0, 2500.0, 2750.0, 2400.0, 2600.0
        ]
        
        result = await agent.run(
            product_id="TEST-001",
            product_name="Parlante JBL Flip 6",
            cost_price=1500.0,
            competitor_prices=competitor_prices,
            target_margin_percent=40.0
        )
        
        # Validations
        assert result is not None
        assert result["product_name"] == "Parlante JBL Flip 6"
        assert result["cost_price"] == 1500.0
        
        # Should have statistics from MCP
        assert result.get("price_statistics") is not None
        stats = result["price_statistics"]
        assert stats.sample_size == 10
        assert stats.mean_price > 0
        assert stats.median_price > 0
        assert stats.min_price <= stats.median_price <= stats.max_price
        
        # Should have recommendation from MCP
        assert result.get("recommendation") is not None
        rec = result["recommendation"]
        assert rec.recommended_price > 0
        assert rec.confidence in ["low", "medium", "high"]
        assert rec.market_position in ["budget", "competitive", "premium", "luxury"]
        assert rec.expected_margin_percent >= 0
        assert len(rec.reasoning) > 0
        assert len(rec.alternative_prices) == 3
        
        # Recommendation should respect minimum margin
        min_price = 1500.0 * 1.4  # 40% margin
        assert rec.recommended_price >= min_price
    
    async def test_full_pricing_workflow(self):
        """Test complete workflow: Research → Extract → Price."""
        # Step 1: Market Research
        research_agent = MarketResearchAgent()
        research_result = await research_agent.run(
            product_name="Parlante Bluetooth JBL",
            product_attributes={"category": "audio"}
        )
        
        assert research_result is not None
        
        # Step 2: Data Extraction (using research results)
        if len(research_result.get("raw_results", [])) > 0:
            extractor_agent = DataExtractorAgent()
            extractor_result = await extractor_agent.run(
                research_result["raw_results"][:10]  # Limit to 10 for speed
            )
            
            assert extractor_result is not None
            
            # Step 3: Pricing Intelligence (using extracted prices)
            if len(extractor_result.get("extracted_products", [])) > 0:
                prices = [p.price for p in extractor_result["extracted_products"]]
                
                pricing_agent = PricingIntelligenceAgent()
                pricing_result = await pricing_agent.run(
                    product_id="TEST-WORKFLOW",
                    product_name="Parlante Bluetooth JBL",
                    cost_price=1200.0,
                    competitor_prices=prices,
                    target_margin_percent=35.0
                )
                
                assert pricing_result is not None
                assert pricing_result.get("recommendation") is not None
                
                # Final recommendation should be data-driven
                rec = pricing_result["recommendation"]
                assert rec.recommended_price > 1200.0
                assert rec.confidence in ["low", "medium", "high"]


@pytest.mark.asyncio
class TestAgentsWithMockData:
    """Tests with mock data (no API calls required)."""
    
    async def test_pricing_agent_with_sample_prices(self):
        """Test pricing agent with predefined sample prices."""
        agent = PricingIntelligenceAgent()
        
        # Realistic sample prices for JBL Flip 6
        sample_prices = [
            2350.0, 2399.0, 2449.0, 2499.0, 2549.0,
            2599.0, 2649.0, 2699.0, 2749.0, 2799.0,
            2850.0, 2899.0, 2949.0, 2999.0, 3049.0
        ]
        
        result = await agent.run(
            product_id="SAMPLE-001",
            product_name="JBL Flip 6",
            cost_price=1500.0,
            competitor_prices=sample_prices,
            current_price=2550.0,
            target_margin_percent=40.0
        )
        
        # Detailed validations
        assert result["recommendation"] is not None
        rec = result["recommendation"]
        
        # Verify pricing logic
        assert 1500.0 * 1.4 <= rec.recommended_price <= max(sample_prices)
        assert rec.confidence in ["medium", "high"]  # 15 samples with moderate variance
        assert rec.expected_margin_percent >= 40.0
        
        # Verify alternatives make sense
        assert len(rec.alternative_prices) == 3
        assert rec.alternative_prices[0] < rec.alternative_prices[1] < rec.alternative_prices[2]
    
    async def test_market_research_relevance_scoring(self):
        """Test relevance scoring in market research agent."""
        agent = MarketResearchAgent()
        
        # Manually create mock state with raw results
        state = {
            "product_name": "JBL Flip 6",
            "product_attributes": {},
            "search_queries": [],
            "raw_results": [
                {"id": "1", "title": "JBL Flip 6 Bluetooth Negro", "price": 2499, "seller_id": "123"},
                {"id": "2", "title": "Parlante Sony SRS-XB43", "price": 3999, "seller_id": "456"},
                {"id": "3", "title": "JBL Flip 5 Azul", "price": 1999, "seller_id": "789"},
            ],
            "competitor_products": [],
            "total_found": 3,
            "errors": []
        }
        
        result = await agent.analyze_results(state)
        
        # Validations
        assert len(result["competitor_products"]) == 3
        
        # First result should have highest relevance (exact match)
        competitors = result["competitor_products"]
        assert competitors[0].relevance_score >= competitors[1].relevance_score
        assert "flip" in competitors[0].title.lower()
        assert "jbl" in competitors[0].title.lower() or "jbl" in competitors[2].title.lower()
