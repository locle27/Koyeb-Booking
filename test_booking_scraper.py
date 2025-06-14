#!/usr/bin/env python3
"""
Test script for Booking.com apartment scraper
Uses the functions added to logic.py
"""

import os
import sys

# Add current directory to path to import logic
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from logic import scrape_booking_apartments, format_apartments_display

def main():
    """
    Test the booking scraper with your provided URL
    """
    print("🏠 HANOI APARTMENT MARKET ANALYSIS")
    print("=" * 50)
    
    # Your original URL (with price filter under 500,000 VND)
    url = "https://www.booking.com/searchresults.vi.html?label=en-vn-booking-desktop-WeZI9wwaGAAqHXeGoKbrHQS652828997899%3Apl%3Ata%3Ap1%3Ap2%3Aac%3Aap%3Aneg%3Afi%3Atikwd-65526620%3Alp1028580%3Ali%3Adec%3Adm&sid=589cbe47166cb7b3ff3f409ac248f19e&aid=2311236&ss=Ha%CC%80+N%C3%B4%CC%A3i&ssne=Ha%CC%80+N%C3%B4%CC%A3i&ssne_untouched=Ha%CC%80+N%C3%B4%CC%A3i&highlighted_hotels=10862832&lang=vi&src=hotel&dest_id=-3714993&dest_type=city&group_adults=2&no_rooms=1&group_children=0&nflt=di%3D2096%3Bprice%3DVND-min-500000-1"
    
    # Run the scraper
    print("🚀 Starting apartment data extraction...")
    apartments_data = scrape_booking_apartments(url)
    
    # Format and display results
    formatted_output = format_apartments_display(apartments_data)
    print(formatted_output)
    
    # Save results to file
    if "error" not in apartments_data:
        try:
            with open('hanoi_apartments_analysis.txt', 'w', encoding='utf-8') as f:
                f.write(formatted_output)
                f.write("\n\n" + "="*70 + "\n")
                f.write("RAW DATA (JSON):\n")
                f.write("="*70 + "\n")
                import json
                f.write(json.dumps(apartments_data, indent=2, ensure_ascii=False))
            
            print(f"\n💾 Results saved to hanoi_apartments_analysis.txt")
            print(f"📊 Found {len(apartments_data.get('apartments', []))} apartment listings")
            
        except Exception as e:
            print(f"⚠️ Could not save to file: {e}")
    
    # Show market summary
    if "apartments" in apartments_data:
        apartments = apartments_data["apartments"]
        if apartments:
            print(f"\n📈 MARKET SUMMARY:")
            print(f"   Total properties: {len(apartments)}")
            
            # Try to extract price ranges (basic analysis)
            prices = []
            for apt in apartments:
                price_str = apt.get('price', '').replace(',', '').replace('VND', '').replace('₫', '')
                # Extract numbers from price string
                import re
                numbers = re.findall(r'\d+', price_str)
                if numbers:
                    prices.append(int(numbers[0]))
            
            if prices:
                print(f"   Price range: {min(prices):,} - {max(prices):,} VND")
                print(f"   Average price: {sum(prices)//len(prices):,} VND")

if __name__ == "__main__":
    main()