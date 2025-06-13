"""
🚀 Simple Hotel RAG System - Zero External Dependencies
Fast deployment, immediate functionality
Uses built-in Python libraries for vector similarity
"""

import json
import re
import math
import os
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from collections import defaultdict
import sqlite3

class SimpleHotelRAG:
    """
    Lightweight RAG system using only built-in Python libraries
    Features:
    - TF-IDF similarity search
    - SQLite for persistence  
    - Guest booking context
    - Hotel knowledge base
    """
    
    def __init__(self, db_path="hotel_rag.db"):
        self.db_path = db_path
        self.knowledge_base = {}
        self.guest_bookings = {}
        self._initialize_database()
        self._load_hotel_knowledge()
        
        print("✅ Simple Hotel RAG System initialized")
    
    def _initialize_database(self):
        """Initialize SQLite database for persistence"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create knowledge base table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS knowledge_base (
                id INTEGER PRIMARY KEY,
                category TEXT,
                topic TEXT,
                content TEXT,
                keywords TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create guest context table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS guest_context (
                id INTEGER PRIMARY KEY,
                guest_name TEXT,
                booking_id TEXT,
                context_data TEXT,
                last_interaction TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
        print("✅ Database initialized")
    
    def _load_hotel_knowledge(self):
        """Load hotel knowledge base"""
        knowledge_data = [
            {
                "category": "check_in",
                "topic": "Check-in Policy",
                "content": "Check-in time is 14:00 (2 PM). Early check-in is subject to availability and may incur additional charges. Please bring valid identification (passport or ID card) and payment is due at check-in. We accept cash (VND), credit cards (Visa, Mastercard), and bank transfers.",
                "keywords": "check-in check in arrival time 14:00 2pm early id identification payment"
            },
            {
                "category": "check_out", 
                "topic": "Check-out Policy",
                "content": "Check-out time is 12:00 (noon). Late check-out is available until 15:00 (3 PM) for 50% of the daily rate. Express check-out is available - just leave your key at reception. Please settle any outstanding charges before departure.",
                "keywords": "check-out checkout departure leave 12:00 noon late express charges"
            },
            {
                "category": "cancellation",
                "topic": "Cancellation Policy", 
                "content": "Free cancellation up to 24 hours before arrival date. Late cancellation or no-show will result in a charge of one night's accommodation. For group bookings (5+ rooms), different terms may apply.",
                "keywords": "cancel cancellation free 24 hours no-show charge group booking policy"
            },
            {
                "category": "payment",
                "topic": "Payment Methods",
                "content": "We accept Vietnamese Dong (VND) cash, major credit cards (Visa, Mastercard), and bank transfers. Foreign currency exchange is not available at the hotel. ATMs are located nearby on Hang Bac Street.",
                "keywords": "payment cash credit card visa mastercard bank transfer vnd currency atm"
            },
            {
                "category": "transportation",
                "topic": "Taxi and Transportation",
                "content": "Airport taxi service to Noi Bai Airport: 280,000 VND (fixed rate). City taxi rides typically cost 50,000-100,000 VND. Book through reception for guaranteed rates. Grab taxi app is also reliable. Bus #17 connects to airport (cheaper option).",
                "keywords": "taxi airport noi bai transportation 280000 grab bus city reception book"
            },
            {
                "category": "amenities",
                "topic": "Hotel Amenities",
                "content": "Free WiFi throughout property, air conditioning in all rooms, hot water 24/7, fresh towels daily, complimentary toiletries. Shared kitchen facilities, comfortable common area, secure luggage storage, and laundry service available.",
                "keywords": "wifi internet air conditioning hot water towels toiletries kitchen common area luggage laundry"
            },
            {
                "category": "location",
                "topic": "Location and Nearby",
                "content": "Located in the heart of Hanoi's Old Quarter on Hang Bac Street. Hoan Kiem Lake is 10 minutes walk. Dong Xuan Market 5 minutes walk. Weekend Night Market on weekends. Many restaurants, cafes, and shops within walking distance.",
                "keywords": "location old quarter hang bac hoan kiem lake dong xuan market weekend night market walking distance"
            },
            {
                "category": "attractions",
                "topic": "Hanoi Attractions",
                "content": "Hoan Kiem Lake (10 min walk) - beautiful lake, best visited early morning or evening. Temple of Literature (15 min taxi) - Vietnam's first university, 30,000 VND entry. Old Quarter narrow streets perfect for walking and shopping. Night market Friday-Sunday.",
                "keywords": "hoan kiem lake temple literature old quarter attractions walking shopping night market friday sunday"
            },
            {
                "category": "food",
                "topic": "Local Food Recommendations", 
                "content": "Must try: Pho (noodle soup), Bun Cha (grilled pork with noodles), Banh Mi (Vietnamese sandwich). Hang Buom Street (2 minutes walk) has excellent local food. Typical meal costs 30,000-80,000 VND. Ask reception for specific restaurant recommendations.",
                "keywords": "food pho bun cha banh mi hang buom street local restaurant recommendations meal cost reception"
            },
            {
                "category": "rules",
                "topic": "House Rules",
                "content": "Quiet hours: 22:00-08:00. No smoking indoors (smoking area available). No outside guests after 23:00. Please keep rooms clean and respect other guests. Report any issues to reception immediately.",
                "keywords": "quiet hours smoking guests rules clean respect reception issues report"
            },
            {
                "category": "emergency",
                "topic": "Emergency Information",
                "content": "Fire emergency: dial 114. Medical emergency: dial 115. Police: dial 113. Hotel emergency contact: reception 24/7. Nearest hospital: Bach Mai Hospital (15 min taxi). Emergency evacuation route posted in each room.",
                "keywords": "emergency fire medical police 114 115 113 hospital bach mai evacuation route reception"
            },
            {
                "category": "wifi",
                "topic": "WiFi and Internet",
                "content": "Free WiFi available throughout the hotel. Network name: 118HangBac_Guest. Password available at reception. High-speed internet suitable for work and streaming. Technical support available 24/7.",
                "keywords": "wifi internet free network password reception high-speed work streaming technical support"
            }
        ]
        
        # Store in database
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        for item in knowledge_data:
            cursor.execute('''
                INSERT OR REPLACE INTO knowledge_base (category, topic, content, keywords)
                VALUES (?, ?, ?, ?)
            ''', (item['category'], item['topic'], item['content'], item['keywords']))
        
        conn.commit()
        conn.close()
        
        # Load into memory for fast access
        self.knowledge_base = {item['category']: item for item in knowledge_data}
        print("✅ Hotel knowledge base loaded")
    
    def calculate_similarity(self, query: str, content: str, keywords: str) -> float:
        """Calculate similarity using simple keyword matching and TF-IDF-like scoring"""
        query_lower = query.lower()
        content_lower = content.lower()
        keywords_lower = keywords.lower()
        
        # Simple keyword matching score
        query_words = set(re.findall(r'\w+', query_lower))
        content_words = set(re.findall(r'\w+', content_lower))
        keyword_words = set(re.findall(r'\w+', keywords_lower))
        
        # Calculate scores
        keyword_matches = len(query_words.intersection(keyword_words))
        content_matches = len(query_words.intersection(content_words))
        
        # Weighted scoring (keywords have higher weight)
        keyword_score = keyword_matches * 2.0
        content_score = content_matches * 1.0
        
        # Normalize by query length
        total_score = (keyword_score + content_score) / len(query_words) if query_words else 0
        
        # Bonus for exact phrase matches
        if any(word in content_lower for word in query_words if len(word) > 3):
            total_score += 0.3
        
        return min(total_score, 1.0)  # Cap at 1.0
    
    def retrieve_context(self, query: str, guest_name: str = None, top_k: int = 3) -> Dict[str, Any]:
        """Retrieve relevant context for query"""
        
        # Get all knowledge base entries
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT category, topic, content, keywords FROM knowledge_base')
        kb_entries = cursor.fetchall()
        conn.close()
        
        # Calculate similarities
        scored_entries = []
        for category, topic, content, keywords in kb_entries:
            score = self.calculate_similarity(query, content, keywords)
            if score > 0.1:  # Only include relevant entries
                scored_entries.append({
                    'category': category,
                    'topic': topic,
                    'content': content,
                    'score': score
                })
        
        # Sort by score and get top results
        scored_entries.sort(key=lambda x: x['score'], reverse=True)
        top_entries = scored_entries[:top_k]
        
        # Build context response
        context = {
            'query': query,
            'guest_name': guest_name,
            'relevant_info': top_entries,
            'confidence': max([entry['score'] for entry in top_entries]) if top_entries else 0,
            'sources_count': len(top_entries),
            'timestamp': datetime.now().isoformat()
        }
        
        # Add guest-specific context if available
        if guest_name:
            context['guest_context'] = self._get_guest_context(guest_name)
        
        return context
    
    def _get_guest_context(self, guest_name: str) -> Dict[str, Any]:
        """Get guest-specific context from previous interactions"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            SELECT booking_id, context_data, last_interaction 
            FROM guest_context 
            WHERE guest_name = ? 
            ORDER BY last_interaction DESC 
            LIMIT 5
        ''', (guest_name,))
        
        results = cursor.fetchall()
        conn.close()
        
        guest_context = {
            'name': guest_name,
            'recent_interactions': [],
            'booking_history': []
        }
        
        for booking_id, context_data, last_interaction in results:
            try:
                context_json = json.loads(context_data) if context_data else {}
                guest_context['recent_interactions'].append({
                    'booking_id': booking_id,
                    'context': context_json,
                    'timestamp': last_interaction
                })
            except:
                pass
        
        return guest_context
    
    def save_guest_interaction(self, guest_name: str, booking_id: str, interaction_data: Dict[str, Any]):
        """Save guest interaction for future context"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO guest_context (guest_name, booking_id, context_data)
            VALUES (?, ?, ?)
        ''', (guest_name, booking_id, json.dumps(interaction_data)))
        
        conn.commit()
        conn.close()
    
    def generate_rag_response(self, query: str, guest_name: str = None) -> Dict[str, Any]:
        """Generate complete RAG response"""
        
        # Retrieve context
        context = self.retrieve_context(query, guest_name)
        
        # Generate answer based on context
        answer = self._generate_contextual_answer(query, context)
        
        # Generate suggestions
        suggestions = self._generate_suggestions(query, context)
        
        response = {
            'query': query,
            'answer': answer,
            'confidence': context['confidence'],
            'sources': [entry['topic'] for entry in context['relevant_info']],
            'suggestions': suggestions,
            'guest_personalized': bool(guest_name and context.get('guest_context')),
            'timestamp': datetime.now().isoformat()
        }
        
        # Save interaction if guest provided
        if guest_name:
            self.save_guest_interaction(guest_name, f"query_{datetime.now().timestamp()}", {
                'query': query,
                'response': answer,
                'confidence': context['confidence']
            })
        
        return response
    
    def _generate_contextual_answer(self, query: str, context: Dict[str, Any]) -> str:
        """Generate contextual answer from retrieved information"""
        
        if not context['relevant_info']:
            return "I don't have specific information about that. Please contact our reception for assistance. We're available 24/7 to help!"
        
        # Use the highest scoring entry as primary answer
        primary_info = context['relevant_info'][0]
        answer = primary_info['content']
        
        # Add personalization if guest context available
        if context.get('guest_context') and context['guest_context']['name']:
            guest_name = context['guest_context']['name']
            answer = f"Hi {guest_name}! {answer}"
        
        # Add confidence indicator for transparency
        confidence_level = context['confidence']
        if confidence_level > 0.8:
            confidence_text = "I'm confident this information is accurate."
        elif confidence_level > 0.5:
            confidence_text = "This should help answer your question."
        else:
            confidence_text = "This is the best match I found - please confirm with reception if needed."
        
        return f"{answer}\n\n{confidence_text}"
    
    def _generate_suggestions(self, query: str, context: Dict[str, Any]) -> List[str]:
        """Generate helpful suggestions based on query and context"""
        suggestions = []
        query_lower = query.lower()
        
        # Category-based suggestions
        if context['relevant_info']:
            primary_category = context['relevant_info'][0]['category']
            
            if primary_category == 'transportation':
                suggestions.extend([
                    "Book taxi through reception for guaranteed rates",
                    "Download Grab app for convenient city transportation",
                    "Ask about bus routes for budget-friendly options"
                ])
            
            elif primary_category == 'food':
                suggestions.extend([
                    "Try Hang Buom Street (2 minutes walk) for authentic local food",
                    "Ask reception for restaurant recommendations based on your preferences",
                    "Don't miss weekend night market for street food experience"
                ])
            
            elif primary_category == 'attractions':
                suggestions.extend([
                    "Start with Hoan Kiem Lake - it's beautiful and close by",
                    "Explore Old Quarter on foot for the best experience",
                    "Ask reception about current events and festivals"
                ])
            
            elif primary_category in ['check_in', 'check_out']:
                suggestions.extend([
                    "Contact reception if you need to adjust your timing",
                    "Ask about luggage storage if arriving early or leaving late",
                    "Confirm payment methods accepted"
                ])
        
        # General helpful suggestions
        if 'time' in query_lower or 'when' in query_lower:
            suggestions.append("Reception is available 24/7 for any timing questions")
        
        if 'cost' in query_lower or 'price' in query_lower or 'how much' in query_lower:
            suggestions.append("Ask reception for current rates and any available discounts")
        
        return suggestions[:3]  # Limit to 3 most relevant suggestions

# Global instance
simple_rag = SimpleHotelRAG()

def get_simple_rag():
    """Get global RAG instance"""
    return simple_rag