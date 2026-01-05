"""
Statistical analysis for pricing data.
Migrated from agente_precios_ml_gagr.ipynb
"""
import statistics
from typing import List, Dict, Any, Tuple

from .models import Offer, PriceStatistics
from app.core.logging import get_logger

logger = get_logger(__name__)


def percentile(values: List[float], p: float) -> float:
    """
    Calculate percentile of a list of values.
    
    Args:
        values: List of numeric values
        p: Percentile (0.0 to 1.0)
        
    Returns:
        Percentile value
    """
    xs = sorted(values)
    if len(xs) == 1:
        return xs[0]
    
    k = (len(xs) - 1) * p
    f = int(k)
    c = min(f + 1, len(xs) - 1)
    
    if f == c:
        return xs[f]
    
    return xs[f] + (k - f) * (xs[c] - xs[f])


def iqr_bounds(values: List[float]) -> Tuple[float, float, float, float]:
    """
    Calculate IQR (Interquartile Range) bounds for outlier detection.
    
    Args:
        values: List of numeric values
        
    Returns:
        Tuple of (q1, q3, lower_bound, upper_bound)
    """
    q1 = percentile(values, 0.25)
    q3 = percentile(values, 0.75)
    iqr = q3 - q1
    
    lower_bound = q1 - 1.5 * iqr
    upper_bound = q3 + 1.5 * iqr
    
    return q1, q3, lower_bound, upper_bound


def calculate_statistics(values: List[float]) -> PriceStatistics:
    """
    Calculate basic statistics for a list of prices.
    
    Args:
        values: List of prices
        
    Returns:
        PriceStatistics object
    """
    if not values:
        raise ValueError("Cannot calculate statistics for empty list")
    
    xs = sorted(values)
    
    stats = PriceStatistics(
        n=len(xs),
        min=xs[0],
        max=xs[-1],
        mean=sum(xs) / len(xs),
        median=statistics.median(xs)
    )
    
    # Calculate IQR if enough data points
    if len(xs) >= 4:
        q1, q3, _, _ = iqr_bounds(xs)
        stats.q1 = q1
        stats.q3 = q3
        stats.iqr = q3 - q1
    
    return stats


def remove_outliers(offers: List[Offer]) -> Tuple[List[Offer], List[Offer]]:
    """
    Remove price outliers using IQR method.
    
    Args:
        offers: List of offers
        
    Returns:
        Tuple of (inliers, outliers)
    """
    if len(offers) < 4:
        # Not enough data for outlier detection
        return offers, []
    
    prices = [o.price for o in offers]
    q1, q3, lower, upper = iqr_bounds(prices)
    
    inliers = [o for o in offers if lower <= o.price <= upper]
    outliers = [o for o in offers if o.price < lower or o.price > upper]
    
    logger.info(
        "Outlier detection completed",
        total=len(offers),
        inliers=len(inliers),
        outliers=len(outliers),
        q1=q1,
        q3=q3,
        lower_bound=lower,
        upper_bound=upper
    )
    
    return inliers, outliers


def analyze_by_condition(offers: List[Offer]) -> Dict[str, Any]:
    """
    Analyze offers grouped by condition (new/used/unknown).
    
    Args:
        offers: List of offers
        
    Returns:
        Dict with statistics per condition
    """
    if not offers:
        return {"new": None, "used": None, "unknown": None}
    
    # Group by condition
    groups = {"new": [], "used": [], "unknown": []}
    for o in offers:
        condition = o.condition if o.condition in groups else "unknown"
        groups[condition].append(o)
    
    result = {}
    
    for condition, cond_offers in groups.items():
        if not cond_offers:
            result[condition] = None
            continue
        
        prices = [o.price for o in cond_offers]
        
        # All offers stats
        stats_all = calculate_statistics(prices)
        
        # Remove outliers if enough data
        inliers = cond_offers
        outliers_removed = 0
        stats_clean = None
        
        if len(cond_offers) >= 4:
            inliers, outliers = remove_outliers(cond_offers)
            outliers_removed = len(outliers)
            
            if inliers:
                clean_prices = [o.price for o in inliers]
                stats_clean = calculate_statistics(clean_prices)
                stats_clean.outliers_removed = outliers_removed
        
        result[condition] = {
            "count": len(cond_offers),
            "stats_all": stats_all.to_dict(),
            "stats_clean": stats_clean.to_dict() if stats_clean else None,
            "sample_offers": [o.to_dict() for o in cond_offers[:5]]  # First 5 as sample
        }
    
    return result


def get_price_recommendation_data(offers: List[Offer]) -> Dict[str, Any]:
    """
    Prepare data for pricing recommendation.
    
    This function analyzes offers and provides clean data for the
    pricing agent to make recommendations.
    
    Args:
        offers: List of offers
        
    Returns:
        Dict with analysis data for recommendation
    """
    logger.info("Preparing pricing recommendation data", total_offers=len(offers))
    
    if not offers:
        return {
            "error": "No offers available",
            "by_condition": {},
            "overall": None
        }
    
    # Analyze by condition
    by_condition = analyze_by_condition(offers)
    
    # Overall statistics (all conditions combined)
    all_prices = [o.price for o in offers]
    overall_stats = calculate_statistics(all_prices)
    
    # Remove outliers from overall
    inliers, outliers = remove_outliers(offers)
    clean_prices = [o.price for o in inliers]
    clean_stats = calculate_statistics(clean_prices) if clean_prices else None
    
    if clean_stats:
        clean_stats.outliers_removed = len(outliers)
    
    return {
        "by_condition": by_condition,
        "overall": {
            "total_offers": len(offers),
            "stats_all": overall_stats.to_dict(),
            "stats_clean": clean_stats.to_dict() if clean_stats else None,
            "outliers_removed": len(outliers)
        },
        "price_distribution": {
            "min": overall_stats.min,
            "q1": overall_stats.q1,
            "median": overall_stats.median,
            "q3": overall_stats.q3,
            "max": overall_stats.max
        }
    }
