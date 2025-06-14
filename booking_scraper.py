#!/usr/bin/env python3
"""
Booking.com Apartment Data Scraper using Gemini AI
Extracts apartment listings with name, price, address, and star rating
"""

import requests
import json
import os
import google.generativeai as genai
from typing import List, Dict, Any
import time

def get_booking_data(url: str) -> str:
    """
    Fetch content from Booking.com URL
    """
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'vi-VN,vi;q=0.8,en-US;q=0.5,en;q=0.3',
        'Accept-Encoding': 'gzip, deflate',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        return response.text
    except requests.RequestException as e:
        print(f"❌ Error fetching data: {e}")
        return ""

def extract_apartments_with_gemini(html_content: str) -> List[Dict[str, Any]]:
    """
    Use Gemini AI to extract apartment data from HTML content
    """
    api_key = os.getenv('GOOGLE_API_KEY')
    if not api_key:
        print("❌ GOOGLE_API_KEY not found in environment variables")
        return []
    
    # Configure Gemini
    genai.configure(api_key=api_key)
    
    # Use Gemini 2.5 Flash Preview (same as your existing system)
    model = genai.GenerativeModel('gemini-2.5-flash-preview-05-20')
    
    prompt = """
    Analyze this Booking.com search results HTML and extract apartment/hotel listings data.
    
    For each property listing, extract:
    1. Property Name (apartment/hotel name)
    2. Price per night (in VND, convert if needed)
    3. Address/Location (district, area)
    4. Star Rating (if available)
    5. Property Type (apartment, hotel, etc.)
    
    Focus on properties under 500,000 VND per night.
    Extract up to 20-30 listings if available.
    
    Return the data in this JSON format:
    {
        "apartments": [
            {
                "name": "Property Name",
                "price": "Price in VND",
                "address": "Address/Location",
                "star_rating": "Rating",
                "property_type": "apartment/hotel"
            }
        ]
    }
    
    If you can't find specific data, use "N/A" for that field.
    """
    
    try:
        # Truncate HTML if too long to avoid token limits
        if len(html_content) > 50000:
            html_content = html_content[:50000] + "..."
            
        response = model.generate_content([prompt, html_content])
        
        # Try to parse JSON response
        response_text = response.text.strip()
        if response_text.startswith('```json'):
            response_text = response_text[7:-3]
        elif response_text.startswith('```'):
            response_text = response_text[3:-3]
            
        try:
            data = json.loads(response_text)
            return data.get('apartments', [])
        except json.JSONDecodeError:
            # If JSON parsing fails, return raw text
            print("⚠️ Could not parse JSON, returning raw response:")
            print(response_text)
            return []
            
    except Exception as e:
        print(f"❌ Gemini API error: {e}")
        return []

def format_apartment_list(apartments: List[Dict[str, Any]]) -> str:
    """
    Format apartment list for display
    """
    if not apartments:
        return "❌ No apartments found"
    
    output = f"\n🏠 HANOI APARTMENT LISTINGS (Under 500,000 VND/night)\n"
    output += "=" * 70 + "\n\n"
    
    for i, apt in enumerate(apartments, 1):
        output += f"{i:2d}. {apt.get('name', 'N/A')}\n"
        output += f"    💰 Price: {apt.get('price', 'N/A')}\n"
        output += f"    📍 Address: {apt.get('address', 'N/A')}\n"
        output += f"    ⭐ Rating: {apt.get('star_rating', 'N/A')}\n"
        output += f"    🏢 Type: {apt.get('property_type', 'N/A')}\n"
        output += "-" * 50 + "\n"
    
    output += f"\n📊 Total listings found: {len(apartments)}\n"
    return output

def main():
    """
    Main function to scrape and process Booking.com data
    """
    # The URL you provided
    url = "https://www.booking.com/searchresults.vi.html?label=en-vn-booking-desktop-WeZI9wwaGAAqHXeGoKbrHQS652828997899%3Apl%3Ata%3Ap1%3Ap2%3Aac%3Aap%3Aneg%3Afi%3Atikwd-65526620%3Alp1028580%3Ali%3Adec%3Adm&sid=589cbe47166cb7b3ff3f409ac248f19e&aid=2311236&ss=Ha%CC%80+N%C3%B4%CC%A3i&ssne=Ha%CC%80+N%C3%B4%CC%A3i&ssne_untouched=Ha%CC%80+N%C3%B4%CC%A3i&highlighted_hotels=10862832&lang=vi&src=hotel&dest_id=-3714993&dest_type=city&group_adults=2&no_rooms=1&group_children=0&nflt=di%3D2096%3Bprice%3DVND-min-500000-1"
    
    print("🔍 Fetching Booking.com data...")
    html_content = get_booking_data(url)
    
    if not html_content:
        print("❌ Failed to fetch data from Booking.com")
        return
    
    print("🧠 Processing with Gemini AI...")
    apartments = extract_apartments_with_gemini(html_content)
    
    # Display results
    result = format_apartment_list(apartments)
    print(result)
    
    # Save to file
    with open('hanoi_apartments.txt', 'w', encoding='utf-8') as f:
        f.write(result)
    
    print(f"💾 Results saved to hanoi_apartments.txt")

if __name__ == "__main__":
    main()