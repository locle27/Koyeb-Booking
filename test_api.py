#!/usr/bin/env python3
"""
Test the RAG API endpoint directly
"""

import requests
import json

def test_rag_api():
    """Test the RAG API endpoint"""
    
    print("🧠 Testing RAG API Endpoint")
    print("=" * 50)
    
    # Test URL (adjust if running on different port)
    url = "http://localhost:5000/api/ai_chat_rag"
    
    # Test queries
    test_cases = [
        {
            "message": "What time is check-in?",
            "guest_name": ""
        },
        {
            "message": "Where can I eat?", 
            "guest_name": ""
        },
        {
            "message": "How much is taxi to airport?",
            "guest_name": "John Doe"
        },
        {
            "message": "What's the WiFi password?",
            "guest_name": ""
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n🎯 Test {i}: '{test_case['message']}'")
        
        try:
            response = requests.post(url, json=test_case, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                
                if data.get('success'):
                    print(f"   ✅ SUCCESS")
                    print(f"   Answer: {data['answer'][:100]}...")
                    print(f"   Confidence: {data['confidence']:.2f}")
                    print(f"   Sources: {data['sources']}")
                    print(f"   RAG Enabled: {data.get('rag_enabled', False)}")
                else:
                    print(f"   ❌ API Error: {data.get('error', 'Unknown')}")
                    
            else:
                print(f"   ❌ HTTP Error: {response.status_code}")
                print(f"   Response: {response.text[:200]}...")
                
        except requests.exceptions.ConnectionError:
            print("   ❌ Connection Error - Is Flask app running?")
            print("   💡 Start with: python3 app.py")
            break
            
        except Exception as e:
            print(f"   ❌ Error: {e}")

if __name__ == "__main__":
    print("🚀 RAG API Test Suite")
    print("Before running this test:")
    print("1. Start Flask app: python3 app.py")
    print("2. Wait for 'Running on http://127.0.0.1:5000'")
    print("3. Then run this test")
    print()
    
    input("Press Enter when Flask app is running...")
    test_rag_api()