"""
MCP Server for Analytics and Statistical Calculations.

Provides tools for:
- Statistical calculations
- Percentile analysis
- Price recommendations
- Market analysis
"""
from typing import List, Dict, Any, Optional
import numpy as np
from scipy import stats
from datetime import datetime

from app.core.logging import get_logger

logger = get_logger(__name__)


class AnalyticsEngine:
    """
    Analytics engine for pricing intelligence.
    
    Provides statistical analysis, percentile calculations,
    and recommendation generation.
    """
    
    @staticmethod
    def calculate_stats(prices: List[float]) -> Dict[str, Any]:
        """
        Calculate comprehensive statistics from price list.
        
        Args:
            prices: List of prices
        
        Returns:
            Dict with statistical measures
        """
        logger.info("Calculating price statistics", sample_size=len(prices))
        
        if not prices:
            return {
                "success": False,
                "error": "Empty price list",
                "sample_size": 0
            }
        
        prices_array = np.array(prices)
        
        # Remove outliers using IQR method
        q1 = np.percentile(prices_array, 25)
        q3 = np.percentile(prices_array, 75)
        iqr = q3 - q1
        lower_bound = q1 - 1.5 * iqr
        upper_bound = q3 + 1.5 * iqr
        
        prices_no_outliers = prices_array[
            (prices_array >= lower_bound) & (prices_array <= upper_bound)
        ]
        
        outliers_removed = len(prices_array) - len(prices_no_outliers)
        
        # Calculate statistics
        result = {
            "success": True,
            "sample_size": len(prices),
            "sample_size_clean": len(prices_no_outliers),
            "outliers_removed": outliers_removed,
            "min": float(np.min(prices_array)),
            "max": float(np.max(prices_array)),
            "mean": float(np.mean(prices_array)),
            "median": float(np.median(prices_array)),
            "std_dev": float(np.std(prices_array)),
            "variance": float(np.var(prices_array)),
            "cv": float(np.std(prices_array) / np.mean(prices_array)) if np.mean(prices_array) > 0 else 0,
            "q1": float(np.percentile(prices_array, 25)),
            "q3": float(np.percentile(prices_array, 75)),
            "iqr": float(iqr),
            "percentiles": {
                "p10": float(np.percentile(prices_array, 10)),
                "p20": float(np.percentile(prices_array, 20)),
                "p25": float(np.percentile(prices_array, 25)),
                "p30": float(np.percentile(prices_array, 30)),
                "p40": float(np.percentile(prices_array, 40)),
                "p50": float(np.percentile(prices_array, 50)),
                "p60": float(np.percentile(prices_array, 60)),
                "p70": float(np.percentile(prices_array, 70)),
                "p75": float(np.percentile(prices_array, 75)),
                "p80": float(np.percentile(prices_array, 80)),
                "p90": float(np.percentile(prices_array, 90)),
            },
            "clean_stats": {
                "mean": float(np.mean(prices_no_outliers)),
                "median": float(np.median(prices_no_outliers)),
                "std_dev": float(np.std(prices_no_outliers)),
            },
            "timestamp": datetime.utcnow().isoformat()
        }
        
        logger.info(
            "Statistics calculated",
            sample_size=result["sample_size"],
            mean=result["mean"],
            median=result["median"]
        )
        
        return result
    
    @staticmethod
    def get_percentile(prices: List[float], percentile: float) -> Dict[str, Any]:
        """
        Get specific percentile value from price distribution.
        
        Args:
            prices: List of prices
            percentile: Percentile to calculate (0-100)
        
        Returns:
            Dict with percentile value and context
        """
        logger.info("Calculating percentile", percentile=percentile, sample_size=len(prices))
        
        if not prices:
            return {
                "success": False,
                "error": "Empty price list",
                "percentile": percentile
            }
        
        if not 0 <= percentile <= 100:
            return {
                "success": False,
                "error": f"Invalid percentile: {percentile}. Must be between 0 and 100",
                "percentile": percentile
            }
        
        prices_array = np.array(prices)
        value = float(np.percentile(prices_array, percentile))
        
        # Calculate how many prices are below/above
        below = np.sum(prices_array < value)
        above = np.sum(prices_array > value)
        equal = np.sum(prices_array == value)
        
        result = {
            "success": True,
            "percentile": percentile,
            "value": value,
            "sample_size": len(prices),
            "below_count": int(below),
            "above_count": int(above),
            "equal_count": int(equal),
            "rank_position": int(below + 1),
            "timestamp": datetime.utcnow().isoformat()
        }
        
        logger.info("Percentile calculated", percentile=percentile, value=value)
        
        return result
    
    @staticmethod
    def generate_recommendation(
        cost_price: float,
        competitor_prices: List[float],
        target_margin_percent: float = 30.0,
        target_percentile: Optional[float] = None,
        current_price: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Generate pricing recommendation based on cost and competition.
        
        Args:
            cost_price: Product cost
            competitor_prices: List of competitor prices
            target_margin_percent: Desired profit margin
            target_percentile: Target market position (0-100)
            current_price: Current selling price (optional)
        
        Returns:
            Dict with recommendation
        """
        logger.info(
            "Generating pricing recommendation",
            cost=cost_price,
            competitors=len(competitor_prices),
            target_margin=target_margin_percent
        )
        
        if not competitor_prices:
            # No competitors - use cost + margin
            recommended = cost_price * (1 + target_margin_percent / 100)
            return {
                "success": True,
                "recommended_price": round(recommended, 2),
                "cost_price": cost_price,
                "margin_percent": target_margin_percent,
                "confidence": "low",
                "reasoning": "No competitor data available. Price based on target margin only.",
                "market_position": "unknown",
                "competitors_analyzed": 0,
                "timestamp": datetime.utcnow().isoformat()
            }
        
        # Calculate statistics
        stats_result = AnalyticsEngine.calculate_stats(competitor_prices)
        
        # Determine target percentile based on margin feasibility
        min_viable_price = cost_price * (1 + target_margin_percent / 100)
        
        if target_percentile is None:
            # Auto-determine based on cost
            if min_viable_price <= stats_result["percentiles"]["p25"]:
                target_percentile = 25.0
                position = "budget"
            elif min_viable_price <= stats_result["median"]:
                target_percentile = 50.0
                position = "competitive"
            elif min_viable_price <= stats_result["percentiles"]["p75"]:
                target_percentile = 75.0
                position = "premium"
            else:
                target_percentile = 90.0
                position = "luxury"
        else:
            # Determine position from target percentile
            if target_percentile <= 30:
                position = "budget"
            elif target_percentile <= 60:
                position = "competitive"
            elif target_percentile <= 80:
                position = "premium"
            else:
                position = "luxury"
        
        # Get price at target percentile
        recommended = float(np.percentile(competitor_prices, target_percentile))
        
        # Ensure minimum margin
        if recommended < min_viable_price:
            recommended = min_viable_price
            logger.warning(
                "Recommended price below minimum viable",
                recommended=recommended,
                min_viable=min_viable_price
            )
        
        # Calculate actual margin
        actual_margin = ((recommended - cost_price) / cost_price) * 100
        
        # Determine confidence
        if stats_result["sample_size"] >= 30 and stats_result["cv"] < 0.3:
            confidence = "high"
        elif stats_result["sample_size"] >= 15 and stats_result["cv"] < 0.5:
            confidence = "medium"
        else:
            confidence = "low"
        
        # Generate alternatives
        alternatives = [
            float(np.percentile(competitor_prices, max(0, target_percentile - 15))),
            recommended,
            float(np.percentile(competitor_prices, min(100, target_percentile + 15)))
        ]
        
        # Calculate current position if provided
        current_position = None
        if current_price:
            current_position = {
                "price": current_price,
                "percentile": float(stats.percentileofscore(competitor_prices, current_price)),
                "margin_percent": ((current_price - cost_price) / cost_price) * 100
            }
        
        result = {
            "success": True,
            "recommended_price": round(recommended, 2),
            "cost_price": cost_price,
            "margin_percent": round(actual_margin, 2),
            "target_percentile": target_percentile,
            "confidence": confidence,
            "market_position": position,
            "competitors_analyzed": stats_result["sample_size"],
            "price_range": {
                "min": stats_result["min"],
                "max": stats_result["max"],
                "median": stats_result["median"],
                "mean": stats_result["mean"]
            },
            "alternatives": [round(p, 2) for p in alternatives],
            "current_position": current_position,
            "statistics": stats_result,
            "reasoning": f"Based on analysis of {stats_result['sample_size']} competitors, "
                        f"recommended price at {target_percentile}th percentile ({position} positioning) "
                        f"with {round(actual_margin, 1)}% margin.",
            "timestamp": datetime.utcnow().isoformat()
        }
        
        logger.info(
            "Recommendation generated",
            recommended_price=result["recommended_price"],
            confidence=confidence,
            margin=result["margin_percent"]
        )
        
        return result


# Singleton instance
analytics_engine = AnalyticsEngine()


# MCP Tool Functions
async def calculate_stats_tool(prices: List[float]) -> Dict[str, Any]:
    """
    MCP Tool: Calculate comprehensive price statistics.
    
    Returns mean, median, percentiles, std dev, and more.
    """
    return analytics_engine.calculate_stats(prices)


async def get_percentile_tool(prices: List[float], percentile: float) -> Dict[str, Any]:
    """
    MCP Tool: Get specific percentile from price distribution.
    
    Useful for understanding market positioning.
    """
    return analytics_engine.get_percentile(prices, percentile)


async def generate_recommendation_tool(
    cost_price: float,
    competitor_prices: List[float],
    target_margin_percent: float = 30.0,
    target_percentile: Optional[float] = None,
    current_price: Optional[float] = None
) -> Dict[str, Any]:
    """
    MCP Tool: Generate intelligent pricing recommendation.
    
    Analyzes competition and generates optimal pricing strategy.
    """
    return analytics_engine.generate_recommendation(
        cost_price=cost_price,
        competitor_prices=competitor_prices,
        target_margin_percent=target_margin_percent,
        target_percentile=target_percentile,
        current_price=current_price
    )
