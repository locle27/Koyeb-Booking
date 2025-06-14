#!/usr/bin/env python3
"""
Simple apartment analyzer using system commands and text processing
No external Python dependencies required
"""

import subprocess
import os
import json
import re
import tempfile

def fetch_booking_page(url):
    """
    Fetch the booking page using curl
    """
    print("🔍 Fetching Booking.com page...")
    
    # Create a temporary file for the HTML content
    with tempfile.NamedTemporaryFile(mode='w+', suffix='.html', delete=False) as f:
        temp_file = f.name
    
    try:
        # Use curl to fetch the page with proper headers
        curl_command = [
            'curl', '-s', '-L',
            '-H', 'User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            '-H', 'Accept: text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            '-H', 'Accept-Language: vi-VN,vi;q=0.8,en-US;q=0.5,en;q=0.3',
            '-H', 'Connection: keep-alive',
            '--connect-timeout', '30',
            '--max-time', '60',
            '-o', temp_file,
            url
        ]
        
        result = subprocess.run(curl_command, capture_output=True, text=True)
        
        if result.returncode == 0:
            # Read the downloaded content
            with open(temp_file, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            return content
        else:
            print(f"❌ Curl error: {result.stderr}")
            return None
            
    except Exception as e:
        print(f"❌ Error fetching page: {e}")
        return None
    finally:
        # Clean up temp file
        try:
            os.unlink(temp_file)
        except:
            pass

def extract_basic_info(html_content):
    """
    Extract basic apartment info using regex (no external dependencies)
    """
    print("🔍 Extracting apartment information...")
    
    apartments = []
    
    try:
        # Look for property cards in Booking.com HTML
        # These patterns are based on common Booking.com HTML structure
        
        # Pattern 1: Look for property names in title attributes or data attributes
        name_patterns = [
            r'data-testid="title"[^>]*>([^<]+)<',
            r'aria-label="([^"]*)"[^>]*data-testid="title"',
            r'<h3[^>]*>([^<]+)</h3>',
            r'title="([^"]*)"[^>]*class="[^"]*property[^"]*"'
        ]
        
        # Pattern 2: Look for prices in VND
        price_patterns = [
            r'VND\s*([\d,]+)',
            r'₫\s*([\d,]+)',
            r'(\d{3,})\s*VND',
            r'(\d{3,})\s*₫'
        ]
        
        # Pattern 3: Look for ratings
        rating_patterns = [
            r'aria-label="Rated\s+([0-9.]+)"',
            r'(\d\.\d)\s*(?:out\s*of|\/)\s*\d+',
            r'rating.*?(\d\.\d)'
        ]
        
        # Extract property names
        all_names = []
        for pattern in name_patterns:
            matches = re.findall(pattern, html_content, re.IGNORECASE)
            all_names.extend(matches)
        
        # Extract prices
        all_prices = []
        for pattern in price_patterns:
            matches = re.findall(pattern, html_content, re.IGNORECASE)
            all_prices.extend(matches)
        
        # Extract ratings
        all_ratings = []
        for pattern in rating_patterns:
            matches = re.findall(pattern, html_content, re.IGNORECASE)
            all_ratings.extend(matches)
        
        # Clean and filter names (remove duplicates, filter hotel-like names)
        clean_names = []
        for name in all_names:
            name = name.strip()
            if len(name) > 5 and len(name) < 100:  # Reasonable length
                if any(keyword in name.lower() for keyword in ['hotel', 'apartment', 'hostel', 'house', 'room', 'home']):
                    clean_names.append(name)
        
        # Remove duplicates while preserving order
        seen = set()
        unique_names = []
        for name in clean_names:
            if name not in seen:
                seen.add(name)
                unique_names.append(name)
        
        # Clean prices (remove commas, convert to int)
        clean_prices = []
        for price in all_prices:
            try:
                price_num = int(price.replace(',', ''))
                if 50000 <= price_num <= 1000000:  # Reasonable price range
                    clean_prices.append(price_num)
            except:
                continue
        
        # Clean ratings
        clean_ratings = []
        for rating in all_ratings:
            try:
                rating_num = float(rating)
                if 1.0 <= rating_num <= 5.0:  # Valid rating range
                    clean_ratings.append(rating_num)
            except:
                continue
        
        # Combine data (use available data, pad with N/A)
        max_items = max(len(unique_names), len(clean_prices), len(clean_ratings))
        
        for i in range(min(max_items, 25)):  # Limit to 25 items
            name = unique_names[i] if i < len(unique_names) else f"Property {i+1}"
            price = clean_prices[i] if i < len(clean_prices) else None
            rating = clean_ratings[i] if i < len(clean_ratings) else None
            
            apartment = {
                "name": name,
                "price": f"{price:,} VND" if price else "N/A",
                "price_num": price,
                "address": "Hanoi, Vietnam",  # Default since we're searching Hanoi
                "star_rating": str(rating) if rating else "N/A",
                "property_type": "Hotel/Apartment"
            }
            apartments.append(apartment)
        
        print(f"✅ Extracted {len(apartments)} properties")
        return apartments
        
    except Exception as e:
        print(f"❌ Error extracting data: {e}")
        return []

def format_results(apartments):
    """Format results for display"""
    if not apartments:
        return "❌ No apartments found"
    
    output = f"\n🏠 HANOI APARTMENT LISTINGS (Price Analysis)\n"
    output += "=" * 70 + "\n\n"
    
    for i, apt in enumerate(apartments, 1):
        output += f"{i:2d}. {apt['name']}\n"
        output += f"    💰 Price: {apt['price']}\n"
        output += f"    📍 Address: {apt['address']}\n"
        output += f"    ⭐ Rating: {apt['star_rating']}\n"
        output += f"    🏢 Type: {apt['property_type']}\n"
        output += "-" * 50 + "\n"
    
    # Calculate price statistics
    prices = [apt['price_num'] for apt in apartments if apt['price_num']]
    if prices:
        output += f"\n📊 PRICE ANALYSIS:\n"
        output += f"   Total properties: {len(apartments)}\n"
        output += f"   Price range: {min(prices):,} - {max(prices):,} VND\n"
        output += f"   Average price: {sum(prices)//len(prices):,} VND\n"
        output += f"   Properties under 500k: {len([p for p in prices if p < 500000])}\n"
    
    return output

def main():
    """Main function"""
    print("🏠 HANOI APARTMENT MARKET ANALYSIS")
    print("Using Simple Text Processing (No External Dependencies)")
    print("=" * 60)
    
    # Your Booking.com URL
    url = "https://www.booking.com/searchresults.vi.html?label=en-vn-booking-desktop-WeZI9wwaGAAqHXeGoKbrHQS652828997899%3Apl%3Ata%3Ap1%3Ap2%3Aac%3Aap%3Aneg%3Afi%3Atikwd-65526620%3Alp1028580%3Ali%3Adec%3Adm&sid=589cbe47166cb7b3ff3f409ac248f19e&aid=2311236&ss=Ha%CC%80+N%C3%B4%CC%A3i&ssne=Ha%CC%80+N%C3%B4%CC%A3i&ssne_untouched=Ha%CC%80+N%C3%B4%CC%A3i&highlighted_hotels=10862832&lang=vi&src=hotel&dest_id=-3714993&dest_type=city&group_adults=2&no_rooms=1&group_children=0&nflt=di%3D2096%3Bprice%3DVND-min-500000-1"
    
    # Fetch the page
    html_content = fetch_booking_page(url)
    
    if not html_content:
        print("❌ Failed to fetch page content")
        return
    
    print(f"✅ Downloaded {len(html_content)} characters of HTML")
    
    # Extract apartment data
    apartments = extract_basic_info(html_content)
    
    # Format and display results
    result = format_results(apartments)
    print(result)
    
    # Save to file
    try:
        with open('hanoi_apartments_simple.txt', 'w', encoding='utf-8') as f:
            f.write(result)
        
        # Also save raw data as JSON
        with open('hanoi_apartments_simple.json', 'w', encoding='utf-8') as f:
            json.dump(apartments, f, indent=2, ensure_ascii=False)
        
        print(f"\n💾 Results saved to:")
        print(f"   📄 hanoi_apartments_simple.txt (formatted)")
        print(f"   📄 hanoi_apartments_simple.json (raw data)")
    except Exception as e:
        print(f"⚠️ Could not save files: {e}")

if __name__ == "__main__":
    main()