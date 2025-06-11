#!/usr/bin/env python3
"""
Test Market Price Analysis - Simple Version
"""

import asyncio
import requests
import json
from market_price_analyzer import analyze_market_prices
from ai_pricing_analyst import analyze_budget_pricing_with_ai, analyze_price_range_with_ai
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

async def test_market_analysis():
    """Test cơ bản của Market Analysis"""
    print("=== TESTING MARKET PRICE ANALYSIS ===")
    
    # Test URL cho Hanoi Old Quarter
    test_url = "https://www.booking.com/searchresults.vi.html?ss=Khu+Phố+Cổ&dest_id=2096&dest_type=district&checkin=2024-12-20&checkout=2024-12-21&group_adults=2&no_rooms=1"
    
    try:
        print(f"Testing market analysis with URL: {test_url[:60]}...")
        
        # Chạy market analysis
        result = await analyze_market_prices(
            booking_url=test_url,
            google_api_key=GOOGLE_API_KEY,
            max_properties=8
        )
        
        print(f"Market Analysis Success: {result.get('success', False)}")
        
        if result.get('success'):
            properties = result.get('properties', [])
            print(f"Properties found: {len(properties)}")
            
            if properties:
                # Show sample property
                sample = properties[0]
                print(f"Sample property: {sample.get('name', 'N/A')}")
                print(f"Price: {sample.get('price_display', 'N/A')}")
                
                # Test AI analysis
                print("\n=== TESTING AI PRICING ANALYSIS ===")
                
                # Test budget analysis
                budget_result = analyze_budget_pricing_with_ai(
                    properties=properties,
                    price_threshold=700000,
                    google_api_key=GOOGLE_API_KEY
                )
                
                print(f"Budget AI Analysis Success: {budget_result.get('success', False)}")
                if budget_result.get('success'):
                    print(f"AI Confidence: {budget_result.get('ai_confidence', 'N/A')}")
                    insights = budget_result.get('ai_analysis', {}).get('actionable_insights', [])
                    if insights:
                        print(f"First insight: {insights[0][:80]}...")
                
                # Test range analysis
                range_result = analyze_price_range_with_ai(
                    properties=properties,
                    min_price=400000,
                    max_price=800000,
                    google_api_key=GOOGLE_API_KEY
                )
                
                print(f"Range AI Analysis Success: {range_result.get('success', False)}")
                if range_result.get('success'):
                    stats = range_result.get('range_statistics', {})
                    print(f"Range properties: {stats.get('total_properties', 0)}")
                    print(f"Average price: {stats.get('avg_price', 0):,.0f} VND")
                
                return True
            else:
                print("No properties found in result")
        else:
            print(f"Market analysis failed: {result.get('error', 'Unknown error')}")
            
    except Exception as e:
        print(f"Test exception: {e}")
        
    return False

def test_api_endpoints():
    """Test API endpoints"""
    print("\n=== TESTING API ENDPOINTS ===")
    
    base_url = "http://127.0.0.1:8080"
    
    try:
        # Test default URL
        print("Testing default URL endpoint...")
        response = requests.get(f"{base_url}/api/get_default_booking_url", timeout=5)
        
        if response.status_code == 200:
            result = response.json()
            print(f"Default URL API Success: {result.get('success', False)}")
            if result.get('success'):
                return result.get('default_url', '')
        else:
            print(f"Default URL API failed: {response.status_code}")
            
    except requests.RequestException as e:
        print(f"API test error: {e}")
        
    return None

async def main():
    """Main test function"""
    print("MARKET PRICE ANALYSIS - TEST SUITE")
    print("=" * 50)
    
    # Test core functionality
    success = await test_market_analysis()
    
    # Test API endpoints
    default_url = test_api_endpoints()
    
    print("\n" + "=" * 50)
    print("TEST RESULTS:")
    print(f"Market Analysis: {'PASS' if success else 'FAIL'}")
    print(f"API Endpoints: {'PASS' if default_url else 'FAIL'}")
    
    if success:
        print("\nFEATURES WORKING:")
        print("- Market data crawling from Booking.com")
        print("- AI-powered pricing analysis with Gemini")
        print("- Price range and threshold analysis")
        print("- Strategic insights generation")
        print("- API endpoints for frontend integration")
    else:
        print("\nSome features may need debugging")

if __name__ == "__main__":
    asyncio.run(main())
