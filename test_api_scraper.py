#!/usr/bin/env python3
"""
Test the apartment scraper API endpoint
"""

import requests
import json
import time

def test_apartment_scraper():
    """Test the apartment scraper API"""
    
    # Your original Booking.com URL
    url = "https://www.booking.com/searchresults.vi.html?label=en-vn-booking-desktop-WeZI9wwaGAAqHXeGoKbrHQS652828997899%3Apl%3Ata%3Ap1%3Ap2%3Aac%3Aap%3Aneg%3Afi%3Atikwd-65526620%3Alp1028580%3Ali%3Adec%3Adm&sid=589cbe47166cb7b3ff3f409ac248f19e&aid=2311236&ss=Ha%CC%80+N%C3%B4%CC%A3i&ssne=Ha%CC%80+N%C3%B4%CC%A3i&ssne_untouched=Ha%CC%80+N%C3%B4%CC%A3i&highlighted_hotels=10862832&lang=vi&src=hotel&dest_id=-3714993&dest_type=city&group_adults=2&no_rooms=1&group_children=0&nflt=di%3D2096%3Bprice%3DVND-min-500000-1"
    
    # Test API endpoint (assuming Flask app is running on localhost:5000)
    api_url = "http://localhost:5000/api/scrape_apartments"
    
    print("🏠 TESTING APARTMENT SCRAPER API")
    print("=" * 50)
    print(f"📡 API URL: {api_url}")
    print(f"🔗 Target URL: {url[:100]}...")
    print("\n🚀 Sending request...")
    
    try:
        # Send POST request with the URL
        response = requests.post(
            api_url,
            json={"url": url},
            timeout=60  # Give it time to process
        )
        
        print(f"📊 Response Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            
            if data.get("success"):
                print("✅ SUCCESS! Data extracted:")
                print("\n📋 FORMATTED DISPLAY:")
                print(data.get("formatted_display", "No display data"))
                
                print("\n📈 MARKET SUMMARY:")
                summary = data.get("market_summary", {})
                if summary:
                    print(f"   Total Properties: {summary.get('total_properties', 'N/A')}")
                    print(f"   Price Range: {summary.get('price_range_formatted', 'N/A')}")
                    print(f"   Average Price: {summary.get('average_price_formatted', 'N/A')}")
                
                # Save full data to file
                apartments = data.get("data", {}).get("apartments", [])
                if apartments:
                    with open('apartment_analysis_result.json', 'w', encoding='utf-8') as f:
                        json.dump(data, f, indent=2, ensure_ascii=False)
                    print(f"\n💾 Full data saved to apartment_analysis_result.json")
                    print(f"📊 Total apartments found: {len(apartments)}")
                
            else:
                print(f"❌ API Error: {data.get('error', 'Unknown error')}")
        else:
            print(f"❌ HTTP Error: {response.status_code}")
            try:
                error_data = response.json()
                print(f"Error details: {error_data}")
            except:
                print(f"Error text: {response.text}")
                
    except requests.exceptions.ConnectionError:
        print("❌ Connection Error: Is the Flask app running?")
        print("💡 Start the app with: python app.py")
    except requests.exceptions.Timeout:
        print("⏰ Timeout Error: Request took too long")
    except Exception as e:
        print(f"❌ Unexpected Error: {e}")

if __name__ == "__main__":
    test_apartment_scraper()