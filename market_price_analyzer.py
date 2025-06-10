"""
Market Price Analyzer - Phân tích giá thị trường từ Booking.com
Sử dụng crawl4ai để thu thập dữ liệu giá cả từ các nền tảng booking
"""

import asyncio
import json
import re
import statistics
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import pandas as pd

try:
    from crawl4ai import AsyncWebCrawler
    CRAWL4AI_AVAILABLE = True
except ImportError:
    try:
        from crawl4ai import WebCrawler, BrowserConfig, CrawlerRunConfig
        CRAWL4AI_AVAILABLE = True
    except ImportError:
        CRAWL4AI_AVAILABLE = False
        print("WARNING: crawl4ai not available - Market Price Analyzer will use fallback mode")

try:
    import google.generativeai as genai
    GENAI_AVAILABLE = True
except ImportError:
    GENAI_AVAILABLE = False

import requests
from bs4 import BeautifulSoup
import time
import random


class MarketPriceAnalyzer:
    """Phân tích giá thị trường từ các platform booking"""
    
    def __init__(self, google_api_key: Optional[str] = None):
        self.google_api_key = google_api_key
        self.crawler = None
        self.results_cache = {}
        
        if GENAI_AVAILABLE and google_api_key:
            genai.configure(api_key=google_api_key)
        
    async def initialize_crawler(self):
        """Khởi tạo crawler với cấu hình tối ưu"""
        if not CRAWL4AI_AVAILABLE:
            print("ERROR: crawl4ai không khả dụng")
            return False
            
        try:
            # Sử dụng AsyncWebCrawler cho version mới
            self.crawler = AsyncWebCrawler(
                headless=True,
                browser_type="chromium",
                verbose=True
            )
            await self.crawler.astart()
            print("SUCCESS: Crawler khởi tạo thành công")
            return True
            
        except Exception as e:
            print(f"ERROR: Lỗi khởi tạo crawler: {e}")
            return False
    
    async def crawl_booking_prices(self, booking_url: str, max_properties: int = 15) -> Dict:
        """
        Crawl giá từ Booking.com với URL cụ thể
        
        Args:
            booking_url: URL tìm kiếm Booking.com
            max_properties: Số lượng property tối đa cần crawl
            
        Returns:
            Dict chứa thông tin properties và phân tích giá
        """
        print(f"🔍 Bắt đầu crawl giá từ Booking.com (max: {max_properties} properties)")
        
        if not self.crawler:
            success = await self.initialize_crawler()
            if not success:
                return await self._fallback_crawl_booking(booking_url, max_properties)
        
        try:
            # Thực hiện crawl với API mới
            result = await self.crawler.arun(
                url=booking_url,
                word_count_threshold=50,
                page_timeout=30000,
                delay_before_return_html=3.0
            )
            
            if result.success:
                print("SUCCESS: Crawl thành công, đang xử lý dữ liệu...")
                return await self._process_crawl_result(result, max_properties)
            else:
                print(f"ERROR: Crawl thất bại: {result.error}")
                return await self._fallback_crawl_booking(booking_url, max_properties)
                
        except Exception as e:
            print(f"ERROR: Lỗi trong quá trình crawl: {e}")
            return await self._fallback_crawl_booking(booking_url, max_properties)
    
    async def _process_crawl_result(self, result, max_properties: int) -> Dict:
        """Xử lý kết quả crawl và trích xuất dữ liệu giá"""
        try:
            # Parse HTML trực tiếp vì không dùng LLM extraction
            properties = await self._parse_html_fallback(result.html)
            
            # Giới hạn số lượng properties
            properties = properties[:max_properties]
            
            # Làm sạch và phân tích dữ liệu
            cleaned_properties = self._clean_property_data(properties)
            analysis = self._analyze_prices(cleaned_properties)
            
            return {
                'success': True,
                'total_properties': len(cleaned_properties),
                'properties': cleaned_properties,
                'price_analysis': analysis,
                'crawl_timestamp': datetime.now().isoformat(),
                'source_url': result.url if hasattr(result, 'url') else 'booking.com'
            }
            
        except Exception as e:
            print(f"ERROR: Lỗi xử lý kết quả: {e}")
            return {
                'success': False,
                'error': str(e),
                'properties': [],
                'price_analysis': {}
            }
    
    async def _parse_html_fallback(self, html_content: str) -> List[Dict]:
        """Fallback parser sử dụng BeautifulSoup khi LLM extraction fail"""
        print("🔄 Sử dụng HTML parser fallback...")
        
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            properties = []
            
            # Tìm các property containers (cấu trúc có thể thay đổi)
            property_selectors = [
                '[data-testid="property-card"]',
                '.sr_property_block',
                '.c-sr-property-block',
                '[data-testid="property-card-container"]'
            ]
            
            property_elements = []
            for selector in property_selectors:
                elements = soup.select(selector)
                if elements:
                    property_elements = elements
                    print(f"✅ Tìm thấy {len(elements)} properties với selector: {selector}")
                    break
            
            for elem in property_elements[:15]:  # Giới hạn 15 properties
                try:
                    property_data = self._extract_property_from_element(elem)
                    if property_data:
                        properties.append(property_data)
                except Exception as e:
                    print(f"⚠️ Lỗi parse property: {e}")
                    continue
            
            print(f"✅ Đã parse {len(properties)} properties thành công")
            return properties
            
        except Exception as e:
            print(f"❌ Lỗi HTML parser: {e}")
            return []
    
    def _extract_property_from_element(self, elem) -> Optional[Dict]:
        """Trích xuất thông tin property từ HTML element"""
        try:
            # Tên property
            name_selectors = [
                '[data-testid="title"]',
                '.sr-hotel__name',
                '.fcab3ed991.a23c043802',
                'h3',
                '.property-card__name'
            ]
            name = self._find_text_by_selectors(elem, name_selectors, "Unknown Property")
            
            # Giá
            price_selectors = [
                '[data-testid="price-and-discounted-price"]',
                '.prco-valign-middle-helper',
                '.bui-price-display__value',
                '.sr-hotel__price',
                '[data-testid="price"]'
            ]
            price_text = self._find_text_by_selectors(elem, price_selectors, "0")
            
            # Rating
            rating_selectors = [
                '[data-testid="review-score"]',
                '.bui-review-score__badge',
                '.sr-hotel__review-score'
            ]
            rating = self._find_text_by_selectors(elem, rating_selectors, "N/A")
            
            # Location (có thể không có)
            location_selectors = [
                '[data-testid="address"]',
                '.sr-hotel__address',
                '.property-card__address'
            ]
            location = self._find_text_by_selectors(elem, location_selectors, "")
            
            return {
                'name': name.strip(),
                'price': price_text.strip(),
                'rating': rating.strip(),
                'location': location.strip(),
                'room_type': 'Standard'  # Default
            }
            
        except Exception as e:
            print(f"⚠️ Lỗi extract property: {e}")
            return None
    
    def _find_text_by_selectors(self, parent_elem, selectors: List[str], default: str = "") -> str:
        """Tìm text bằng danh sách selectors"""
        for selector in selectors:
            try:
                elem = parent_elem.select_one(selector)
                if elem and elem.get_text(strip=True):
                    return elem.get_text(strip=True)
            except:
                continue
        return default
    
    def _clean_property_data(self, properties: List[Dict]) -> List[Dict]:
        """Làm sạch và chuẩn hóa dữ liệu property"""
        cleaned = []
        
        for prop in properties:
            try:
                # Làm sạch giá
                price_vnd = self._extract_price_vnd(prop.get('price', ''))
                
                # Chỉ giữ lại properties có giá hợp lệ
                if price_vnd > 0:
                    cleaned_prop = {
                        'name': prop.get('name', 'Unknown')[:100],  # Giới hạn độ dài
                        'price_vnd': price_vnd,
                        'price_display': f"{price_vnd:,.0f}₫",
                        'rating': self._clean_rating(prop.get('rating', '')),
                        'location': prop.get('location', '')[:100],
                        'room_type': prop.get('room_type', 'Standard')
                    }
                    cleaned.append(cleaned_prop)
                    
            except Exception as e:
                print(f"⚠️ Lỗi clean property: {e}")
                continue
        
        print(f"✅ Đã làm sạch {len(cleaned)} properties")
        return cleaned
    
    def _extract_price_vnd(self, price_text: str) -> float:
        """Trích xuất và chuyển đổi giá về VND"""
        try:
            # Loại bỏ các ký tự không cần thiết
            price_clean = re.sub(r'[^\d.,]', '', price_text)
            
            # Tìm số
            numbers = re.findall(r'[\d.,]+', price_clean)
            if not numbers:
                return 0
            
            # Lấy số lớn nhất (thường là giá chính)
            max_number = max(numbers, key=len)
            
            # Xử lý dấu phẩy và chấm
            if ',' in max_number and '.' in max_number:
                # Format: 1,234.56 hoặc 1.234,56
                if max_number.rfind(',') > max_number.rfind('.'):
                    # Format: 1.234,56 (European)
                    max_number = max_number.replace('.', '').replace(',', '.')
                else:
                    # Format: 1,234.56 (US)
                    max_number = max_number.replace(',', '')
            elif ',' in max_number:
                # Chỉ có dấu phẩy - có thể là separator hoặc decimal
                if len(max_number.split(',')[-1]) <= 2:
                    # Có thể là decimal
                    max_number = max_number.replace(',', '.')
                else:
                    # Là separator
                    max_number = max_number.replace(',', '')
            
            price_float = float(max_number)
            
            # Detect currency và convert về VND
            if 'USD' in price_text.upper() or '$' in price_text:
                price_float *= 24000  # USD to VND approximation
            elif 'EUR' in price_text.upper() or '€' in price_text:
                price_float *= 26000  # EUR to VND approximation
            elif price_float < 1000:  # Có thể là USD
                price_float *= 24000
            
            return price_float
            
        except Exception as e:
            print(f"⚠️ Lỗi parse giá '{price_text}': {e}")
            return 0
    
    def _clean_rating(self, rating_text: str) -> str:
        """Làm sạch rating"""
        try:
            # Tìm số rating
            rating_match = re.search(r'(\d+\.?\d*)', rating_text)
            if rating_match:
                return rating_match.group(1)
            return "N/A"
        except:
            return "N/A"
    
    def _analyze_prices(self, properties: List[Dict]) -> Dict:
        """Phân tích giá cả và tạo insights"""
        if not properties:
            return {}
        
        prices = [prop['price_vnd'] for prop in properties if prop['price_vnd'] > 0]
        
        if not prices:
            return {}
        
        analysis = {
            'total_properties': len(properties),
            'price_count': len(prices),
            'min_price': min(prices),
            'max_price': max(prices),
            'avg_price': statistics.mean(prices),
            'median_price': statistics.median(prices),
            'price_std': statistics.stdev(prices) if len(prices) > 1 else 0,
        }
        
        # Phân loại giá
        analysis['price_ranges'] = self._categorize_prices(prices)
        
        # Insights
        analysis['insights'] = self._generate_insights(analysis, properties)
        
        return analysis
    
    def _categorize_prices(self, prices: List[float]) -> Dict:
        """Phân loại giá theo các tầng"""
        if not prices:
            return {}
        
        # Định nghĩa các tầng giá
        ranges = {
            'budget': (0, 500000),           # Dưới 500k
            'mid_range': (500000, 1000000),  # 500k - 1M
            'upscale': (1000000, 2000000),   # 1M - 2M
            'luxury': (2000000, float('inf')) # Trên 2M
        }
        
        categorized = {}
        for category, (min_price, max_price) in ranges.items():
            count = len([p for p in prices if min_price <= p < max_price])
            percentage = (count / len(prices)) * 100
            categorized[category] = {
                'count': count,
                'percentage': round(percentage, 1),
                'range': f"{min_price/1000:.0f}k - {max_price/1000:.0f}k" if max_price != float('inf') else f">{min_price/1000:.0f}k"
            }
        
        return categorized
    
    def _generate_insights(self, analysis: Dict, properties: List[Dict]) -> List[str]:
        """Tạo insights từ phân tích giá"""
        insights = []
        
        avg_price = analysis['avg_price']
        median_price = analysis['median_price']
        
        # Insight về giá trung bình
        insights.append(f"💰 Giá trung bình: {avg_price:,.0f}₫/đêm")
        insights.append(f"📊 Giá trung vị: {median_price:,.0f}₫/đêm")
        
        # So sánh giá
        if avg_price > median_price * 1.2:
            insights.append("📈 Có một số property giá cao kéo trung bình lên")
        elif avg_price < median_price * 0.8:
            insights.append("📉 Phần lớn property có giá thấp, ít property premium")
        
        # Phân tích theo tầng giá
        ranges = analysis.get('price_ranges', {})
        if ranges:
            dominant_range = max(ranges.items(), key=lambda x: x[1]['count'])
            insights.append(f"🎯 Tầng giá phổ biến nhất: {dominant_range[0]} ({dominant_range[1]['percentage']}%)")
        
        # Insight về độ biến động
        if analysis.get('price_std', 0) > avg_price * 0.5:
            insights.append("⚡ Giá có độ biến động cao - thị trường đa dạng")
        else:
            insights.append("🎯 Giá tương đối ổn định - thị trường đồng nhất")
        
        return insights

    async def _fallback_crawl_booking(self, booking_url: str, max_properties: int) -> Dict:
        """Fallback method sử dụng requests + BeautifulSoup"""
        print("🔄 Sử dụng fallback crawl method...")
        
        try:
            # Headers để tránh bị block
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'vi-VN,vi;q=0.9,en;q=0.8',
                'Accept-Encoding': 'gzip, deflate, br',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
            }
            
            # Random delay để tránh rate limiting
            await asyncio.sleep(random.uniform(1, 3))
            
            response = requests.get(booking_url, headers=headers, timeout=30)
            response.raise_for_status()
            
            # Parse HTML
            properties = await self._parse_html_fallback(response.text)
            
            # Làm sạch và phân tích
            cleaned_properties = self._clean_property_data(properties)
            analysis = self._analyze_prices(cleaned_properties)
            
            return {
                'success': True,
                'total_properties': len(cleaned_properties),
                'properties': cleaned_properties[:max_properties],
                'price_analysis': analysis,
                'crawl_timestamp': datetime.now().isoformat(),
                'source_url': booking_url,
                'method': 'fallback'
            }
            
        except Exception as e:
            print(f"❌ Fallback crawl failed: {e}")
            return {
                'success': False,
                'error': str(e),
                'properties': [],
                'price_analysis': {},
                'method': 'fallback'
            }
    
    async def cleanup(self):
        """Dọn dẹp resources"""
        if self.crawler:
            try:
                await self.crawler.aclose()
            except:
                pass

