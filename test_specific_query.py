#!/usr/bin/env python3
"""
Test specific failing query
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_query(query):
    """Test a specific query"""
    
    print(f"🔍 Testing Query: '{query}'")
    print("=" * 50)
    
    try:
        from simple_rag import get_simple_rag
        
        rag = get_simple_rag()
        
        # Test the full pipeline
        print("📊 Step 1: Retrieve Context")
        context = rag.retrieve_context(query)
        
        print(f"   Relevant entries found: {len(context['relevant_info'])}")
        print(f"   Overall confidence: {context['confidence']:.3f}")
        print(f"   Sources count: {context['sources_count']}")
        
        if context['relevant_info']:
            print("   Top matches:")
            for i, entry in enumerate(context['relevant_info'][:3], 1):
                print(f"   {i}. {entry['topic']} (score: {entry['score']:.3f})")
                print(f"      Content: {entry['content'][:100]}...")
        
        print("\n💬 Step 2: Generate Response")
        response = rag.generate_rag_response(query)
        
        print(f"   Final answer: {response['answer']}")
        print(f"   Confidence: {response['confidence']:.3f}")
        print(f"   Sources: {response['sources']}")
        print(f"   Suggestions: {response['suggestions']}")
        
        return response
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    # Test common queries
    test_queries = [
        "What time is check-in?",
        "check-in time",
        "check in time", 
        "when can I check in",
        "How much is taxi to airport?",
        "taxi airport price",
        "Where can I eat?",
        "food recommendations"
    ]
    
    print("🧠 RAG Query Testing")
    print("=" * 60)
    
    for query in test_queries:
        print(f"\n🎯 TESTING: '{query}'")
        response = test_query(query)
        
        if response and "I don't have specific information" not in response['answer']:
            print("✅ SUCCESS - Got relevant response")
        else:
            print("❌ FAILED - Got fallback response")
        
        print("-" * 40)
    
    print("\n🎯 DIAGNOSIS:")
    print("If all tests show 'SUCCESS' but you're still getting fallback responses,")
    print("the issue might be in the Flask API endpoint or frontend integration.")
    print("\nNext steps:")
    print("1. Check Flask console logs when you test via browser")
    print("2. Check browser console (F12) for JavaScript errors") 
    print("3. Test the API endpoint directly with curl")