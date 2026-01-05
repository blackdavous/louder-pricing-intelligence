"""
Demo: Pricing Pipeline with Pivot Product (URL Mode)

This demo shows the NEW workflow for analyzing imported/rebranded products:
1. Extract complete specifications from your product URL
2. LLM generates optimal search terms based on specifications
3. Search for similar products (different brands, similar specs)
4. LLM filters comparable products
5. Calculate price statistics
6. LLM generates pricing recommendation

Example: Louder branded speaker (imported from China, rebranded)
Goal: Find competitors with similar specs but different brands

Run: python scripts/demo_pivot_product.py
"""
import asyncio
import sys
import json
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add backend to path
backend_path = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_path))

from app.agents.pricing_pipeline import PricingPipeline


def print_header(title: str):
    """Print section header."""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70 + "\n")


async def main():
    """Run the demo with pivot product URL."""
    
    print_header("PRICING PIPELINE - Pivot Product Mode")
    print("Analyzing YOUR product and finding similar competitors")
    print("Ideal for imported/rebranded products\n")
    
    # Your Louder product URL
    pivot_url = "https://www.mercadolibre.com.mx/bocina-techo-louder-ypo-900red-5-pulgadas-ambientales-10w-linea-70-100v/p/MLM50988032"
    
    print(f"🎯 Pivot Product: Louder YPO-900RED")
    print(f"   URL: {pivot_url}\n")
    
    pipeline = PricingPipeline()
    
    print("⏳ Running pipeline (5 steps + pivot extraction)...")
    print("   0. Extract pivot product specifications")
    print("   1. Generate search strategy (LLM)")
    print("   2. Scrape similar products from ML")
    print("   3. Filter comparable products (LLM)")
    print("   4. Calculate price statistics")
    print("   5. Generate pricing recommendation (LLM)\n")
    
    result = await pipeline.analyze_product(
        product_input=pivot_url,
        max_offers=30
    )
    
    # Step 0: Pivot Product
    if "pivot_product" in result.get("pipeline_steps", {}):
        print_header("Step 0: Pivot Product Extracted")
        pivot = result["pipeline_steps"]["pivot_product"]
        print(f"✅ Status: {pivot.get('status')}")
        print(f"\n   Product ID: {pivot.get('product_id')}")
        print(f"   Title: {pivot.get('title')}")
        print(f"   Price: ${pivot.get('price'):,.2f} MXN")
        print(f"   Brand: {pivot.get('brand', 'N/A')}")
        
        if pivot.get('attributes'):
            print(f"\n   📋 Specifications:")
            for key, value in pivot.get('attributes', {}).items():
                print(f"      • {key}: {value}")
    
    # Step 1: Search Strategy
    if "search_strategy" in result.get("pipeline_steps", {}):
        print_header("Step 1: Search Strategy Generated (LLM)")
        strategy = result["pipeline_steps"]["search_strategy"]
        print(f"✅ Status: {strategy.get('status')}")
        print(f"\n   🔍 Primary Search: \"{strategy.get('primary_search')}\"")
        
        if strategy.get('alternative_searches'):
            print(f"\n   🔄 Alternatives:")
            for i, alt in enumerate(strategy.get('alternative_searches', []), 1):
                print(f"      {i}. {alt}")
        
        if strategy.get('key_specs'):
            print(f"\n   🎯 Key Specs to Match:")
            for spec in strategy.get('key_specs', []):
                print(f"      • {spec}")
        
        if strategy.get('reasoning'):
            print(f"\n   💡 Reasoning:")
            print(f"      {strategy.get('reasoning')}")
    
    # Step 2: Scraping
    if "scraping" in result.get("pipeline_steps", {}):
        print_header("Step 2: Scraping Results")
        scraping = result["pipeline_steps"]["scraping"]
        print(f"✅ Status: {scraping.get('status')}")
        print(f"\n   Search Term: \"{scraping.get('search_term')}\"")
        print(f"   Strategy: {scraping.get('strategy')}")
        print(f"   Offers Found: {scraping.get('offers_found')}")
        print(f"   URL: {scraping.get('url', '')[:70]}...")
    
    # Step 3: Matching
    if "matching" in result.get("pipeline_steps", {}):
        print_header("Step 3: Product Matching (LLM)")
        matching = result["pipeline_steps"]["matching"]
        print(f"✅ Status: {matching.get('status')}")
        print(f"\n   Total Offers: {matching.get('total_offers')}")
        print(f"   Comparable: {matching.get('comparable')}")
        print(f"   Excluded: {matching.get('excluded')}")
        keep_rate = (matching.get('comparable', 0) / matching.get('total_offers', 1)) * 100
        print(f"   Keep Rate: {keep_rate:.1f}%")
    
    # Step 4: Statistics
    if "statistics" in result.get("pipeline_steps", {}):
        print_header("Step 4: Price Statistics")
        stats = result["pipeline_steps"]["statistics"]
        print(f"✅ Status: {stats.get('status')}")
        print(f"\n   Total Offers: {stats.get('total_offers')}")
        print(f"   Outliers Removed: {stats.get('outliers_removed')}")
        
        dist = stats.get('price_distribution', {})
        if dist:
            print(f"\n   📊 Price Distribution:")
            print(f"      Min:    ${dist.get('min', 0):>10,.2f} MXN")
            print(f"      Q1:     ${dist.get('q1', 0):>10,.2f} MXN")
            print(f"      Median: ${dist.get('median', 0):>10,.2f} MXN")
            print(f"      Q3:     ${dist.get('q3', 0):>10,.2f} MXN")
            print(f"      Max:    ${dist.get('max', 0):>10,.2f} MXN")
            print(f"      Mean:   ${dist.get('mean', 0):>10,.2f} MXN")
        
        by_cond = stats.get('by_condition', {})
        if by_cond:
            print(f"\n   📦 By Condition:")
            for condition, data in by_cond.items():
                print(f"      {condition.upper()}: {data.get('count')} offers, median ${data.get('median', 0):,.2f}")
    
    # Step 5: Recommendation
    if result.get("final_recommendation"):
        print_header("Step 5: Pricing Recommendation (LLM)")
        rec = result["final_recommendation"]
        print(f"✅ Status: completed")
        print(f"\n   💰 RECOMMENDED PRICE: ${rec.get('recommended_price', 0):,.2f} {rec.get('currency', 'MXN')}")
        print(f"   📊 Strategy: {rec.get('strategy', 'N/A').upper()}")
        print(f"   🎯 Confidence: {rec.get('confidence_score', 0) * 100:.1f}%")
        
        if rec.get('market_position'):
            print(f"   📍 Position: {rec['market_position']}")
        
        if rec.get('reasoning'):
            print(f"\n   📝 Reasoning:")
            for reason in rec['reasoning']:
                print(f"      • {reason}")
        
        if rec.get('risk_factors'):
            print(f"\n   ⚠️  Risk Factors:")
            for risk in rec['risk_factors']:
                print(f"      • {risk}")
        
        if rec.get('alternative_prices'):
            print(f"\n   🔄 Alternative Prices:")
            for scenario, price in rec['alternative_prices'].items():
                print(f"      {scenario.title()}: ${price:,.2f} {rec.get('currency', 'MXN')}")
    
    # Summary
    print_header("SUMMARY")
    duration = result.get("duration_seconds", 0)
    print(f"   ⏱️  Duration: {duration:.2f} seconds")
    
    errors = result.get("errors", [])
    if errors:
        print(f"\n   ⚠️  Errors:")
        for error in errors:
            print(f"      • {error}")
    else:
        print(f"\n   ✅ Analysis completed successfully!")
    
    # Save results
    output_file = "pricing_analysis_pivot.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    
    print(f"\n   📄 Full results: {output_file}")
    print("=" * 70 + "\n")
    
    print("\n✅ Demo completed!")


if __name__ == "__main__":
    asyncio.run(main())
