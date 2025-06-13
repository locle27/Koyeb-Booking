#!/usr/bin/env python3
"""
🧠 Test Gemini-Enhanced RAG System
Complete testing of both Simple RAG and Gemini-enhanced responses
"""

import json
from gemini_rag import initialize_gemini_rag
from simple_rag import SimpleHotelRAG
import os

def test_gemini_rag():
    """Test the Gemini-enhanced RAG system"""
    
    print("🚀 Testing Gemini-Enhanced RAG System")
    print("=" * 60)
    
    # Test queries
    test_queries = [
        {
            "query": "What time is check-in?",
            "guest_name": "",
            "description": "Basic hotel information"
        },
        {
            "query": "Where can I eat nearby?",
            "guest_name": "",
            "description": "Food/restaurant recommendations"
        },
        {
            "query": "How much is taxi to airport?",
            "guest_name": "John Smith",
            "description": "Transportation with guest context"
        },
        {
            "query": "I need help with late check-out tomorrow",
            "guest_name": "Mary Johnson",
            "description": "Service request with guest personalization"
        }
    ]
    
    # Initialize systems
    print("🔧 Initializing RAG systems...")
    simple_rag = SimpleHotelRAG()
    
    # Try to initialize Gemini (will fallback gracefully if API key missing)
    try:
        gemini_rag = initialize_gemini_rag()
        gemini_available = gemini_rag.gemini_available if gemini_rag else False
    except Exception as e:
        print(f"⚠️ Gemini initialization failed: {e}")
        gemini_available = False
        gemini_rag = None
    
    print(f"✅ Simple RAG: Ready")
    print(f"{'✅' if gemini_available else '⚠️'} Gemini RAG: {'Ready' if gemini_available else 'Fallback mode (no API key)'}")
    print()
    
    # Test each query
    for i, test_case in enumerate(test_queries, 1):
        print(f"🎯 Test {i}: {test_case['description']}")
        print(f"   Query: \"{test_case['query']}\"")
        print(f"   Guest: {test_case['guest_name'] or 'Anonymous'}")
        print()
        
        # Test Simple RAG
        print("   📊 Simple RAG Response:")
        try:
            simple_response = simple_rag.generate_rag_response(
                test_case['query'], 
                test_case['guest_name'] or None
            )
            
            print(f"      ✅ Answer: {simple_response['answer'][:100]}...")
            print(f"      ✅ Confidence: {simple_response['confidence']:.2f}")
            print(f"      ✅ Sources: {len(simple_response.get('sources', []))} found")
            
        except Exception as e:
            print(f"      ❌ Error: {e}")
        
        print()
        
        # Test Gemini RAG (if available)
        if gemini_available and gemini_rag:
            print("   🧠 Gemini-Enhanced RAG Response:")
            try:
                conversation_id = gemini_rag.start_conversation(test_case['guest_name'])
                
                gemini_response = gemini_rag.generate_enhanced_response(
                    test_case['query'],
                    test_case['guest_name'] or None,
                    conversation_id
                )
                
                print(f"      ✅ Enhanced Answer: {gemini_response['answer'][:100]}...")
                print(f"      ✅ Confidence: {gemini_response['confidence']:.2f}")
                print(f"      ✅ Sources: {len(gemini_response.get('sources', []))} found")
                print(f"      ✅ Model: {gemini_response.get('model_used', 'N/A')}")
                print(f"      ✅ Gemini Enhanced: {gemini_response.get('gemini_enhanced', False)}")
                print(f"      ✅ Suggestions: {len(gemini_response.get('suggestions', []))} provided")
                
                # Show first suggestion
                if gemini_response.get('suggestions'):
                    print(f"      💡 First suggestion: \"{gemini_response['suggestions'][0]}\"")
                
            except Exception as e:
                print(f"      ❌ Error: {e}")
        else:
            print("   🧠 Gemini-Enhanced RAG: Not available (using fallback)")
        
        print("\n" + "-" * 60 + "\n")
    
    # Test conversation continuity (if Gemini available)
    if gemini_available and gemini_rag:
        print("🔄 Testing Multi-Turn Conversation...")
        
        try:
            conv_id = gemini_rag.start_conversation("Test Guest")
            
            # First message
            response1 = gemini_rag.generate_enhanced_response(
                "What time is check-in?", "Test Guest", conv_id
            )
            print(f"   Q1: What time is check-in?")
            print(f"   A1: {response1['answer'][:80]}...")
            
            # Follow-up message
            response2 = gemini_rag.generate_enhanced_response(
                "Can I check in earlier?", "Test Guest", conv_id
            )
            print(f"   Q2: Can I check in earlier?")
            print(f"   A2: {response2['answer'][:80]}...")
            
            # Get conversation summary
            summary = gemini_rag.get_conversation_summary(conv_id)
            print(f"   📋 Conversation Summary:")
            print(f"      - Exchanges: {summary['exchange_count']}")
            print(f"      - Topics: {summary['topics_discussed']}")
            
        except Exception as e:
            print(f"   ❌ Conversation test error: {e}")
    
    print("\n🎉 Testing Complete!")
    
    # Performance comparison
    if gemini_available:
        print("\n📊 SYSTEM COMPARISON:")
        print("   Simple RAG:")
        print("   ✅ Fast response time")
        print("   ✅ Zero external dependencies")
        print("   ⚡ TF-IDF similarity matching")
        print("   📚 Basic context retrieval")
        print()
        print("   Gemini-Enhanced RAG:")
        print("   🧠 Advanced AI reasoning")
        print("   💬 Multi-turn conversation support")
        print("   🎯 Context-aware suggestions")
        print("   📈 Higher confidence scoring")
        print("   🎨 Natural language understanding")
        print("   🔄 Conversation memory")
    else:
        print("\n💡 To test Gemini features:")
        print("   1. Set GOOGLE_API_KEY environment variable")
        print("   2. Install google-generativeai library")
        print("   3. Rerun this test")

if __name__ == "__main__":
    test_gemini_rag()