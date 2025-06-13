#!/usr/bin/env python3
"""
Debug script for RAG system
Find out why RAG is returning fallback responses
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def debug_knowledge_base():
    """Check if knowledge base is properly loaded"""
    
    print("🔍 Debugging Knowledge Base...")
    
    try:
        from simple_rag import get_simple_rag
        import sqlite3
        
        rag = get_simple_rag()
        
        # Check database
        if os.path.exists(rag.db_path):
            print(f"✅ Database exists: {rag.db_path}")
            
            conn = sqlite3.connect(rag.db_path)
            cursor = conn.cursor()
            
            # Check knowledge base table
            cursor.execute("SELECT COUNT(*) FROM knowledge_base")
            count = cursor.fetchone()[0]
            print(f"✅ Knowledge base entries: {count}")
            
            # Show first few entries
            cursor.execute("SELECT category, topic, keywords FROM knowledge_base LIMIT 5")
            entries = cursor.fetchall()
            
            print("\n📚 Sample knowledge base entries:")
            for i, (category, topic, keywords) in enumerate(entries, 1):
                print(f"{i}. {category}: {topic}")
                print(f"   Keywords: {keywords[:100]}...")
            
            conn.close()
        else:
            print(f"❌ Database not found: {rag.db_path}")
            
    except Exception as e:
        print(f"❌ Error checking knowledge base: {e}")
        import traceback
        traceback.print_exc()

def debug_similarity_calculation():
    """Test similarity calculation with specific queries"""
    
    print("\n🧮 Debugging Similarity Calculation...")
    
    try:
        from simple_rag import get_simple_rag
        
        rag = get_simple_rag()
        
        # Test queries that should work
        test_cases = [
            ("check-in time", "Check-in time is 14:00"),
            ("check in", "Check-in time is 14:00"), 
            ("what time check in", "Check-in time is 14:00"),
            ("taxi airport", "Airport taxi service"),
            ("wifi password", "Free WiFi available")
        ]
        
        for query, expected_content in test_cases:
            print(f"\n🔍 Testing: '{query}'")
            
            # Manual similarity test
            content = expected_content
            keywords = "check-in check in arrival time 14:00 2pm early id identification payment"
            
            score = rag.calculate_similarity(query, content, keywords)
            print(f"   Similarity score: {score:.3f}")
            
            if score > 0.1:
                print(f"   ✅ Should match (score > 0.1)")
            else:
                print(f"   ❌ Won't match (score <= 0.1)")
                
            # Test actual retrieval
            context = rag.retrieve_context(query)
            print(f"   Retrieved entries: {len(context['relevant_info'])}")
            print(f"   Overall confidence: {context['confidence']:.3f}")
            
    except Exception as e:
        print(f"❌ Error testing similarity: {e}")
        import traceback
        traceback.print_exc()

def debug_specific_query(query):
    """Debug a specific query step by step"""
    
    print(f"\n🎯 Debugging Specific Query: '{query}'")
    
    try:
        from simple_rag import get_simple_rag
        import sqlite3
        
        rag = get_simple_rag()
        
        # Step 1: Check database entries
        conn = sqlite3.connect(rag.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT category, topic, content, keywords FROM knowledge_base")
        all_entries = cursor.fetchall()
        conn.close()
        
        print(f"📊 Total database entries: {len(all_entries)}")
        
        # Step 2: Calculate similarity for each entry
        print(f"\n🧮 Similarity scores for '{query}':")
        scored_entries = []
        
        for category, topic, content, keywords in all_entries:
            score = rag.calculate_similarity(query, content, keywords)
            if score > 0.0:  # Show any non-zero scores
                scored_entries.append((score, category, topic))
                print(f"   {score:.3f} - {category}: {topic}")
        
        # Step 3: Show top matches
        scored_entries.sort(reverse=True)
        print(f"\n🏆 Top 3 matches:")
        for i, (score, category, topic) in enumerate(scored_entries[:3], 1):
            print(f"{i}. Score: {score:.3f} - {category}: {topic}")
        
        # Step 4: Test full retrieval
        context = rag.retrieve_context(query)
        print(f"\n📄 Retrieval results:")
        print(f"   Entries found: {len(context['relevant_info'])}")
        print(f"   Confidence: {context['confidence']:.3f}")
        print(f"   Sources: {context['sources_count']}")
        
        # Step 5: Test response generation
        response = rag.generate_rag_response(query)
        print(f"\n💬 Generated response:")
        print(f"   Answer: {response['answer'][:200]}...")
        print(f"   Confidence: {response['confidence']:.3f}")
        print(f"   Sources: {response['sources']}")
        
    except Exception as e:
        print(f"❌ Error debugging query: {e}")
        import traceback
        traceback.print_exc()

def test_keyword_matching():
    """Test keyword matching algorithm"""
    
    print("\n🔑 Testing Keyword Matching Algorithm...")
    
    try:
        from simple_rag import get_simple_rag
        import re
        
        rag = get_simple_rag()
        
        # Test specific cases
        test_cases = [
            {
                'query': 'check-in time',
                'content': 'Check-in time is 14:00',
                'keywords': 'check-in check in arrival time 14:00 2pm early'
            },
            {
                'query': 'what time check in',
                'content': 'Check-in time is 14:00',
                'keywords': 'check-in check in arrival time 14:00 2pm early'
            },
            {
                'query': 'checkin',
                'content': 'Check-in time is 14:00',
                'keywords': 'check-in check in arrival time 14:00 2pm early'
            }
        ]
        
        for test_case in test_cases:
            query = test_case['query']
            content = test_case['content']
            keywords = test_case['keywords']
            
            print(f"\n🔍 Query: '{query}'")
            
            # Show word extraction
            query_lower = query.lower()
            content_lower = content.lower()
            keywords_lower = keywords.lower()
            
            query_words = set(re.findall(r'\w+', query_lower))
            content_words = set(re.findall(r'\w+', content_lower))
            keyword_words = set(re.findall(r'\w+', keywords_lower))
            
            print(f"   Query words: {query_words}")
            print(f"   Keyword words: {keyword_words}")
            print(f"   Content words: {content_words}")
            
            # Show matches
            keyword_matches = len(query_words.intersection(keyword_words))
            content_matches = len(query_words.intersection(content_words))
            
            print(f"   Keyword matches: {keyword_matches}")
            print(f"   Content matches: {content_matches}")
            
            # Calculate score
            score = rag.calculate_similarity(query, content, keywords)
            print(f"   Final score: {score:.3f}")
            
            if score > 0.1:
                print(f"   ✅ PASS - Should retrieve this entry")
            else:
                print(f"   ❌ FAIL - Won't retrieve (score too low)")
                
    except Exception as e:
        print(f"❌ Error testing keyword matching: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("🔧 RAG Debug Suite")
    print("=" * 60)
    
    # Run debug tests
    debug_knowledge_base()
    debug_similarity_calculation() 
    test_keyword_matching()
    
    # Test your specific failing query
    print("\n" + "=" * 60)
    failing_query = input("Enter the query that's failing (or press Enter for 'check-in time'): ").strip()
    if not failing_query:
        failing_query = "check-in time"
    
    debug_specific_query(failing_query)
    
    print("\n" + "=" * 60)
    print("🎯 RECOMMENDATIONS:")
    print("1. If similarity scores are too low, we need to improve keyword matching")
    print("2. If no entries found, knowledge base might not be loaded properly")
    print("3. If scores look good but still failing, check the threshold (0.1)")
    print("4. Try exact phrases from the knowledge base keywords")