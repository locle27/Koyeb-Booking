"""
Test Market Price Analyzer - Debug script
"""
import asyncio
import sys
import os

# Add parent directory to path để import được modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from market_price_analyzer import analyze_market_prices, format_price_analysis_for_display

async def test_market_analyzer():
    """Test market analyzer với demo data"""
    print("🧪 Testing Market Price Analyzer...")
    
    # Test với URL giả
    test_url = "https://www.booking.com/searchresults.html?ss=Hanoi+Old+Quarter"
    
    try:
        print(f"📊 Testing with URL: {test_url}")
        
        # Run analysis
        result = await analyze_market_prices(
            booking_url=test_url,
            google_api_key=None,  # No API key for test
            max_properties=10
        )
        
        print(f"✅ Raw result success: {result.get('success', False)}")
        print(f"📋 Properties found: {len(result.get('properties', []))}")
        print(f"🔧 Method used: {result.get('method', 'unknown')}")
        
        if result.get('properties'):
            print("📊 Sample properties:")
            for i, prop in enumerate(result['properties'][:3]):
                print(f"  {i+1}. {prop.get('name', 'N/A')} - {prop.get('price_display', 'N/A')}")
        
        # Test formatting
        formatted = format_price_analysis_for_display(result)
        print(f"\n✅ Formatted result success: {formatted.get('success', False)}")
        
        if formatted.get('success'):
            summary = formatted.get('summary', {})
            print(f"📈 Summary:")
            print(f"  - Total: {summary.get('total_found', 0)}")
            print(f"  - Avg price: {summary.get('avg_price', 0):,.0f}₫")
            print(f"  - Min price: {summary.get('min_price', 0):,.0f}₫")
            print(f"  - Max price: {summary.get('max_price', 0):,.0f}₫")
            
            insights = formatted.get('insights', [])
            print(f"💡 Insights ({len(insights)}):")
            for insight in insights[:3]:
                print(f"  - {insight}")
        
        return formatted
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return {"success": False, "error": str(e)}

if __name__ == "__main__":
    # Run test
    result = asyncio.run(test_market_analyzer())
    
    print(f"\n🎯 Final test result: {result.get('success', False)}")
    if not result.get('success'):
        print(f"❌ Error: {result.get('error', 'Unknown error')}")
