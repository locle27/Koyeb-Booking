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
    
    def analyze_budget_segment(self, properties: List[Dict], price_threshold: int = 500000) -> Dict:
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
    
    def _generate_fallback_ai_response(self) -> str:
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

# Utility function để sử dụng trong app.py
def analyze_budget_pricing_with_ai(properties: List[Dict], price_threshold: int, google_api_key: Optional[str]) -> Dict:
    """
    Wrapper function để phân tích pricing với AI
    
    Args:
        properties: Danh sách properties
        price_threshold: Ngưỡng giá (VD: 500000)
        google_api_key: Google API key
        
    Returns:
        Dict chứa AI analysis results
    """
    analyst = AIPricingAnalyst(google_api_key)
    return analyst.analyze_budget_segment(properties, price_threshold)
