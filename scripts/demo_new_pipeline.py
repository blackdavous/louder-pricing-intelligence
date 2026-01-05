"""
Demo: Complete Pricing Pipeline with New Architecture

This script demonstrates the new agent architecture:
- HTML scraping without LLM
- LLM agents for intelligent filtering and recommendation
- Clear separation of concerns

Run: python scripts/demo_new_pipeline.py
"""
import asyncio
import sys
import json
from pathlib import Path

# Add backend to path to find 'app' module
backend_path = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_path))

from app.agents.pricing_pipeline import PricingPipeline
from app.core.logging import get_logger

logger = get_logger(__name__)


def print_section(title: str):
    """Print section header."""
    print("\n" + "="*70)
    print(f"  {title}")
    print("="*70)


def print_scraping_results(step_data: dict):
    """Print scraping step results."""
    print(f"\n✅ Status: {step_data['status']}")
    print(f"   Strategy: {step_data['strategy']}")
    print(f"   Offers Found: {step_data['offers_found']}")
    print(f"   URL: {step_data['url'][:80]}...")


def print_matching_results(step_data: dict):
    """Print matching step results."""
    print(f"\n✅ Status: {step_data['status']}")
    print(f"   Total Offers: {step_data['total_offers']}")
    print(f"   Comparable: {step_data['comparable_count']}")
    print(f"   Excluded: {step_data['excluded_count']}")
    print(f"   Keep Rate: {step_data['comparable_count']/step_data['total_offers']*100:.1f}%")


def print_statistics(step_data: dict):
    """Print statistics step results."""
    print(f"\n✅ Status: {step_data['status']}")
    
    analysis = step_data.get('analysis', {})
    overall = analysis.get('overall', {})
    
    if overall:
        print(f"\n   Overall Market:")
        print(f"   - Total Offers: {overall.get('total_offers', 0)}")
        print(f"   - Outliers Removed: {overall.get('outliers_removed', 0)}")
        
        clean_stats = overall.get('stats_clean', {})
        if clean_stats:
            print(f"\n   Price Distribution (clean):")
            print(f"   - Min:    ${clean_stats.get('min', 0):>10,.2f} MXN")
            print(f"   - Q1:     ${clean_stats.get('q1', 0):>10,.2f} MXN")
            print(f"   - Median: ${clean_stats.get('median', 0):>10,.2f} MXN")
            print(f"   - Q3:     ${clean_stats.get('q3', 0):>10,.2f} MXN")
            print(f"   - Max:    ${clean_stats.get('max', 0):>10,.2f} MXN")
            print(f"   - Mean:   ${clean_stats.get('mean', 0):>10,.2f} MXN")
    
    # By condition
    by_condition = analysis.get('by_condition', {})
    if by_condition:
        print(f"\n   By Condition:")
        for cond, cond_data in by_condition.items():
            if cond_data:
                clean = cond_data.get('stats_clean', {})
                if clean:
                    print(f"   - {cond.upper()}: {cond_data['count']} offers, " +
                          f"median ${clean.get('median', 0):,.2f} MXN")


def print_recommendation(step_data: dict):
    """Print recommendation step results."""
    print(f"\n✅ Status: {step_data['status']}")
    
    rec = step_data.get('recommendation')
    if not rec:
        print("   ⚠️ No recommendation generated")
        return
    
    print(f"\n   💰 RECOMMENDED PRICE: ${rec['recommended_price']:,.2f} MXN")
    print(f"   📊 Strategy: {rec['strategy'].upper()}")
    print(f"   🎯 Confidence: {rec['confidence']:.1%}")
    print(f"   📍 Market Position: {rec['market_position']}")
    
    print(f"\n   📝 Reasoning:")
    reasoning_lines = rec['reasoning'].split('. ')
    for line in reasoning_lines:
        if line.strip():
            print(f"      • {line.strip()}")
    
    if rec.get('risk_factors'):
        print(f"\n   ⚠️  Risk Factors:")
        for risk in rec['risk_factors']:
            print(f"      • {risk}")
    
    if rec.get('alternative_prices'):
        print(f"\n   🔄 Alternative Scenarios:")
        for scenario, price in rec['alternative_prices'].items():
            print(f"      • {scenario.title()}: ${price:,.2f} MXN")


