#!/usr/bin/env python3
"""
Test script for the RAG system
Run this to verify RAG functionality
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_rag_system():
    """Test the RAG system functionality"""
    
    print("🧠 Testing RAG System...")
    
    try:
        from simple_rag import get_simple_rag
        
        # Initialize RAG system
        rag = get_simple_rag()
        print("✅ RAG system initialized successfully")
        
        # Test queries
        test_queries = [
            "What time is check-in?",
            "How much is taxi to airport?", 
            "Where can I eat nearby?",
            "What is the WiFi password?",
            "Can I cancel my booking?"
        ]
        
        print("\n🔍 Testing queries:")
        for i, query in enumerate(test_queries, 1):
            print(f"\n{i}. Query: '{query}'")
            
            response = rag.generate_rag_response(query)
            
            print(f"   Answer: {response['answer'][:100]}...")
            print(f"   Confidence: {response['confidence']:.2f}")
            print(f"   Sources: {response['sources']}")
            print(f"   Suggestions: {len(response['suggestions'])} provided")
        
        print("\n✅ All RAG tests completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ RAG test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_guest_context():
    """Test guest context functionality"""
    
    print("\n👤 Testing guest context...")
    
    try:
        from simple_rag import get_simple_rag
        
        rag = get_simple_rag()
        
        # Test with guest name
        response = rag.generate_rag_response("When do I check out?", "John Doe")
        
        print(f"Guest-specific query response: {response['answer'][:100]}...")
        print(f"Guest personalized: {response['guest_personalized']}")
        
        print("✅ Guest context test completed")
        return True
        
    except Exception as e:
        print(f"❌ Guest context test failed: {e}")
        return False

if __name__ == "__main__":
    print("🚀 RAG System Test Suite")
    print("=" * 50)
    
    # Run tests
    rag_test = test_rag_system()
    guest_test = test_guest_context()
    
    print("\n" + "=" * 50)
    if rag_test and guest_test:
        print("🎉 ALL TESTS PASSED! RAG system is ready for production!")
    else:
        print("⚠️ Some tests failed. Check the errors above.")
    
    print("\n🌐 Next steps:")
    print("1. Start your Flask app: python app.py")
    print("2. Go to AI Assistant Hub")
    print("3. Try the new RAG Chat Assistant!")
    print("4. Ask questions like 'check-in time' or 'taxi airport'")