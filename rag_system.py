"""
🧠 Hotel RAG System - Advanced Retrieval-Augmented Generation
Ultra-fast implementation for immediate deployment
"""

import json
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from sentence_transformers import SentenceTransformer
import chromadb
from chromadb.config import Settings
import re
from typing import List, Dict, Any, Optional
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class HotelRAGSystem:
    """
    Fast, production-ready RAG system for hotel operations
    Features:
    - Guest booking context retrieval
    - Hotel policy knowledge base
    - Hanoi tourism information
    - Dynamic response generation
    """
    
    def __init__(self, data_directory="rag_data"):
        """Initialize RAG system with lightweight components"""
        self.data_dir = data_directory
        self.model = SentenceTransformer('all-MiniLM-L6-v2')  # Fast, lightweight model
        
        # Initialize ChromaDB (local, no server needed)
        self.chroma_client = chromadb.PersistentClient(path=f"./{data_directory}/chroma_db")
        
        # Initialize collections
        self.collections = {
            'guest_data': self._get_or_create_collection('guest_data'),
            'hotel_policies': self._get_or_create_collection('hotel_policies'),
            'hanoi_tourism': self._get_or_create_collection('hanoi_tourism'),
            'staff_knowledge': self._get_or_create_collection('staff_knowledge')
        }
        
        logger.info("✅ Hotel RAG System initialized successfully")
    
    def _get_or_create_collection(self, name: str):
        """Get or create ChromaDB collection"""
        try:
            return self.chroma_client.get_collection(name)
        except:
            return self.chroma_client.create_collection(name)
    
    async def initialize_knowledge_base(self, booking_data_path: str = None):
        """Initialize knowledge base from existing hotel data"""
        try:
            logger.info("🔄 Initializing knowledge base...")
            
            # 1. Hotel Policies Knowledge Base
            await self._create_hotel_policies_kb()
            
            # 2. Hanoi Tourism Knowledge Base  
            await self._create_hanoi_tourism_kb()
            
            # 3. Staff Knowledge Base
            await self._create_staff_knowledge_kb()
            
            # 4. Guest Data (if booking data provided)
            if booking_data_path:
                await self._index_guest_data(booking_data_path)
            
            logger.info("✅ Knowledge base initialized successfully")
            
        except Exception as e:
            logger.error(f"❌ Error initializing knowledge base: {e}")
            raise
    
    async def _create_hotel_policies_kb(self):
        """Create hotel policies knowledge base"""
        policies = [
            {
                "topic": "Check-in Policy",
                "content": "Check-in time is 14:00. Early check-in subject to availability. Valid ID required. Payment due at check-in.",
                "category": "check_in"
            },
            {
                "topic": "Check-out Policy", 
                "content": "Check-out time is 12:00. Late check-out available until 15:00 for 50% daily rate. Express check-out available.",
                "category": "check_out"
            },
            {
                "topic": "Cancellation Policy",
                "content": "Free cancellation up to 24 hours before arrival. Late cancellation or no-show: 1 night charge.",
                "category": "cancellation"
            },
            {
                "topic": "Payment Policy",
                "content": "Accept cash (VND), credit cards (Visa, Mastercard), bank transfer. No foreign currency exchange.",
                "category": "payment"
            },
            {
                "topic": "Taxi Service",
                "content": "Airport taxi service available: 280,000 VND to Noi Bai Airport. City taxi: 50,000-100,000 VND. Book through reception.",
                "category": "transportation"
            },
            {
                "topic": "Amenities",
                "content": "Free WiFi, air conditioning, hot water, towels, toiletries. Shared kitchen, common area, luggage storage.",
                "category": "amenities"
            },
            {
                "topic": "House Rules",
                "content": "Quiet hours 22:00-08:00. No smoking indoors. No guests after 23:00. Keep room clean.",
                "category": "rules"
            }
        ]
        
        # Add to vector database
        for i, policy in enumerate(policies):
            embedding = self.model.encode(policy["content"])
            
            self.collections['hotel_policies'].add(
                embeddings=[embedding.tolist()],
                documents=[policy["content"]],
                metadatas=[{
                    "topic": policy["topic"],
                    "category": policy["category"],
                    "source": "hotel_policies"
                }],
                ids=[f"policy_{i}"]
            )
        
        logger.info("✅ Hotel policies knowledge base created")
    
    async def _create_hanoi_tourism_kb(self):
        """Create Hanoi tourism knowledge base"""
        tourism_info = [
            {
                "topic": "Hoan Kiem Lake",
                "content": "Beautiful lake in Old Quarter, 10 minutes walk from hotel. Best visited early morning or evening. Free to visit.",
                "category": "attractions"
            },
            {
                "topic": "Old Quarter",
                "content": "Historic area with narrow streets, traditional shops, street food. Walking distance from hotel. Best for shopping and dining.",
                "category": "districts"
            },
            {
                "topic": "Temple of Literature",
                "content": "Vietnam's first university, beautiful architecture. 15 minutes by taxi. Entry fee: 30,000 VND. Open 8:30-17:30.",
                "category": "attractions"
            },
            {
                "topic": "Street Food",
                "content": "Try pho, bun cha, banh mi. Hang Buom Street (2 min walk) has great local food. Prices: 30,000-80,000 VND per meal.",
                "category": "food"
            },
            {
                "topic": "Shopping",
                "content": "Dong Xuan Market (5 min walk) for souvenirs. Hang Gai Street for silk. Weekend Night Market Friday-Sunday.",
                "category": "shopping"
            },
            {
                "topic": "Transportation",
                "content": "Grab taxi most convenient. Motorbike taxi cheaper but less safe. Bus #17 to airport. Walk for nearby attractions.",
                "category": "transport"
            },
            {
                "topic": "Weather",
                "content": "Hot humid summer (May-Sep), cool dry winter (Oct-Apr). Rainy season Jun-Aug. Pack accordingly.",
                "category": "weather"
            }
        ]
        
        for i, info in enumerate(tourism_info):
            embedding = self.model.encode(info["content"])
            
            self.collections['hanoi_tourism'].add(
                embeddings=[embedding.tolist()],
                documents=[info["content"]],
                metadatas=[{
                    "topic": info["topic"],
                    "category": info["category"],
                    "source": "hanoi_tourism"
                }],
                ids=[f"tourism_{i}"]
            )
        
        logger.info("✅ Hanoi tourism knowledge base created")
    
    async def _create_staff_knowledge_kb(self):
        """Create staff knowledge and procedures"""
        staff_knowledge = [
            {
                "topic": "Guest Complaints",
                "content": "Listen actively, apologize, offer solution. Common issues: noise, AC, WiFi. Escalate to manager if needed.",
                "category": "service_recovery"
            },
            {
                "topic": "Emergency Procedures",
                "content": "Fire: evacuation route posted. Medical: call 115. Police: call 113. Guest lockout: master key at reception.",
                "category": "emergency"
            },
            {
                "topic": "VIP Guest Service",
                "content": "Repeat guests, long stays, positive reviews get priority. Offer room upgrade, late checkout, welcome drink.",
                "category": "vip_service"
            },
            {
                "topic": "Maintenance Issues",
                "content": "Report immediately: water leaks, electrical problems, broken AC. Use maintenance log. Relocate guest if severe.",
                "category": "maintenance"
            }
        ]
        
        for i, knowledge in enumerate(staff_knowledge):
            embedding = self.model.encode(knowledge["content"])
            
            self.collections['staff_knowledge'].add(
                embeddings=[embedding.tolist()],
                documents=[knowledge["content"]],
                metadatas=[{
                    "topic": knowledge["topic"],
                    "category": knowledge["category"],
                    "source": "staff_knowledge"
                }],
                ids=[f"staff_{i}"]
            )
        
        logger.info("✅ Staff knowledge base created")
    
    async def retrieve_context(self, query: str, guest_name: str = None, top_k: int = 5) -> Dict[str, Any]:
        """
        Retrieve relevant context for query using RAG
        Returns structured context from multiple sources
        """
        query_embedding = self.model.encode(query)
        
        context = {
            'guest_context': {},
            'hotel_policies': [],
            'hanoi_info': [],
            'staff_guidance': [],
            'confidence_scores': {}
        }
        
        try:
            # 1. Guest-specific context (if guest name provided)
            if guest_name:
                context['guest_context'] = await self._get_guest_context(guest_name)
            
            # 2. Hotel policies search
            policy_results = self.collections['hotel_policies'].query(
                query_embeddings=[query_embedding.tolist()],
                n_results=top_k
            )
            
            if policy_results['documents'][0]:
                for i, doc in enumerate(policy_results['documents'][0]):
                    context['hotel_policies'].append({
                        'content': doc,
                        'metadata': policy_results['metadatas'][0][i],
                        'score': 1 - policy_results['distances'][0][i]  # Convert distance to similarity
                    })
            
            # 3. Hanoi tourism info search
            tourism_results = self.collections['hanoi_tourism'].query(
                query_embeddings=[query_embedding.tolist()],
                n_results=top_k
            )
            
            if tourism_results['documents'][0]:
                for i, doc in enumerate(tourism_results['documents'][0]):
                    context['hanoi_info'].append({
                        'content': doc,
                        'metadata': tourism_results['metadatas'][0][i],
                        'score': 1 - tourism_results['distances'][0][i]
                    })
            
            # 4. Staff knowledge search
            staff_results = self.collections['staff_knowledge'].query(
                query_embeddings=[query_embedding.tolist()],
                n_results=top_k
            )
            
            if staff_results['documents'][0]:
                for i, doc in enumerate(staff_results['documents'][0]):
                    context['staff_guidance'].append({
                        'content': doc,
                        'metadata': staff_results['metadatas'][0][i],
                        'score': 1 - staff_results['distances'][0][i]
                    })
            
            # Calculate overall confidence
            all_scores = []
            for source in ['hotel_policies', 'hanoi_info', 'staff_guidance']:
                if context[source]:
                    all_scores.extend([item['score'] for item in context[source]])
            
            context['confidence_scores'] = {
                'overall': np.mean(all_scores) if all_scores else 0,
                'max_relevance': max(all_scores) if all_scores else 0,
                'sources_found': len([s for s in ['hotel_policies', 'hanoi_info', 'staff_guidance'] if context[s]])
            }
            
            logger.info(f"✅ Retrieved context for query: {query[:50]}...")
            return context
            
        except Exception as e:
            logger.error(f"❌ Error retrieving context: {e}")
            return context
    
    async def _get_guest_context(self, guest_name: str) -> Dict[str, Any]:
        """Get guest-specific context from bookings"""
        # This will be enhanced when we integrate with Google Sheets
        # For now, return placeholder structure
        return {
            'name': guest_name,
            'booking_history': [],
            'preferences': {},
            'notes': []
        }
    
    def generate_rag_response(self, query: str, context: Dict[str, Any], max_length: int = 500) -> Dict[str, Any]:
        """
        Generate response using retrieved context
        Optimized for token efficiency in Claude Code environment
        """
        
        # Build context summary for efficient token usage
        context_summary = self._build_context_summary(context)
        
        # Create structured response
        response = {
            'answer': self._generate_contextual_answer(query, context_summary),
            'sources': self._extract_sources(context),
            'confidence': context['confidence_scores']['overall'],
            'guest_personalization': bool(context['guest_context']),
            'actionable_suggestions': self._generate_suggestions(query, context)
        }
        
        return response
    
    def _build_context_summary(self, context: Dict[str, Any]) -> str:
        """Build efficient context summary for response generation"""
        summary_parts = []
        
        # Guest context
        if context['guest_context'] and context['guest_context'].get('name'):
            summary_parts.append(f"Guest: {context['guest_context']['name']}")
        
        # Top hotel policies
        if context['hotel_policies']:
            top_policy = context['hotel_policies'][0]
            if top_policy['score'] > 0.5:
                summary_parts.append(f"Policy: {top_policy['content'][:100]}...")
        
        # Top Hanoi info
        if context['hanoi_info']:
            top_info = context['hanoi_info'][0]
            if top_info['score'] > 0.5:
                summary_parts.append(f"Hanoi: {top_info['content'][:100]}...")
        
        # Top staff guidance
        if context['staff_guidance']:
            top_guidance = context['staff_guidance'][0]
            if top_guidance['score'] > 0.5:
                summary_parts.append(f"Staff: {top_guidance['content'][:100]}...")
        
        return " | ".join(summary_parts)
    
    def _generate_contextual_answer(self, query: str, context_summary: str) -> str:
        """Generate answer based on context (simplified for immediate deployment)"""
        
        # For immediate deployment, return structured response
        # This will be enhanced with LLM integration
        
        if not context_summary:
            return "I don't have specific information about that. Please contact our staff for assistance."
        
        # Basic keyword matching for immediate functionality
        query_lower = query.lower()
        
        if any(word in query_lower for word in ['check-in', 'check in', 'arrival', 'time']):
            return "Check-in time is 14:00. Early check-in is subject to availability. Please bring valid ID and payment is due at check-in."
        
        elif any(word in query_lower for word in ['check-out', 'checkout', 'departure', 'leave']):
            return "Check-out time is 12:00. Late check-out is available until 15:00 for 50% of daily rate. Express check-out is also available."
        
        elif any(word in query_lower for word in ['taxi', 'airport', 'transport']):
            return "Airport taxi service: 280,000 VND to Noi Bai Airport. City taxi: 50,000-100,000 VND. Please book through reception."
        
        elif any(word in query_lower for word in ['food', 'restaurant', 'eat', 'pho']):
            return "Try pho, bun cha, banh mi on Hang Buom Street (2 minutes walk). Great local food, prices 30,000-80,000 VND per meal."
        
        elif any(word in query_lower for word in ['attraction', 'visit', 'see', 'tourism']):
            return "Hoan Kiem Lake is 10 minutes walk - beautiful in morning/evening. Old Quarter nearby for shopping and dining. Temple of Literature 15 minutes by taxi."
        
        else:
            return f"Based on our hotel knowledge: {context_summary[:200]}... Please let me know if you need more specific information!"
    
    def _extract_sources(self, context: Dict[str, Any]) -> List[str]:
        """Extract source references for transparency"""
        sources = []
        
        for source_type in ['hotel_policies', 'hanoi_info', 'staff_guidance']:
            for item in context[source_type]:
                if item['score'] > 0.5:  # Only high-confidence sources
                    sources.append(f"{item['metadata']['source']}: {item['metadata']['topic']}")
        
        return sources[:3]  # Limit to top 3 sources
    
    def _generate_suggestions(self, query: str, context: Dict[str, Any]) -> List[str]:
        """Generate actionable suggestions"""
        suggestions = []
        
        query_lower = query.lower()
        
        if 'taxi' in query_lower:
            suggestions.append("Book taxi through reception for best rates")
            suggestions.append("Consider Grab app for city transportation")
        
        elif any(word in query_lower for word in ['food', 'hungry', 'eat']):
            suggestions.append("Try the street food on Hang Buom Street (2 min walk)")
            suggestions.append("Ask reception for restaurant recommendations")
        
        elif any(word in query_lower for word in ['visit', 'see', 'tour']):
            suggestions.append("Start with Hoan Kiem Lake (10 min walk)")
            suggestions.append("Explore Old Quarter for authentic experience")
        
        return suggestions

# Global RAG instance for app integration
hotel_rag = None

async def initialize_hotel_rag():
    """Initialize global RAG instance"""
    global hotel_rag
    hotel_rag = HotelRAGSystem()
    await hotel_rag.initialize_knowledge_base()
    return hotel_rag

def get_hotel_rag():
    """Get global RAG instance"""
    return hotel_rag