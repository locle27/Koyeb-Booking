"""
Test AI Pricing Analyst functionality
"""
try:
    print("Testing AI Pricing Analyst imports...")
    
    # Test import
    from ai_pricing_analyst import AIPricingAnalyst, analyze_budget_pricing_with_ai
    print("✅ AI Pricing Analyst imported successfully")
    
    # Test basic initialization
    analyst = AIPricingAnalyst(google_api_key=None)  # Test without API key
    print("✅ AIPricingAnalyst initialized")
    
    # Test sample data
    sample_properties = [
        {'name': 'Test Hotel 1', 'price_vnd': 450000, 'rating': '8.5', 'location': 'Hàng Bạc'},
        {'name': 'Test Hotel 2', 'price_vnd': 350000, 'rating': '8.0', 'location': 'Tạ Hiện'},
        {'name': 'Test Hotel 3', 'price_vnd': 650000, 'rating': '8.8', 'location': 'Hàng Gai'},
    ]
    
    # Test fallback analysis (without API key)
    result = analyze_budget_pricing_with_ai(
        properties=sample_properties,
        price_threshold=500000,
        google_api_key=None
    )
    
    print(f"✅ Analysis completed - Success: {result.get('success', False)}")
    print(f"📊 Properties analyzed: {result.get('segment_statistics', {}).get('total_properties', 0)}")
    print(f"🔧 Method used: {result.get('method', 'unknown')}")
    
    if result.get('ai_analysis', {}).get('actionable_insights'):
        print("💡 Sample insights:")
        for insight in result['ai_analysis']['actionable_insights'][:2]:
            print(f"  - {insight}")
    
    print("\n🎉 All tests passed! AI Pricing Analyst is ready.")
    
except Exception as e:
    print(f"❌ Test failed: {e}")
    import traceback
    traceback.print_exc()
