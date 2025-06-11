#!/usr/bin/env python3
"""
Debug Market Price Analyzer directly
"""

import asyncio
import os
import sys
from dotenv import load_dotenv

# Load env
load_dotenv()
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

# Import với error handling
try:
    from market_price_analyzer import analyze_market_prices
    print("SUCCESS: market_price_analyzer imported")
except Exception as e:
    print(f"ERROR importing market_price_analyzer: {e}")
    sys.exit(1)

async def test_market_analyzer():
    """Test market analyzer với simple demo data"""
    print("=== TESTING MARKET ANALYZER DIRECTLY ===")
    
    # Simple test URL
    test_url = "https://www.booking.com/searchresults.vi.html"
    
    try:
        print(f"Testing with URL: {test_url}")
        print("Max properties: 3")
        
        # Call analyzer
        result = await analyze_market_prices(
            booking_url=test_url,
            google_api_key=GOOGLE_API_KEY,
            max_properties=3
        )
        
        print(f"Result success: {result.get('success', False)}")
        print(f"Result method: {result.get('method', 'N/A')}")
        
        if result.get('success'):
            properties = result.get('properties', [])
            print(f"Properties count: {len(properties)}")
            
            if properties:
                sample = properties[0]
                print(f"Sample property: {sample.get('name', 'N/A')}")
                print(f"Sample price: {sample.get('price_display', 'N/A')}")
                
                return True
        else:
            print(f"Analysis failed: {result.get('error', 'Unknown error')}")
            
    except Exception as e:
        print(f"Test exception: {e}")
        import traceback
        traceback.print_exc()
        
    return False

if __name__ == "__main__":
    success = asyncio.run(test_market_analyzer())
    print(f"\nTest result: {'PASS' if success else 'FAIL'}")