async def demo_single_product():
    """Demo analysis of a single product."""
    print_section("DEMO: Single Product Analysis")
    
    product = "Sony WH-1000XM5 audífonos"
    print(f"\n🔍 Analyzing: {product}")
    
    pipeline = PricingPipeline()
    
    print("\n⏳ Running complete pipeline...")
    print("   1. Scraping HTML from Mercado Libre")
    print("   2. Filtering comparable products (LLM)")
    print("   3. Calculating statistics")
    print("   4. Generating price recommendation (LLM)")
    
    result = await pipeline.analyze_product(product, max_offers=25)
    
    # Print results
    steps = result.get('pipeline_steps', {})
    
    # Step 1: Scraping
    if '1_scraping' in steps:
        print_section("Step 1/4: HTML Scraping")
        print_scraping_results(steps['1_scraping'])
    
    # Step 2: Matching
    if '2_matching' in steps:
        print_section("Step 2/4: Product Matching (LLM Agent)")
        print_matching_results(steps['2_matching'])
    
    # Step 3: Statistics
    if '3_statistics' in steps:
        print_section("Step 3/4: Statistical Analysis")
        print_statistics(steps['3_statistics'])
    
    # Step 4: Recommendation
    if '4_recommendation' in steps:
        print_section("Step 4/4: Pricing Recommendation (LLM Agent)")
        print_recommendation(steps['4_recommendation'])
    
    # Summary
    print_section("SUMMARY")
    print(f"\n   Duration: {result.get('duration_seconds', 0):.2f} seconds")
    
    if result.get('errors'):
        print(f"\n   ⚠️ Errors:")
        for error in result['errors']:
            print(f"      • {error}")
    else:
        print(f"\n   ✅ Analysis completed successfully!")
    
    # Save full results
    output_path = Path(__file__).parent.parent / "pricing_analysis_result.json"
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    
    print(f"\n   📄 Full results saved to: {output_path.name}")
    print("="*70 + "\n")


async def demo_multiple_products():
    """Demo batch analysis of multiple products."""
    print_section("DEMO: Batch Analysis")
    
    products = [
        "Sony WH-1000XM5",
        "Bose QuietComfort 45",
        "JBL Flip 6"
    ]
    
    print(f"\n🔍 Analyzing {len(products)} products:")
    for i, p in enumerate(products, 1):
        print(f"   {i}. {p}")
    
    pipeline = PricingPipeline()
    
    print("\n⏳ Running batch analysis...")
    results = await pipeline.analyze_multiple_products(products, max_offers_per_product=20)
    
    print_section("BATCH RESULTS")
    print(f"\n   Total Products: {results['total_products']}")
    print(f"   ✅ Successful: {results['successful']}")
    print(f"   ❌ Failed: {results['failed']}")
    
    # Show recommendations
    print(f"\n   💰 Price Recommendations:")
    for i, result in enumerate(results['results'], 1):
        if isinstance(result, dict) and result.get('final_recommendation'):
            rec = result['final_recommendation']
            print(f"      {i}. {result['product']}: ${rec['recommended_price']:,.2f} MXN ({rec['strategy']})")
        else:
            print(f"      {i}. {products[i-1]}: ❌ Failed")
    
    print("="*70 + "\n")


async def main():
    """Run demos."""
    print("\n" + "="*70)
    print("  PRICING PIPELINE DEMO - New Architecture")
    print("  Separation of Concerns: Scraping vs Intelligence")
    print("="*70)
    
    try:
        # Demo 1: Single product (detailed)
        await demo_single_product()
        
        # Demo 2: Batch analysis (optional - comment out if slow)
        # await demo_multiple_products()
        
        print("\n✅ Demo completed successfully!\n")
        
    except KeyboardInterrupt:
        print("\n\n⚠️ Demo interrupted by user\n")
    except Exception as e:
        print(f"\n\n❌ Demo failed: {str(e)}\n")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
