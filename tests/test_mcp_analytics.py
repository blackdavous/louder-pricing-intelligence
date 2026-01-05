"""
Tests for Analytics MCP Server.
"""
import pytest
from app.mcp_servers.analytics import (
    analytics_engine,
    calculate_stats_tool,
    get_percentile_tool,
    generate_recommendation_tool,
)


class TestAnalyticsEngine:
    """Test suite for AnalyticsEngine."""
    
    def test_calculate_stats_basic(self):
        """Test basic statistics calculation."""
        prices = [100, 150, 200, 250, 300]
        result = analytics_engine.calculate_stats(prices)
        
        assert result["success"] is True
        assert result["sample_size"] == 5
        assert result["mean"] == 200.0
        assert result["median"] == 200.0
        assert result["min"] == 100.0
        assert result["max"] == 300.0
    
    def test_calculate_stats_with_outliers(self):
        """Test statistics with outlier removal."""
        prices = [100, 110, 120, 130, 140, 1000]  # 1000 is outlier
        result = analytics_engine.calculate_stats(prices)
        
        assert result["success"] is True
        assert result["sample_size"] == 6
        assert result["outliers_removed"] >= 1
        assert result["clean_stats"]["mean"] < result["mean"]
    
    def test_calculate_stats_empty_list(self):
        """Test with empty price list."""
        result = analytics_engine.calculate_stats([])
        
        assert result["success"] is False
        assert "error" in result
    
    def test_get_percentile_50(self):
        """Test median percentile calculation."""
        prices = [10, 20, 30, 40, 50]
        result = analytics_engine.get_percentile(prices, 50)
        
        assert result["success"] is True
        assert result["percentile"] == 50
        assert result["value"] == 30.0
        assert result["sample_size"] == 5
    
    def test_get_percentile_invalid(self):
        """Test invalid percentile."""
        prices = [10, 20, 30]
        result = analytics_engine.get_percentile(prices, 150)
        
        assert result["success"] is False
        assert "error" in result
    
    def test_generate_recommendation_basic(self):
        """Test basic recommendation generation."""
        cost = 100
        competitors = [150, 160, 170, 180, 190, 200]
        result = analytics_engine.generate_recommendation(
            cost_price=cost,
            competitor_prices=competitors,
            target_margin_percent=30.0
        )
        
        assert result["success"] is True
        assert result["recommended_price"] >= cost * 1.3  # At least 30% margin
        assert result["confidence"] in ["low", "medium", "high"]
        assert result["market_position"] in ["budget", "competitive", "premium", "luxury"]
    
    def test_generate_recommendation_no_competitors(self):
        """Test recommendation with no competitor data."""
        cost = 100
        result = analytics_engine.generate_recommendation(
            cost_price=cost,
            competitor_prices=[],
            target_margin_percent=40.0
        )
        
        assert result["success"] is True
        assert result["recommended_price"] == 140.0  # 100 * 1.4
        assert result["confidence"] == "low"
        assert result["competitors_analyzed"] == 0
    
    def test_generate_recommendation_with_current_price(self):
        """Test recommendation including current price analysis."""
        cost = 100
        competitors = [150, 160, 170, 180, 190]
        current = 165
        
        result = analytics_engine.generate_recommendation(
            cost_price=cost,
            competitor_prices=competitors,
            current_price=current
        )
        
        assert result["success"] is True
        assert result["current_position"] is not None
        assert result["current_position"]["price"] == current
        assert "percentile" in result["current_position"]
    
    def test_generate_recommendation_target_percentile(self):
        """Test recommendation with specific target percentile."""
        cost = 50
        competitors = [100, 120, 140, 160, 180, 200]
        
        result = analytics_engine.generate_recommendation(
            cost_price=cost,
            competitor_prices=competitors,
            target_percentile=75.0
        )
        
        assert result["success"] is True
        assert result["target_percentile"] == 75.0
        assert result["market_position"] == "premium"
        assert len(result["alternatives"]) == 3


@pytest.mark.asyncio
class TestAnalyticsMCPTools:
    """Test suite for MCP tool functions."""
    
    async def test_calculate_stats_tool(self):
        """Test calculate_stats MCP tool."""
        prices = [100, 150, 200, 250, 300]
        result = await calculate_stats_tool(prices)
        
        assert result["success"] is True
        assert result["sample_size"] == 5
        assert "percentiles" in result
    
    async def test_get_percentile_tool(self):
        """Test get_percentile MCP tool."""
        prices = [10, 20, 30, 40, 50, 60, 70, 80, 90, 100]
        result = await get_percentile_tool(prices, 90)
        
        assert result["success"] is True
        assert result["percentile"] == 90
        assert result["value"] > 0
    
    async def test_generate_recommendation_tool(self):
        """Test generate_recommendation MCP tool."""
        result = await generate_recommendation_tool(
            cost_price=100,
            competitor_prices=[150, 160, 170, 180, 190],
            target_margin_percent=35.0
        )
        
        assert result["success"] is True
        assert result["recommended_price"] >= 135.0
        assert "reasoning" in result
