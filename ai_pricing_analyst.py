"""
AI Pricing Analyst - Sử dụng Gemini AI để phân tích thị trường giá thông minh
Tập trung vào segment dưới 500k và đưa ra strategic insights
"""

import google.generativeai as genai
import json
from typing import Dict, List, Optional
from datetime import datetime

class AIPricingAnalyst:
    """AI-powered pricing analyst sử dụng Gemini API"""
    
    def __init__(self, google_api_key: Optional[str] = None):
        self.google_api_key = google_api_key
        if google_api_key:
            genai.configure(api_key=google_api_key)
    
    def analyze_price_range_segment(self, properties: List[Dict], min_price: int = 0, max_price: int = 500000) -> Dict:
        """
        Phân tích segment giá trong khoảng min-max với AI
        
        Args:
            properties: Danh sách properties từ market analysis
            min_price: Giá tối thiểu (VND)
            max_price: Giá tối đa (VND)
            
        Returns:
            Dict chứa AI insights và recommendations cho price range
        """
        try:
            if not self.google_api_key:
                return self._fallback_range_analysis(properties, min_price, max_price)
            
            # Filter properties trong price range
            range_properties = [
                prop for prop in properties 
                if min_price <= prop.get('price_vnd', 0) <= max_price
            ]
            
            if not range_properties:
                return {
                    'success': False,
                    'message': f'Không có property nào trong khoảng {min_price:,}₫ - {max_price:,}₫',
                    'ai_insights': [],
                    'recommendations': []
                }
            
            # Chuẩn bị data context cho AI với price range
            analysis_context = self._prepare_range_ai_context(range_properties, min_price, max_price, properties)
            
            # Gọi Gemini AI với range-specific prompt
            ai_response = self._call_range_gemini_ai(analysis_context)
            
            # Parse và format response
            formatted_response = self._format_range_ai_response(ai_response, range_properties, min_price, max_price)
            
            return formatted_response
            
        except Exception as e:
            print(f"AI Price Range Analysis error: {e}")
            return self._fallback_range_analysis(properties, min_price, max_price)
        """
        Phân tích segment giá dưới ngưỡng cụ thể với AI
        
        Args:
            properties: Danh sách properties từ market analysis
            price_threshold: Ngưỡng giá (default 500k)
            
        Returns:
            Dict chứa AI insights và recommendations
        """
        try:
            if not self.google_api_key:
                return self._fallback_analysis(properties, price_threshold)
            
            # Filter properties dưới ngưỡng giá
            budget_properties = [
                prop for prop in properties 
                if prop.get('price_vnd', 0) <= price_threshold
            ]
            
            if not budget_properties:
                return {
                    'success': False,
                    'message': f'Không có property nào dưới {price_threshold:,}₫',
                    'ai_insights': [],
                    'recommendations': []
                }
            
            # Chuẩn bị data context cho AI
            analysis_context = self._prepare_ai_context(budget_properties, price_threshold)
            
            # Gọi Gemini AI
            ai_response = self._call_gemini_ai(analysis_context)
            
            # Parse và format response
            formatted_response = self._format_ai_response(ai_response, budget_properties, price_threshold)
            
            return formatted_response
            
        except Exception as e:
            print(f"AI Pricing Analysis error: {e}")
            return self._fallback_analysis(properties, price_threshold)
    
    def _prepare_ai_context(self, budget_properties: List[Dict], price_threshold: int) -> str:
        """Chuẩn bị context data cho AI analysis"""
        
        # Tính toán basic statistics
        prices = [prop['price_vnd'] for prop in budget_properties]
        locations = [prop.get('location', 'N/A') for prop in budget_properties]
        ratings = [float(prop.get('rating', '0')) for prop in budget_properties if prop.get('rating', '0') != 'N/A']
        
        # Market context
        avg_price = sum(prices) / len(prices) if prices else 0
        min_price = min(prices) if prices else 0
        max_price = max(prices) if prices else 0
        avg_rating = sum(ratings) / len(ratings) if ratings else 0
        
        # Location analysis
        location_counts = {}
        for loc in locations:
            location_counts[loc] = location_counts.get(loc, 0) + 1
        
        # Properties detail for AI
        properties_summary = []
        for prop in budget_properties[:10]:  # Top 10 để tránh quá dài
            properties_summary.append({
                'name': prop.get('name', 'N/A'),
                'price': prop.get('price_vnd', 0),
                'rating': prop.get('rating', 'N/A'),
                'location': prop.get('location', 'N/A')
            })
        
        context = f"""
MARKET DATA ANALYSIS REQUEST - HANOI OLD QUARTER BUDGET SEGMENT

ANALYSIS FOCUS: Properties under {price_threshold:,} VND per night
DATE: {datetime.now().strftime('%Y-%m-%d')}
LOCATION: Hanoi Old Quarter (Khu Phố Cổ)

BUDGET SEGMENT STATISTICS:
- Total Properties Analyzed: {len(budget_properties)}
- Price Range: {min_price:,}₫ - {max_price:,}₫ 
- Average Price: {avg_price:,.0f}₫
- Average Rating: {avg_rating:.1f}/10
- Price Threshold: Under {price_threshold:,}₫

LOCATION DISTRIBUTION:
{json.dumps(location_counts, indent=2, ensure_ascii=False)}

SAMPLE PROPERTIES:
{json.dumps(properties_summary, indent=2, ensure_ascii=False)}

COMPETITIVE LANDSCAPE CONTEXT:
- This is Hanoi's prime tourist area (Old Quarter)
- Target customers: Budget travelers, backpackers, young tourists
- High competition with hundreds of hostels/budget hotels
- Location advantage: Walking distance to major attractions
- Price sensitivity: Very high among target demographic

BUSINESS CONTEXT:
- Hotel: 118 Hang Bac Hostel
- Current positioning: Budget accommodation in premium location
- Need: Strategic pricing insights for competitive advantage
- Goal: Optimize pricing while maintaining occupancy
"""
        
        return context
    
    def _call_gemini_ai(self, context: str) -> str:
        """Gọi Gemini AI với pricing analysis prompt"""
        
        prompt = f"""
You are an expert hospitality pricing analyst specializing in budget accommodation in Southeast Asia. Analyze the provided market data and provide strategic insights.

{context}

ANALYSIS REQUIREMENTS:
1. COMPETITIVE POSITIONING: How does this price segment position against the market?
2. PRICING OPPORTUNITIES: Where are the gaps and opportunities?
3. CUSTOMER VALUE ANALYSIS: What do customers get at this price point?
4. STRATEGIC RECOMMENDATIONS: Actionable pricing strategies
5. RISK ASSESSMENT: What are the pricing risks and how to mitigate?

SPECIFIC FOCUS AREAS:
- Price elasticity in this segment
- Location premium analysis (Old Quarter advantage)
- Rating vs price correlation insights
- Competitive differentiation opportunities
- Revenue optimization strategies

Please provide your analysis in the following JSON format:

{{
    "market_overview": {{
        "segment_health": "Brief assessment of the under-500k segment health",
        "competition_level": "Assessment of competition intensity",
        "customer_behavior": "Insights about budget traveler behavior"
    }},
    "competitive_analysis": {{
        "price_positioning": "How our target price compares to market",
        "location_advantage": "Analysis of Old Quarter location premium",
        "rating_insights": "What ratings tell us about quality expectations"
    }},
    "pricing_opportunities": [
        {{
            "opportunity": "Specific pricing opportunity",
            "rationale": "Why this opportunity exists",
            "implementation": "How to implement this strategy",
            "expected_impact": "Expected business impact"
        }}
    ],
    "strategic_recommendations": [
        {{
            "strategy": "Strategic recommendation",
            "priority": "High/Medium/Low",
            "timeframe": "Implementation timeframe",
            "success_metrics": "How to measure success"
        }}
    ],
    "risk_analysis": {{
        "pricing_risks": ["List of potential pricing risks"],
        "mitigation_strategies": ["How to mitigate each risk"],
        "market_threats": ["External market threats to consider"]
    }},
    "actionable_insights": [
        "Immediate actionable insight 1",
        "Immediate actionable insight 2",
        "Immediate actionable insight 3"
    ],
    "ai_confidence": "High/Medium/Low confidence in this analysis"
}}

Provide deep, strategic insights that a hotel owner can immediately act upon.
"""
        
        try:
            model = genai.GenerativeModel('gemini-2.0-flash-exp')
            response = model.generate_content(prompt)
            return response.text.strip()
        except Exception as e:
            print(f"Gemini AI call error: {e}")
            return self._generate_fallback_ai_response()
    
    def _format_ai_response(self, ai_response: str, budget_properties: List[Dict], price_threshold: int) -> Dict:
        """Format AI response thành structure phù hợp cho frontend"""
        
        try:
            # Extract JSON từ AI response
            json_start = ai_response.find('{')
            json_end = ai_response.rfind('}') + 1
            
            if json_start >= 0 and json_end > json_start:
                json_str = ai_response[json_start:json_end]
                ai_analysis = json.loads(json_str)
            else:
                raise ValueError("No valid JSON found in AI response")
            
            # Tính toán thêm statistics
            prices = [prop['price_vnd'] for prop in budget_properties]
            price_analysis = {
                'total_properties': len(budget_properties),
                'avg_price': sum(prices) / len(prices),
                'min_price': min(prices),
                'max_price': max(prices),
                'price_threshold': price_threshold,
                'market_share': len(budget_properties) / max(1, len(budget_properties)) * 100  # Sẽ update sau
            }
            
            # Format final response
            formatted_response = {
                'success': True,
                'analysis_timestamp': datetime.now().isoformat(),
                'price_threshold': price_threshold,
                'segment_statistics': price_analysis,
                'ai_analysis': ai_analysis,
                'properties_analyzed': budget_properties,
                'ai_confidence': ai_analysis.get('ai_confidence', 'Medium'),
                'method': 'gemini_ai_analysis'
            }
            
            return formatted_response
            
        except (json.JSONDecodeError, ValueError) as e:
            print(f"AI response parsing error: {e}")
            # Fallback: tạo insights từ raw text
            return {
                'success': True,
                'analysis_timestamp': datetime.now().isoformat(),
                'price_threshold': price_threshold,
                'segment_statistics': {
                    'total_properties': len(budget_properties),
                    'avg_price': sum([p['price_vnd'] for p in budget_properties]) / len(budget_properties),
                    'price_threshold': price_threshold
                },
                'ai_analysis': {
                    'market_overview': {'segment_health': 'AI analysis completed'},
                    'actionable_insights': [ai_response[:200] + '...']
                },
                'properties_analyzed': budget_properties,
                'ai_confidence': 'Medium',
                'method': 'gemini_ai_analysis'
            }
    
    def _fallback_analysis(self, properties: List[Dict], price_threshold: int) -> Dict:
        """Fallback analysis khi AI không available"""
        
        budget_properties = [
            prop for prop in properties 
            if prop.get('price_vnd', 0) <= price_threshold
        ]
        
        if not budget_properties:
            return {
                'success': False,
                'message': f'Không có property nào dưới {price_threshold:,}₫'
            }
        
        prices = [prop['price_vnd'] for prop in budget_properties]
        avg_price = sum(prices) / len(prices)
        
        return {
            'success': True,
            'analysis_timestamp': datetime.now().isoformat(),
            'price_threshold': price_threshold,
            'segment_statistics': {
                'total_properties': len(budget_properties),
                'avg_price': avg_price,
                'min_price': min(prices),
                'max_price': max(prices),
                'price_threshold': price_threshold
            },
            'ai_analysis': {
                'market_overview': {
                    'segment_health': 'Segment analysis completed with fallback method'
                },
                'actionable_insights': [
                    f'Có {len(budget_properties)} properties dưới {price_threshold:,}₫',
                    f'Giá trung bình segment: {avg_price:,.0f}₫',
                    'Đây là thị trường cạnh tranh cao cho phân khúc budget'
                ]
            },
            'properties_analyzed': budget_properties,
            'ai_confidence': 'Low',
            'method': 'fallback_analysis'
        }
    
    def _prepare_range_ai_context(self, range_properties: List[Dict], min_price: int, max_price: int, all_properties: List[Dict]) -> str:
        """Chuẩn bị context data cho AI analysis với price range"""
        
        # Tính toán statistics cho range
        range_prices = [prop['price_vnd'] for prop in range_properties]
        all_prices = [prop['price_vnd'] for prop in all_properties]
        
        # Range statistics
        range_avg = sum(range_prices) / len(range_prices) if range_prices else 0
        range_min = min(range_prices) if range_prices else 0
        range_max = max(range_prices) if range_prices else 0
        
        # Market comparison
        market_avg = sum(all_prices) / len(all_prices) if all_prices else 0
        market_share = len(range_properties) / len(all_properties) * 100 if all_properties else 0
        
        # Location và rating analysis
        locations = [prop.get('location', 'N/A') for prop in range_properties]
        ratings = [float(prop.get('rating', '0')) for prop in range_properties if prop.get('rating', '0') != 'N/A']
        avg_rating = sum(ratings) / len(ratings) if ratings else 0
        
        location_counts = {}
        for loc in locations:
            location_counts[loc] = location_counts.get(loc, 0) + 1
        
        # Sample properties trong range
        properties_summary = []
        for prop in range_properties[:8]:  # Top 8 properties
            properties_summary.append({
                'name': prop.get('name', 'N/A'),
                'price': prop.get('price_vnd', 0),
                'rating': prop.get('rating', 'N/A'),
                'location': prop.get('location', 'N/A')
            })
        
        context = f"""
PRICE RANGE MARKET ANALYSIS - HANOI OLD QUARTER

ANALYSIS FOCUS: Properties in range {min_price:,}₫ - {max_price:,}₫ per night
DATE: {datetime.now().strftime('%Y-%m-%d')}
LOCATION: Hanoi Old Quarter (Khu Phố Cổ)

PRICE RANGE SEGMENT STATISTICS:
- Properties in Range: {len(range_properties)} / {len(all_properties)} total
- Market Share: {market_share:.1f}% of analyzed properties
- Range Price: {range_min:,}₫ - {range_max:,}₫ 
- Range Average: {range_avg:,.0f}₫
- Market Average: {market_avg:,.0f}₫
- Average Rating: {avg_rating:.1f}/10

COMPETITIVE POSITIONING:
- Range vs Market: {"Above average" if range_avg > market_avg else "Below average" if range_avg < market_avg else "At market level"}
- Price Position: {((range_avg / market_avg - 1) * 100):+.1f}% vs market average

LOCATION DISTRIBUTION IN RANGE:
{json.dumps(location_counts, indent=2, ensure_ascii=False)}

SAMPLE PROPERTIES IN RANGE:
{json.dumps(properties_summary, indent=2, ensure_ascii=False)}

MARKET CONTEXT:
- Target Range: {min_price:,}₫ - {max_price:,}₫
- Segment Classification: {"Budget" if max_price <= 600000 else "Mid-range" if max_price <= 1200000 else "Upscale" if max_price <= 2000000 else "Luxury"}
- Competition Density: {"High" if market_share > 30 else "Medium" if market_share > 15 else "Low"}
- Location Advantage: Prime Old Quarter tourist area
- Customer Profile: {"Budget travelers" if max_price <= 600000 else "Mid-tier tourists" if max_price <= 1200000 else "Premium travelers"}

STRATEGIC CONTEXT:
- Hotel: 118 Hang Bac Hostel positioning analysis
- Competitive landscape within this specific price range
- Optimization opportunities for this segment
- Risk assessment for this price positioning
"""
        
        return context
    
    def _call_range_gemini_ai(self, context: str) -> str:
        """Gọi Gemini AI với range-specific pricing analysis prompt"""
        
        prompt = f"""
You are an expert hospitality revenue management consultant specializing in dynamic pricing strategies for boutique accommodations in Southeast Asia. Analyze the provided price range data and provide strategic insights.

{context}

ANALYSIS REQUIREMENTS FOR THIS PRICE RANGE:
1. SEGMENT POSITIONING: How does this price range position in the overall market?
2. COMPETITIVE DYNAMICS: Who are the key competitors in this exact range?
3. CUSTOMER VALUE PROPOSITION: What value do customers expect at this price point?
4. PRICING ELASTICITY: How price-sensitive are customers in this range?
5. REVENUE OPTIMIZATION: How to maximize revenue within this range?
6. DIFFERENTIATION STRATEGY: How to stand out in this specific price segment?

RANGE-SPECIFIC FOCUS AREAS:
- Price range competitive analysis vs adjacent segments
- Customer behavior patterns within this price band
- Seasonal demand fluctuations for this segment
- Location premium opportunities within the range
- Service level expectations vs pricing
- Revenue per available room (RevPAR) optimization

Please provide your analysis in the following JSON format:

{{
    "range_analysis": {{
        "segment_position": "Position of this range in overall market",
        "competition_intensity": "Level of competition within this range",
        "customer_profile": "Detailed profile of customers in this range",
        "demand_drivers": "What drives demand in this price segment"
    }},
    "competitive_insights": {{
        "direct_competitors": "Key competitors in this exact range",
        "competitive_advantages": "Advantages our property could have",
        "market_gaps": "Gaps or opportunities in this range",
        "differentiation_potential": "How to differentiate in this segment"
    }},
    "pricing_strategy": {{
        "optimal_positioning": "Recommended positioning within the range",
        "pricing_flexibility": "How much pricing flexibility exists",
        "seasonal_adjustments": "Recommended seasonal pricing changes",
        "demand_optimization": "How to optimize for demand patterns"
    }},
    "revenue_opportunities": [
        {{
            "opportunity": "Specific revenue opportunity",
            "implementation": "How to implement this opportunity",
            "revenue_impact": "Expected revenue impact",
            "timeframe": "Implementation timeframe"
        }}
    ],
    "strategic_recommendations": [
        {{
            "recommendation": "Strategic recommendation for this range",
            "priority": "High/Medium/Low",
            "rationale": "Why this recommendation makes sense",
            "success_metrics": "How to measure success"
        }}
    ],
    "risk_assessment": {{
        "pricing_risks": ["Risks specific to this price range"],
        "market_risks": ["Market risks that could affect this segment"],
        "mitigation_strategies": ["How to mitigate identified risks"]
    }},
    "immediate_actions": [
        "Immediate action item 1 for this price range",
        "Immediate action item 2 for this price range",
        "Immediate action item 3 for this price range"
    ],
    "range_confidence": "High/Medium/Low confidence in this range analysis"
}}

Focus on actionable insights specific to this exact price range that a hotel owner can implement immediately.
"""
        
        try:
            model = genai.GenerativeModel('gemini-2.0-flash-exp')
            response = model.generate_content(prompt)
            return response.text.strip()
        except Exception as e:
            print(f"Gemini AI range call error: {e}")
            return self._generate_fallback_range_response()
    
    def _format_range_ai_response(self, ai_response: str, range_properties: List[Dict], min_price: int, max_price: int) -> Dict:
        """Format AI response cho price range analysis"""
        
        try:
            # Extract JSON từ AI response
            json_start = ai_response.find('{')
            json_end = ai_response.rfind('}') + 1
            
            if json_start >= 0 and json_end > json_start:
                json_str = ai_response[json_start:json_end]
                ai_analysis = json.loads(json_str)
            else:
                raise ValueError("No valid JSON found in AI response")
            
            # Tính toán range statistics
            prices = [prop['price_vnd'] for prop in range_properties]
            range_analysis = {
                'total_properties': len(range_properties),
                'avg_price': sum(prices) / len(prices) if prices else 0,
                'min_price': min(prices) if prices else min_price,
                'max_price': max(prices) if prices else max_price,
                'price_range': f"{min_price:,}₫ - {max_price:,}₫",
                'range_width': max_price - min_price
            }
            
            # Format final response
            formatted_response = {
                'success': True,
                'analysis_timestamp': datetime.now().isoformat(),
                'price_range': {
                    'min_price': min_price,
                    'max_price': max_price,
                    'range_display': f"{min_price:,}₫ - {max_price:,}₫"
                },
                'range_statistics': range_analysis,
                'ai_analysis': ai_analysis,
                'properties_analyzed': range_properties,
                'ai_confidence': ai_analysis.get('range_confidence', 'Medium'),
                'method': 'gemini_range_analysis'
            }
            
            return formatted_response
            
        except (json.JSONDecodeError, ValueError) as e:
            print(f"AI range response parsing error: {e}")
            return self._fallback_range_analysis_formatted(range_properties, min_price, max_price)
    
    def _fallback_range_analysis(self, properties: List[Dict], min_price: int, max_price: int) -> Dict:
        """Fallback analysis cho price range khi AI không available"""
        
        range_properties = [
            prop for prop in properties 
            if min_price <= prop.get('price_vnd', 0) <= max_price
        ]
        
        if not range_properties:
            return {
                'success': False,
                'message': f'Không có property nào trong khoảng {min_price:,}₫ - {max_price:,}₫'
            }
        
        return self._fallback_range_analysis_formatted(range_properties, min_price, max_price)
    
    def _fallback_range_analysis_formatted(self, range_properties: List[Dict], min_price: int, max_price: int) -> Dict:
        """Format fallback analysis results"""
        
        prices = [prop['price_vnd'] for prop in range_properties]
        avg_price = sum(prices) / len(prices) if prices else 0
        
        # Basic analysis
        segment_type = "Budget" if max_price <= 600000 else "Mid-range" if max_price <= 1200000 else "Upscale"
        
        return {
            'success': True,
            'analysis_timestamp': datetime.now().isoformat(),
            'price_range': {
                'min_price': min_price,
                'max_price': max_price,
                'range_display': f"{min_price:,}₫ - {max_price:,}₫"
            },
            'range_statistics': {
                'total_properties': len(range_properties),
                'avg_price': avg_price,
                'min_price': min(prices) if prices else min_price,
                'max_price': max(prices) if prices else max_price,
                'range_width': max_price - min_price
            },
            'ai_analysis': {
                'range_analysis': {
                    'segment_position': f'{segment_type} segment analysis completed',
                    'competition_intensity': 'Medium to High',
                    'customer_profile': f'{segment_type} travelers seeking value'
                },
                'immediate_actions': [
                    f'Có {len(range_properties)} properties trong khoảng {min_price:,}₫ - {max_price:,}₫',
                    f'Giá trung bình segment: {avg_price:,.0f}₫',
                    f'Phân khúc {segment_type} - cạnh tranh cao tại Old Quarter'
                ]
            },
            'properties_analyzed': range_properties,
            'ai_confidence': 'Low',
            'method': 'fallback_range_analysis'
        }
    
    def _generate_fallback_range_response(self) -> str:
        """Generate fallback response cho range analysis khi AI call fails"""
        return json.dumps({
            "range_analysis": {
                "segment_position": "Price range analysis completed with limited AI",
                "competition_intensity": "High competition in selected range",
                "customer_profile": "Price-conscious customers in this segment"
            },
            "immediate_actions": [
                "Analyze competitors in this exact price range",
                "Optimize value proposition for this segment",
                "Monitor pricing trends in this range"
            ],
            "range_confidence": "Low"
        })
        """Generate fallback response when AI call fails"""
        return json.dumps({
            "market_overview": {
                "segment_health": "Budget segment analysis completed with limited AI",
                "competition_level": "High competition in budget accommodation",
                "customer_behavior": "Price-sensitive customers seeking value"
            },
            "actionable_insights": [
                "Focus on competitive pricing in budget segment",
                "Leverage Old Quarter location premium",
                "Monitor competitor pricing regularly"
            ],
            "ai_confidence": "Low"
        })

# Utility functions để sử dụng trong app.py
def analyze_budget_pricing_with_ai(properties: List[Dict], price_threshold: int, google_api_key: Optional[str]) -> Dict:
    """
    Wrapper function để phân tích pricing với AI (legacy - threshold-based)
    
    Args:
        properties: Danh sách properties
        price_threshold: Ngưỡng giá (VD: 500000)
        google_api_key: Google API key
        
    Returns:
        Dict chứa AI analysis results
    """
    analyst = AIPricingAnalyst(google_api_key)
    return analyst.analyze_budget_segment(properties, price_threshold)

def analyze_price_range_with_ai(properties: List[Dict], min_price: int, max_price: int, google_api_key: Optional[str]) -> Dict:
    """
    Wrapper function để phân tích price range với AI (new - range-based)
    
    Args:
        properties: Danh sách properties
        min_price: Giá tối thiểu (VND)
        max_price: Giá tối đa (VND)
        google_api_key: Google API key
        
    Returns:
        Dict chứa AI range analysis results
    """
    analyst = AIPricingAnalyst(google_api_key)
    return analyst.analyze_price_range_segment(properties, min_price, max_price)
