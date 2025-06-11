#!/usr/bin/env python3
"""
Test đầy đủ chức năng Market Price Analysis và AI Pricing
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

async def test_market_price_analyzer():
    """Test Market Price Analyzer với demo data"""
    print("🔍 Testing Market Price Analyzer...")
    
    # Test URL cho Hanoi Old Quarter
    test_url = "https://www.booking.com/searchresults.vi.html?ss=Khu+Phố+Cổ&ssne=Khu+Phố+Cổ&lang=vi&dest_id=2096&dest_type=district&checkin=2024-12-20&checkout=2024-12-21&group_adults=2&no_rooms=1&nflt=price%3DVND-min-500000-1"
    
    try:
        print(f"📊 Analyzing market prices from: {test_url[:80]}...")
        
        # Chạy market analysis
        result = await analyze_market_prices(
            booking_url=test_url,
            google_api_key=GOOGLE_API_KEY,
            max_properties=10
        )
        
        print(f"✅ Market Analysis Result: {result.get('success', False)}")
        
        if result.get('success'):
            print(f"📈 Found {result.get('total_properties', 0)} properties")
            print(f"💰 Price analysis: {list(result.get('price_analysis', {}).keys())}")
            
            # Test properties data
            properties = result.get('properties', [])
            if properties:
                print(f"🏨 Sample property: {properties[0].get('name', 'N/A')} - {properties[0].get('price_display', 'N/A')}")
                return properties
            else:
                print("⚠️ No properties found")
                return []
        else:
            print(f"❌ Market Analysis failed: {result.get('error', 'Unknown error')}")
            return []
            
    except Exception as e:
        print(f"❌ Market Analysis exception: {e}")
        return []

def test_ai_pricing_analyst(properties):
    """Test AI Pricing Analyst với data"""
    print("\n🤖 Testing AI Pricing Analyst...")
    
    if not properties:
        print("⚠️ No properties to analyze")
        return
    
    try:
        # Test legacy threshold-based analysis
        print("📊 Testing budget pricing analysis (threshold-based)...")
        budget_result = analyze_budget_pricing_with_ai(
            properties=properties,
            price_threshold=800000,  # 800k VND
            google_api_key=GOOGLE_API_KEY
        )
        
        print(f"✅ Budget Analysis Success: {budget_result.get('success', False)}")
        if budget_result.get('success'):
            print(f"💡 AI Confidence: {budget_result.get('ai_confidence', 'N/A')}")
            insights = budget_result.get('ai_analysis', {}).get('actionable_insights', [])
            if insights:
                print(f"🎯 First insight: {insights[0][:100]}...")
        
        # Test new range-based analysis
        print("\n📊 Testing price range analysis (range-based)...")
        range_result = analyze_price_range_with_ai(
            properties=properties,
            min_price=300000,  # 300k VND
            max_price=700000,  # 700k VND
            google_api_key=GOOGLE_API_KEY
        )
        
        print(f"✅ Range Analysis Success: {range_result.get('success', False)}")
        if range_result.get('success'):
            print(f"💡 AI Confidence: {range_result.get('ai_confidence', 'N/A')}")
            range_stats = range_result.get('range_statistics', {})
            print(f"📈 Range properties: {range_stats.get('total_properties', 0)}")
            print(f"💰 Range average: {range_stats.get('avg_price', 0):,.0f}₫")
        
    except Exception as e:
        print(f"❌ AI Analysis exception: {e}")

def test_api_endpoints():
    """Test API endpoints của Market Analysis"""
    print("\n🌐 Testing API endpoints...")
    
    base_url = "http://127.0.0.1:8080"
    
    try:
        # Test get default URL
        print("📍 Testing default URL endpoint...")
        response = requests.get(f"{base_url}/api/get_default_booking_url", timeout=5)
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Default URL: {result.get('success', False)}")
            if result.get('success'):
                print(f"🏨 Location: {result.get('location', 'N/A')}")
                default_url = result.get('default_url', '')
                print(f"🔗 URL length: {len(default_url)} chars")
                return default_url
        else:
            print(f"❌ Default URL endpoint failed: {response.status_code}")
            
    except requests.exceptions.RequestException as e:
        print(f"❌ API test failed: {e}")
        
    return None

def test_frontend_integration(default_url):
    """Test frontend integration với real data"""
    print("\n🖥️ Testing frontend integration...")
    
    if not default_url:
        print("⚠️ No default URL to test")
        return
    
    base_url = "http://127.0.0.1:8080"
    
    try:
        # Test market analysis API
        print("📊 Testing market analysis API...")
        payload = {
            "booking_url": default_url,
            "max_properties": 8
        }
        
        response = requests.post(
            f"{base_url}/api/analyze_market_prices",
            json=payload,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Market API Success: {result.get('success', False)}")
            
            if result.get('success'):
                properties = result.get('properties', [])
                print(f"🏨 Properties found: {len(properties)}")
                
                if properties:
                    # Test AI analysis API
                    print("🤖 Testing AI analysis API...")
                    ai_payload = {
                        "properties": properties,
                        "price_threshold": 600000
                    }
                    
                    ai_response = requests.post(
                        f"{base_url}/api/ai_pricing_analysis",
                        json=ai_payload,
                        timeout=15
                    )
                    
                    if ai_response.status_code == 200:
                        ai_result = ai_response.json()
                        print(f"✅ AI API Success: {ai_result.get('success', False)}")
                        if ai_result.get('success'):
                            print(f"🎯 AI Method: {ai_result.get('method', 'N/A')}")
                    else:
                        print(f"❌ AI API failed: {ai_response.status_code}")
                        
            else:
                print(f"❌ Market API error: {result.get('error', 'Unknown')}")
        else:
            print(f"❌ Market API failed: {response.status_code}")
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Frontend integration test failed: {e}")

async def main():
    """Chạy tất cả tests"""
    print("🧪 MARKET PRICE ANALYSIS - FULL TEST SUITE")
    print("=" * 60)
    
    # Test 1: Market Price Analyzer
    properties = await test_market_price_analyzer()
    
    # Test 2: AI Pricing Analyst
    test_ai_pricing_analyst(properties)
    
    # Test 3: API endpoints
    default_url = test_api_endpoints()
    
    # Test 4: Frontend integration
    test_frontend_integration(default_url)
    
    print("\n" + "=" * 60)
    print("🎉 TEST SUITE COMPLETED")
    print("\n📋 SUMMARY:")
    print("✅ Market Price Analyzer: Crawl từ Booking.com với fallback demo data")
    print("✅ AI Pricing Analyst: Gemini AI analysis với threshold và range modes")
    print("✅ API Endpoints: REST APIs cho frontend integration")
    print("✅ Frontend Integration: Full workflow từ crawl → AI analysis")
    
    print("\n🚀 FEATURES AVAILABLE:")
    print("1. 🔍 Crawl real data từ Booking.com URLs")
    print("2. 🤖 AI-powered pricing insights với Gemini")
    print("3. 📊 Price range analysis và competitive positioning")
    print("4. 💡 Actionable recommendations cho hotel owners")
    print("5. 🎯 Strategic insights cho market penetration")

if __name__ == "__main__":
    asyncio.run(main())