# Utility functions
async def analyze_market_prices(booking_url: str, google_api_key: Optional[str] = None, max_properties: int = 15) -> Dict:
    """
    Hàm chính để phân tích giá thị trường
    
    Args:
        booking_url: URL Booking.com để crawl
        google_api_key: API key cho Gemini (optional)
        max_properties: Số lượng property tối đa
        
    Returns:
        Dict chứa kết quả phân tích
    """
    analyzer = MarketPriceAnalyzer(google_api_key)
    
    try:
        result = await analyzer.crawl_booking_prices(booking_url, max_properties)
        return result
    finally:
        await analyzer.cleanup()

def format_price_analysis_for_display(analysis_result: Dict) -> Dict:
    """Format kết quả phân tích để hiển thị trên frontend"""
    if not analysis_result.get('success'):
        return {
            'error': analysis_result.get('error', 'Unknown error'),
            'success': False
        }
    
    properties = analysis_result.get('properties', [])
    price_analysis = analysis_result.get('price_analysis', {})
    
    return {
        'success': True,
        'summary': {
            'total_found': len(properties),
            'avg_price': price_analysis.get('avg_price', 0),
            'min_price': price_analysis.get('min_price', 0),
            'max_price': price_analysis.get('max_price', 0),
            'median_price': price_analysis.get('median_price', 0),
        },
        'properties': properties,
        'insights': price_analysis.get('insights', []),
        'price_ranges': price_analysis.get('price_ranges', {}),
        'timestamp': analysis_result.get('crawl_timestamp'),
        'source_url': analysis_result.get('source_url')
    }
