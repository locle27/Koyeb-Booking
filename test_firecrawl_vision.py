#!/usr/bin/env python3
"""
Test script for Firecrawl + Gemini Vision Market Intelligence
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add the current directory to the path
sys.path.append(os.path.dirname(__file__))

try:
    from market_intelligence_complete import HotelMarketIntelligence
    
    print("🧪 Testing Firecrawl + Gemini Vision Market Intelligence System")
    print("=" * 60)
    
    # Initialize the market intelligence system
    market_intel = HotelMarketIntelligence()
    
    # Test the firecrawl vision source specifically
    print("\n📸 Testing Firecrawl + Gemini Vision data source...")
    result = market_intel._firecrawl_vision_source("Hanoi", 500000)
    
    print(f"\n📊 Results:")
    print(f"   Found {len(result.get('apartments', []))} properties")
    print(f"   Data source: {result.get('method', 'unknown')}")
    print(f"   Search URL: {result.get('search_url', 'N/A')}")
    
    if result.get('apartments'):
        print(f"\n🏨 Sample property:")
        sample = result['apartments'][0]
        for key, value in sample.items():
            print(f"   {key}: {value}")
    
    print("\n✅ Test completed!")
    
except Exception as e:
    print(f"❌ Test failed: {e}")
    import traceback
    traceback.print_exc()