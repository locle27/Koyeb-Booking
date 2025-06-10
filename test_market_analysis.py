"""
Demo script để test Market Price Analysis locally
"""

import asyncio
import os
from market_price_analyzer import analyze_market_prices, format_price_analysis_for_display

async def test_market_analysis():
    """Test basic functionality của Market Price Analyzer"""
    
    print("Testing Market Price Analysis...")
    print("=" * 50)
    
    # Test URL cho Khu Phố Cổ
    test_url = """https://www.booking.com/searchresults.vi.html?ss=Khu+Ph%E1%BB%91+C%E1%BB%95&ssne=Khu+Ph%E1%BB%91+C%E1%BB%95&ssne_untouched=Khu+Ph%E1%BB%91+C%E1%BB%95&lang=vi&src=index&dest_id=2096&dest_type=district&checkin=2025-06-11&checkout=2025-06-12&group_adults=2&no_rooms=1&group_children=0&nflt=price%3DVND-min-500000-1"""
    
    print(f"Test URL: {test_url[:100]}...")
    print("Analyzing market prices (max 10 properties for demo)...")
    
    try:
        # Chạy analysis với số lượng ít để test
        result = await analyze_market_prices(
            booking_url=test_url,
            google_api_key=os.getenv("GOOGLE_API_KEY"),  # Optional
            max_properties=10
        )
        
        print("\nRESULTS:")
        print("=" * 30)
        
        if result.get('success'):
            # Format kết quả
            formatted = format_price_analysis_for_display(result)
            
            summary = formatted.get('summary', {})
            properties = formatted.get('properties', [])
            insights = formatted.get('insights', [])
            
            print(f"SUCCESS: Found {summary.get('total_found', 0)} properties")
            print(f"Average Price: {summary.get('avg_price', 0):,.0f}₫")
            print(f"Price Range: {summary.get('min_price', 0):,.0f}₫ - {summary.get('max_price', 0):,.0f}₫")
            print(f"Median Price: {summary.get('median_price', 0):,.0f}₫")
            
            print("\nSAMPLE PROPERTIES:")
            for i, prop in enumerate(properties[:5], 1):
                print(f"{i}. {prop['name'][:50]}... - {prop['price_display']} - {prop['rating']}")
            
            print("\nINSIGHTS:")
            for insight in insights:
                print(f"  • {insight}")
            
            print(f"\nAnalysis completed at: {formatted.get('timestamp', 'N/A')}")
            
        else:
            error = result.get('error', 'Unknown error')
            print(f"FAILED: {error}")
            
            # Kiểm tra fallback mode
            if 'fallback' in str(result):
                print("Using fallback mode (requests + BeautifulSoup)")
            else:
                print("crawl4ai mode attempted")
        
    except Exception as e:
        print(f"EXCEPTION: {e}")
        import traceback
        traceback.print_exc()

async def test_fallback_mode():
    """Test fallback mode specifically"""
    print("\n" + "=" * 50)
    print("🔄 Testing Fallback Mode (requests + BeautifulSoup)")
    print("=" * 50)
    
    from market_price_analyzer import MarketPriceAnalyzer
    
    analyzer = MarketPriceAnalyzer()
    
    # Test simple Booking.com URL
    simple_url = "https://www.booking.com/searchresults.vi.html?ss=Hanoi"
    
    try:
        result = await analyzer._fallback_crawl_booking(simple_url, 5)
        
        if result.get('success'):
            print(f"✅ Fallback SUCCESS: {len(result.get('properties', []))} properties")
            for prop in result.get('properties', [])[:3]:
                print(f"  • {prop.get('name', 'N/A')} - {prop.get('price_display', 'N/A')}")
        else:
            print(f"❌ Fallback FAILED: {result.get('error', 'Unknown')}")
            
    except Exception as e:
        print(f"❌ Fallback EXCEPTION: {e}")
    
    finally:
        await analyzer.cleanup()

def main():
    """Main function to run all tests"""
    print("MARKET PRICE ANALYSIS - DEMO TEST")
    print("=" * 60)
    
    # Chạy tests
    asyncio.run(test_market_analysis())
    asyncio.run(test_fallback_mode())
    
    print("\n" + "=" * 60)
    print("Demo test completed!")
    print("\nNotes:")
    print("  • This is a demo test with limited properties")
    print("  • Real usage will crawl 15-25 properties")
    print("  • Fallback mode works even without crawl4ai")
    print("  • Full functionality available in Flask web interface")

if __name__ == "__main__":
    main()
